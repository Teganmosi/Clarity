from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import Lead
from ..schemas import EnrichmentResponse, BulkEnrichmentResponse
from ..auth import get_current_user
from ..services.clearbit import ClearbitService
from ..services.apollo import ApolloService

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])


def _extract_domain(email: str) -> str:
    return email.split("@")[1] if "@" in email else None


async def _run_enrichment(lead_id: int):
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return

        lead.enrichment_status = "processing"
        db.commit()

        clearbit = ClearbitService()
        apollo = ApolloService()

        domain = _extract_domain(lead.email)
        if not domain:
            lead.enrichment_status = "failed"
            db.commit()
            return

        company_data = await clearbit.enrich_company(domain)
        if company_data:
            for key, value in company_data.items():
                if hasattr(lead, key) and value is not None:
                    setattr(lead, key, value)

        person_data = await clearbit.enrich_person(lead.email)
        if person_data and person_data.get("title") and not lead.title:
            lead.title = person_data["title"]

        lead.enrichment_status = "completed"
        lead.last_enriched_at = datetime.utcnow()
        lead.enrichment_source = "clearbit"

        db.commit()
        await clearbit.close()
        await apollo.close()
    except Exception as e:
        print(f"Enrichment failed for lead {lead_id}: {str(e)}")
        lead.enrichment_status = "failed"
        db.commit()
        db.rollback()
    finally:
        db.close()


@router.post("/enrich", response_model=EnrichmentResponse)
async def enrich_lead(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    background_tasks.add_task(_run_enrichment, lead_id)
    return EnrichmentResponse(
        message="Enrichment started",
        lead_id=lead_id,
        status="processing"
    )


@router.post("/bulk-enrich", response_model=BulkEnrichmentResponse)
async def bulk_enrich(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    leads = db.query(Lead).filter(
        (Lead.enrichment_status == None) | (Lead.enrichment_status == "pending")
    ).limit(100).all()

    for lead in leads:
        background_tasks.add_task(_run_enrichment, lead.id)

    return BulkEnrichmentResponse(
        message="Bulk enrichment queued",
        total_queued=len(leads),
        status="processing"
    )


@router.post("/refresh/{lead_id}", response_model=EnrichmentResponse)
async def refresh_enrichment(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    background_tasks.add_task(_run_enrichment, lead_id)
    return EnrichmentResponse(
        message="Enrichment refresh started",
        lead_id=lead_id,
        status="processing"
    )


@router.get("/{lead_id}", response_model=EnrichmentResponse)
async def get_enrichment_data(
    lead_id: int,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return EnrichmentResponse(
        message="Enrichment data retrieved",
        lead_id=lead_id,
        status=lead.enrichment_status or "pending",
        enrichment_source=lead.enrichment_source
    )


@router.get("/summary/{lead_id}")
async def get_enrichment_summary(
    lead_id: int,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    enrichment_fields = {
        "technologies": lead.technologies,
        "funding_stage": lead.funding_stage,
        "employee_count": lead.employee_count,
        "logo_url": lead.logo_url,
        "linkedin_url": lead.linkedin_url,
        "twitter_handle": lead.twitter_handle,
        "annual_revenue": lead.annual_revenue,
        "headquarters_location": lead.headquarters_location,
        "founded_year": lead.founded_year,
        "industry_tags": lead.industry_tags,
    }
    has_fields = {k: v for k, v in enrichment_fields.items() if v}
    missing_fields = {k: v for k, v in enrichment_fields.items() if not v}

    return {
        "lead_id": lead_id,
        "enrichment_status": lead.enrichment_status or "pending",
        "enrichment_source": lead.enrichment_source,
        "last_enriched_at": lead.last_enriched_at,
        "enriched_field_count": len(has_fields),
        "total_available_fields": len(enrichment_fields),
        "has_data": {
            "fields": list(has_fields.keys()),
            "count": len(has_fields)
        },
        "missing_data": {
            "fields": list(missing_fields.keys()),
            "count": len(missing_fields)
        }
    }
