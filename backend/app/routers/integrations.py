"""
Integrations router
Handles CRM integrations (HubSpot, Pipedrive)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
import os

from app.database import get_db
from app.models import Lead, User, IntegrationLog
from app.schemas import IntegrationConfig, IntegrationSyncRequest, IntegrationSyncResponse
from app.auth import get_current_user
from app.integrations import (
    sync_to_hubspot,
    sync_to_pipedrive,
    bulk_sync_to_hubspot,
    bulk_sync_to_pipedrive
)

# Create router
router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("/config", response_model=IntegrationConfig)
async def get_integration_config(current_user: User = Depends(get_current_user)):
    """
    Get current integration configuration
    
    Returns the status of HubSpot and Pipedrive integrations
    """
    hubspot_api_key = os.getenv("HUBSPOT_API_KEY", "")
    pipedrive_api_key = os.getenv("PIPEDRIVE_API_KEY", "")
    
    return {
        'hubspot_api_key': hubspot_api_key[:10] + "..." if hubspot_api_key else None,
        'pipedrive_api_key': pipedrive_api_key[:10] + "..." if pipedrive_api_key else None,
        'hubspot_enabled': bool(hubspot_api_key),
        'pipedrive_enabled': bool(pipedrive_api_key)
    }


@router.post("/sync/hubspot", response_model=IntegrationSyncResponse)
async def sync_to_hubspot_crm(
    sync_request: IntegrationSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync leads to HubSpot CRM
    
    - **lead_ids**: List of specific lead IDs to sync (optional)
    - **sync_all**: If true, sync all leads (default: false)
    """
    # Get leads to sync
    if sync_request.sync_all:
        leads = db.query(Lead).filter(Lead.user_id == current_user.id).all()
    elif sync_request.lead_ids:
        leads = db.query(Lead).filter(
            Lead.id.in_(sync_request.lead_ids),
            Lead.user_id == current_user.id
        ).all()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either lead_ids or sync_all must be specified"
        )
    
    if not leads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No leads found to sync"
        )
    
    # Sync to HubSpot
    results = await bulk_sync_to_hubspot(leads, db)
    
    return {
        'success': results['failed'] == 0,
        'synced_count': results['success'],
        'failed_count': results['failed'],
        'errors': results['errors']
    }


@router.post("/sync/pipedrive", response_model=IntegrationSyncResponse)
async def sync_to_pipedrive_crm(
    sync_request: IntegrationSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync leads to Pipedrive CRM
    
    - **lead_ids**: List of specific lead IDs to sync (optional)
    - **sync_all**: If true, sync all leads (default: false)
    """
    # Get leads to sync
    if sync_request.sync_all:
        leads = db.query(Lead).filter(Lead.user_id == current_user.id).all()
    elif sync_request.lead_ids:
        leads = db.query(Lead).filter(
            Lead.id.in_(sync_request.lead_ids),
            Lead.user_id == current_user.id
        ).all()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either lead_ids or sync_all must be specified"
        )
    
    if not leads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No leads found to sync"
        )
    
    # Sync to Pipedrive
    results = await bulk_sync_to_pipedrive(leads, db)
    
    return {
        'success': results['failed'] == 0,
        'synced_count': results['success'],
        'failed_count': results['failed'],
        'errors': results['errors']
    }


@router.post("/sync/{lead_id}/hubspot")
async def sync_single_lead_to_hubspot(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync a single lead to HubSpot
    
    Creates a new contact if the lead doesn't have a HubSpot ID,
    otherwise updates the existing contact.
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
    
    # Sync to HubSpot
    result = await sync_to_hubspot(lead, db)
    
    if result.get('success'):
        db.commit()
        db.refresh(lead)
        return {
            'success': True,
            'message': 'Lead synced to HubSpot successfully',
            'hubspot_id': lead.hubspot_id
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Failed to sync lead to HubSpot')
        )


@router.post("/sync/{lead_id}/pipedrive")
async def sync_single_lead_to_pipedrive(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync a single lead to Pipedrive
    
    Creates a new person if the lead doesn't have a Pipedrive ID,
    otherwise updates the existing person.
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
    
    # Sync to Pipedrive
    result = await sync_to_pipedrive(lead, db)
    
    if result.get('success'):
        db.commit()
        db.refresh(lead)
        return {
            'success': True,
            'message': 'Lead synced to Pipedrive successfully',
            'pipedrive_id': lead.pipedrive_id
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Failed to sync lead to Pipedrive')
        )


@router.get("/logs")
async def get_integration_logs(
    integration_type: str = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get integration logs
    
    - **integration_type**: Filter by integration type (hubspot/pipedrive)
    - **limit**: Maximum number of logs to return (default: 50)
    """
    # Get lead IDs for current user using explicit scalar subquery
    user_lead_ids_subquery = select(Lead.id).where(Lead.user_id == current_user.id).scalar_subquery()
    
    # Build query
    query = db.query(IntegrationLog).filter(
        IntegrationLog.lead_id.in_(user_lead_ids_subquery)
    )
    
    # Apply filter if specified
    if integration_type:
        query = query.filter(IntegrationLog.integration_type == integration_type)
    
    # Get logs
    logs = query.order_by(IntegrationLog.created_at.desc()).limit(limit).all()
    
    # Convert to response format
    log_list = []
    for log in logs:
        log_list.append({
            'id': log.id,
            'lead_id': log.lead_id,
            'integration_type': log.integration_type,
            'action': log.action,
            'external_id': log.external_id,
            'status': log.status,
            'error_message': log.error_message,
            'created_at': log.created_at.isoformat() if log.created_at else None
        })
    
    return log_list


@router.get("/status")
async def get_integration_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get overall integration status
    
    Returns statistics about integrations for the current user
    """
    # Get lead IDs for current user using explicit scalar subquery
    user_lead_ids_subquery = select(Lead.id).where(Lead.user_id == current_user.id).scalar_subquery()
    
    # Get HubSpot stats
    hubspot_count = db.query(Lead).filter(
        Lead.id.in_(user_lead_ids_subquery),
        Lead.hubspot_id.isnot(None)
    ).count()
    
    # Get Pipedrive stats
    pipedrive_count = db.query(Lead).filter(
        Lead.id.in_(user_lead_ids_subquery),
        Lead.pipedrive_id.isnot(None)
    ).count()
    
    # Get total leads
    total_leads = db.query(Lead).filter(Lead.user_id == current_user.id).count()
    
    # Get recent sync logs
    recent_logs = db.query(IntegrationLog).filter(
        IntegrationLog.lead_id.in_(user_lead_ids_subquery)
    ).order_by(IntegrationLog.created_at.desc()).limit(5).all()
    
    recent_syncs = []
    for log in recent_logs:
        recent_syncs.append({
            'integration_type': log.integration_type,
            'action': log.action,
            'status': log.status,
            'created_at': log.created_at.isoformat() if log.created_at else None
        })
    
    return {
        'hubspot': {
            'enabled': bool(os.getenv("HUBSPOT_API_KEY")),
            'synced_leads': hubspot_count,
            'unsynced_leads': total_leads - hubspot_count
        },
        'pipedrive': {
            'enabled': bool(os.getenv("PIPEDRIVE_API_KEY")),
            'synced_leads': pipedrive_count,
            'unsynced_leads': total_leads - pipedrive_count
        },
        'total_leads': total_leads,
        'recent_syncs': recent_syncs
    }
