from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import User, AnonymizedOutcome, NetworkInsight
from ..auth import get_current_user
from ..services.network_engine import (
    ingest_anonymized_outcome, calculate_industry_benchmarks, get_network_insights
)

router = APIRouter(prefix="/network", tags=["Network"])


@router.post("/ingest")
async def ingest_outcome(
    lead_id: int = None,
    email: str = None,
    industry: str = None,
    action: str = "outreach",
    action_type: str = "email",
    success: bool = None,
    channel: str = "email",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ingest_anonymized_outcome(
        db, lead_id=lead_id, email=email, industry=industry,
        action=action, action_type=action_type, success=success, channel=channel,
    )
    return {"status": "ingested"}


@router.get("/benchmarks")
async def get_benchmarks(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return calculate_industry_benchmarks(db, industry)


@router.get("/insights")
async def get_insights(
    industry: Optional[str] = Query(None, description="Your industry for personalized tips"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_network_insights(db, industry)


@router.get("/stats")
async def get_network_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.query(AnonymizedOutcome).count()
    success = db.query(AnonymizedOutcome).filter(AnonymizedOutcome.success == True).count()
    industries = db.query(AnonymizedOutcome.industry_tag).distinct().count()
    return {
        "total_anonymized_outcomes": total,
        "total_success": success,
        "overall_success_rate": round(success / max(total, 1) * 100, 1),
        "industries_tracked": industries,
    }
