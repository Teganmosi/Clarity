from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import Lead
from ..schemas import LeadWithEnrichment, EnrichmentTriggerResponse, BulkEnrichmentTriggerResponse
from ..auth import get_current_user
from ..services.clearbit import ClearbitService
from ..services.apollo import ApolloService

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])


@router.post("/{lead_id}/enrich", response_model=EnrichmentTriggerResponse)
async def enrich_lead(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    background_tasks.add_task(run_enrichment, lead_id)
    return EnrichmentTriggerResponse(message="Enrichment started", lead_id=lead_id)


@router.post("/bulk/enrich", response_model=BulkEnrichmentTriggerResponse)
async def bulk_enrich(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    leads = db.query(Lead).filter(Lead.enriched_at == None).limit(100).all()
    for lead in leads:
        background_tasks.add_task(run_enrichment, lead.id)
    return BulkEnrichmentTriggerResponse(
        message=f"Started enrichment for {len(leads)} leads",
        count=len(leads)
    )


@router.post("/{lead_id}/refresh", response_model=EnrichmentTriggerResponse)
async def refresh_enrichment(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    background_tasks.add_task(run_enrichment, lead_id)
    return EnrichmentTriggerResponse(message="Enrichment refresh started", lead_id=lead_id)


@router.get("/{lead_id}", response_model=LeadWithEnrichment)
async def get_enriched_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/status/summary")
async def get_enrichment_summary(
    db: Session = Depends(get_db)
):
    total = db.query(Lead).count()
    enriched = db.query(Lead).filter(Lead.enriched_at != None).count()
    pending = total - enriched
    sources = db.query(
        Lead.enrichment_source,
        Lead.enrichment_source.label("count")
    ).filter(
        Lead.enrichment_source != None
    ).distinct().all()
    return {
        "total_leads": total,
        "enriched_leads": enriched,
        "pending_enrichment": pending,
        "enrichment_sources": [{"source": s[0], "count": db.query(Lead).filter(Lead.enrichment_source == s[0]).count()} for s in sources] if sources else [],
        "coverage_percentage": round((enriched / total * 100), 1) if total > 0 else 0
    }


async def run_enrichment(lead_id: int):
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return

        clearbit = ClearbitService()
        apollo = ApolloService()

        domain = lead.email.split("@")[1] if "@" in lead.email else None
        if not domain:
            return

        company_data = await clearbit.enrich_company(domain)
        if company_data:
            if company_data.get("industry"):
                lead.industry = company_data["industry"]
            if company_data.get("employee_count"):
                lead.employee_count = company_data["employee_count"]
            if company_data.get("technologies"):
                lead.technologies = company_data["technologies"]
            if company_data.get("description"):
                lead.company_description = company_data["description"]
            if company_data.get("logo_url"):
                lead.logo_url = company_data["logo_url"]
            if company_data.get("linkedin_url"):
                lead.linkedin_url = company_data["linkedin_url"]
            if company_data.get("twitter_url"):
                lead.twitter_url = company_data["twitter_url"]

        person_data = await clearbit.enrich_person(lead.email)
        if person_data:
            if person_data.get("title") and not lead.title:
                lead.title = person_data["title"]
            if person_data.get("linkedin_url") and not lead.linkedin_url:
                lead.linkedin_url = person_data["linkedin_url"]

        lead.enriched_at = datetime.utcnow()
        lead.enrichment_source = "clearbit"

        db.commit()
        await clearbit.close()
        await apollo.close()
    except Exception as e:
        print(f"Enrichment failed for lead {lead_id}: {str(e)}")
        db.rollback()
    finally:
        db.close()
