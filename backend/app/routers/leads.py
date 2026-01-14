"""
Leads router
Handles lead CRUD operations, scoring, and bulk operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import io
import csv
import json
from datetime import datetime

from app.database import get_db
from app.models import Lead, User
from app.schemas import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadListResponse,
    BulkLeadUpload,
    BulkLeadUploadResponse,
    LeadFilter,
    ExportRequest
)
from app.auth import get_current_user
from app.scoring import score_leads, retrain_model, enrich_lead_data
from app.notifications import send_lead_notification, send_bulk_lead_notifications

# Create router
router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new lead
    
    The lead will be automatically scored based on its attributes.
    High-priority leads (score >= 80) will trigger notifications.
    """
    # Score the lead
    lead_dict = lead.dict()
    scored_leads = score_leads([lead_dict])
    scored_lead = scored_leads[0]
    
    # Create lead in database
    db_lead = Lead(
        user_id=current_user.id,
        **lead_dict,
        score=scored_lead['score'],
        score_category=scored_lead['score_category'],
        conversion_probability=scored_lead['conversion_probability']
    )
    
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    # Send notification for high-priority leads
    if db_lead.score >= 80:
        await send_lead_notification(db_lead, db)
    
    return db_lead


@router.get("/", response_model=LeadListResponse)
async def list_leads(
    source: Optional[str] = None,
    campaign: Optional[str] = None,
    status: Optional[str] = None,
    score_min: Optional[float] = None,
    score_max: Optional[float] = None,
    score_category: Optional[str] = None,
    company_size: Optional[str] = None,
    industry: Optional[str] = None,
    converted: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("score", regex="^(score|created_at|name|company)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List leads with filtering and pagination
    
    - **source**: Filter by lead source
    - **campaign**: Filter by campaign
    - **status**: Filter by lead status
    - **score_min**: Minimum lead score
    - **score_max**: Maximum lead score
    - **score_category**: Filter by score category (hot/warm/cold)
    - **company_size**: Filter by company size
    - **industry**: Filter by industry
    - **converted**: Filter by conversion status
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **sort_by**: Sort field (score, created_at, name, company)
    - **sort_order**: Sort order (asc, desc)
    """
    # Build query
    query = db.query(Lead).filter(Lead.user_id == current_user.id)
    
    # Apply filters
    if source:
        query = query.filter(Lead.source == source)
    if campaign:
        query = query.filter(Lead.campaign == campaign)
    if status:
        query = query.filter(Lead.status == status)
    if score_min is not None:
        query = query.filter(Lead.score >= score_min)
    if score_max is not None:
        query = query.filter(Lead.score <= score_max)
    if score_category:
        query = query.filter(Lead.score_category == score_category)
    if company_size:
        query = query.filter(Lead.company_size == company_size)
    if industry:
        query = query.filter(Lead.industry == industry)
    if converted is not None:
        query = query.filter(Lead.converted == converted)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Lead, sort_by)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    leads = query.offset(offset).limit(page_size).all()
    
    # Enrich leads with AI insights
    enriched_leads = [enrich_lead_data(lead, db, current_user.id) for lead in leads]
    
    return {
        "leads": enriched_leads,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific lead by ID
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return enrich_lead_data(lead, db, current_user.id)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a lead
    
    The lead will be re-scored if scoring-relevant fields are updated.
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Check if scoring-relevant fields are being updated
    scoring_fields = {
        'source', 'campaign', 'medium', 'past_interactions',
        'pages_visited', 'time_on_site', 'company_size', 'budget'
    }
    update_data = lead_update.dict(exclude_unset=True)
    needs_rescoring = bool(scoring_fields.intersection(update_data.keys()))
    
    # Update lead
    for field, value in update_data.items():
        setattr(lead, field, value)
    
    # Re-score if needed
    if needs_rescoring:
        lead_dict = {
            'name': lead.name,
            'email': lead.email,
            'company': lead.company,
            'source': lead.source,
            'campaign': lead.campaign,
            'medium': lead.medium,
            'past_interactions': lead.past_interactions,
            'pages_visited': lead.pages_visited,
            'time_on_site': lead.time_on_site,
            'company_size': lead.company_size,
            'budget': lead.budget,
            'last_interaction_date': lead.last_interaction_date
        }
        scored_leads = score_leads([lead_dict])
        scored_lead = scored_leads[0]
        lead.score = scored_lead['score']
        lead.score_category = scored_lead['score_category']
        lead.conversion_probability = scored_lead['conversion_probability']
    
    db.commit()
    db.refresh(lead)
    
    return enrich_lead_data(lead, db, current_user.id)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a lead
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    db.delete(lead)
    db.commit()
    
    return None


@router.post("/bulk", response_model=BulkLeadUploadResponse)
async def bulk_upload_leads(
    bulk_upload: BulkLeadUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple leads at once
    
    All leads will be automatically scored.
    High-priority leads (score >= 80) will trigger notifications.
    """
    leads_data = [lead.dict() for lead in bulk_upload.leads]
    
    # Score all leads
    scored_leads = score_leads(leads_data)
    
    # Create leads in database
    created_leads = []
    errors = []
    
    for i, scored_lead in enumerate(scored_leads):
        try:
            db_lead = Lead(
                user_id=current_user.id,
                **leads_data[i],
                score=scored_lead['score'],
                score_category=scored_lead['score_category'],
                conversion_probability=scored_lead['conversion_probability']
            )
            db.add(db_lead)
            db.commit()
            db.refresh(db_lead)
            created_leads.append(db_lead)
        except Exception as e:
            errors.append(f"Lead {i + 1}: {str(e)}")
            db.rollback()
    
    # Send notifications for high-priority leads
    high_priority_leads = [lead for lead in created_leads if lead.score >= 80]
    if high_priority_leads:
        await send_bulk_lead_notifications(high_priority_leads, db)
    
    return {
        "success_count": len(created_leads),
        "failed_count": len(errors),
        "leads": created_leads,
        "errors": errors
    }


@router.post("/upload/csv", response_model=BulkLeadUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload leads from a CSV file
    
    Expected CSV columns:
    - name (required)
    - email (required)
    - company (optional)
    - phone (optional)
    - title (optional)
    - source (optional)
    - campaign (optional)
    - medium (optional)
    - past_interactions (optional, default: 0)
    - pages_visited (optional, default: 0)
    - time_on_site (optional, default: 0)
    - company_size (optional)
    - industry (optional)
    - budget (optional)
    - notes (optional)
    - tags (optional)
    """
    try:
        # Read CSV file
        contents = await file.read()
        
        # Try to read with pandas (handling different encodings)
        try:
            # First try UTF-8
            df = pd.read_csv(io.BytesIO(contents), encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # Try common Windows encoding
                df = pd.read_csv(io.BytesIO(contents), encoding='cp1252')
            except UnicodeDecodeError:
                # Fallbact to latin-1
                df = pd.read_csv(io.BytesIO(contents), encoding='latin-1')
        
        # Validate required columns
        required_columns = ['name', 'email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Convert to list of dictionaries
        leads_data = df.to_dict('records')
        
        # Score all leads
        scored_leads = score_leads(leads_data)
        
        # Create leads in database
        created_leads = []
        errors = []
        
        for i, scored_lead in enumerate(scored_leads):
            try:
                # Prepare lead data
                lead_data = leads_data[i].copy()
                
                # Convert NaN to None
                lead_data = {k: (v if pd.notna(v) else None) for k, v in lead_data.items()}
                
                db_lead = Lead(
                    user_id=current_user.id,
                    **lead_data,
                    score=scored_lead['score'],
                    score_category=scored_lead['score_category'],
                    conversion_probability=scored_lead['conversion_probability']
                )
                db.add(db_lead)
                db.commit()
                db.refresh(db_lead)
                created_leads.append(db_lead)
            except Exception as e:
                errors.append(f"Row {i + 2}: {str(e)}")  # +2 because of header and 0-index
                db.rollback()
        
        # Send notifications for high-priority leads
        high_priority_leads = [lead for lead in created_leads if lead.score >= 80]
        if high_priority_leads:
            await send_bulk_lead_notifications(high_priority_leads, db)
        
        return {
            "success_count": len(created_leads),
            "failed_count": len(errors),
            "leads": created_leads,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing CSV file: {str(e)}"
        )


@router.post("/upload/json", response_model=BulkLeadUploadResponse)
async def upload_json(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload leads from a JSON file
    
    Expected JSON format:
    [
        {
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Acme Corp",
            ...
        },
        ...
    ]
    """
    try:
        # Read JSON file
        contents = await file.read()
        leads_data = json.loads(contents.decode('utf-8'))
        
        if not isinstance(leads_data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON must be an array of lead objects"
            )
        
        # Validate required fields
        for i, lead in enumerate(leads_data):
            if 'name' not in lead or 'email' not in lead:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lead at index {i} missing required fields: name, email"
                )
        
        # Score all leads
        scored_leads = score_leads(leads_data)
        
        # Create leads in database
        created_leads = []
        errors = []
        
        for i, scored_lead in enumerate(scored_leads):
            try:
                db_lead = Lead(
                    user_id=current_user.id,
                    **leads_data[i],
                    score=scored_lead['score'],
                    score_category=scored_lead['score_category'],
                    conversion_probability=scored_lead['conversion_probability']
                )
                db.add(db_lead)
                db.commit()
                db.refresh(db_lead)
                created_leads.append(db_lead)
            except Exception as e:
                errors.append(f"Lead {i + 1}: {str(e)}")
                db.rollback()
        
        # Send notifications for high-priority leads
        high_priority_leads = [lead for lead in created_leads if lead.score >= 80]
        if high_priority_leads:
            await send_bulk_lead_notifications(high_priority_leads, db)
        
        return {
            "success_count": len(created_leads),
            "failed_count": len(errors),
            "leads": created_leads,
            "errors": errors
        }
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing JSON file: {str(e)}"
        )


@router.post("/export")
async def export_leads(
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export leads to CSV or JSON
    
    - **format**: Export format (csv or json)
    - **filters**: Optional filters to apply
    """
    # Build query
    query = db.query(Lead).filter(Lead.user_id == current_user.id)
    
    # Apply filters if provided
    if export_request.filters:
        filters = export_request.filters
        if filters.source:
            query = query.filter(Lead.source == filters.source)
        if filters.campaign:
            query = query.filter(Lead.campaign == filters.campaign)
        if filters.status:
            query = query.filter(Lead.status == filters.status)
        if filters.score_min is not None:
            query = query.filter(Lead.score >= filters.score_min)
        if filters.score_max is not None:
            query = query.filter(Lead.score <= filters.score_max)
        if filters.score_category:
            query = query.filter(Lead.score_category == filters.score_category)
        if filters.company_size:
            query = query.filter(Lead.company_size == filters.company_size)
        if filters.industry:
            query = query.filter(Lead.industry == filters.industry)
        if filters.converted is not None:
            query = query.filter(Lead.converted == filters.converted)
        
        # Apply sorting
        sort_column = getattr(Lead, filters.sort_by)
        if filters.sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    
    leads = query.all()
    
    # Convert to list of dictionaries
    leads_data = []
    for lead in leads:
        lead_dict = {
            'id': lead.id,
            'name': lead.name,
            'email': lead.email,
            'company': lead.company,
            'phone': lead.phone,
            'title': lead.title,
            'source': lead.source,
            'campaign': lead.campaign,
            'medium': lead.medium,
            'past_interactions': lead.past_interactions,
            'pages_visited': lead.pages_visited,
            'time_on_site': lead.time_on_site,
            'company_size': lead.company_size,
            'industry': lead.industry,
            'budget': lead.budget,
            'score': lead.score,
            'score_category': lead.score_category,
            'conversion_probability': lead.conversion_probability,
            'status': lead.status,
            'converted': lead.converted,
            'notes': lead.notes,
            'tags': lead.tags,
            'created_at': lead.created_at.isoformat() if lead.created_at else None
        }
        leads_data.append(lead_dict)
    
    # Generate file based on format
    if export_request.format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=leads_data[0].keys() if leads_data else [])
        writer.writeheader()
        writer.writerows(leads_data)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    else:  # JSON
        return StreamingResponse(
            io.BytesIO(json.dumps(leads_data, indent=2).encode('utf-8')),
            media_type='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )


@router.post("/{lead_id}/mark-converted")
async def mark_lead_converted(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a lead as converted
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    lead.converted = True
    lead.conversion_date = datetime.now()
    lead.status = "converted"
    
    db.commit()
    db.refresh(lead)
    
    return lead


@router.post("/retrain-model")
async def retrain_scoring_model(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrain the lead scoring model with current data
    
    This will update the ML model with all leads and their conversion status.
    """
    try:
        metrics = retrain_model(db)
        return {
            "success": True,
            "message": "Model retrained successfully",
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrain model: {str(e)}"
        )
