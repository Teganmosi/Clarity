from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import User, Account
from ..auth import get_current_user
from ..services.retention_engine import (
    calculate_churn_score, calculate_expansion_score,
    trigger_retention_workflow, get_health_trends, snapshot_all_accounts,
)

router = APIRouter(prefix="/retention", tags=["Retention"])


@router.post("/analyze/{account_id}")
async def analyze_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = trigger_retention_workflow(account_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/at-risk")
async def get_at_risk_accounts(
    threshold: int = Query(70, description="Churn score threshold"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = db.query(Account).filter(Account.churn_risk_score >= threshold).all()
    return {
        "threshold": threshold,
        "accounts": [
            {
                "id": a.id,
                "company_name": a.company_name,
                "churn_risk_score": a.churn_risk_score,
                "expansion_score": a.expansion_score,
                "health_status": a.health_status,
                "industry": a.industry,
            }
            for a in accounts
        ],
    }


@router.get("/expansion")
async def get_expansion_opportunities(
    threshold: int = Query(80, description="Expansion score threshold"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = db.query(Account).filter(Account.expansion_score >= threshold).all()
    return {
        "threshold": threshold,
        "accounts": [
            {
                "id": a.id,
                "company_name": a.company_name,
                "expansion_score": a.expansion_score,
                "churn_risk_score": a.churn_risk_score,
                "health_status": a.health_status,
                "industry": a.industry,
            }
            for a in accounts
        ],
    }


@router.get("/trends")
async def get_trends(
    account_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trends = get_health_trends(db, account_id)
    return {"trends": trends}


@router.post("/snapshot-all")
async def take_snapshot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    snapshot_all_accounts(db)
    return {"status": "snapshot_complete"}
