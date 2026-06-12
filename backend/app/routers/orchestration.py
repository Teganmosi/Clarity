from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import User, Lead
from ..auth import get_current_user
from ..services.orchestrator import (
    evaluate_lead_state, delegate_task, update_lifecycle,
    get_execution_logs, get_global_status,
)

router = APIRouter(prefix="/orchestration", tags=["Orchestration"])


@router.post("/run/{lead_id}")
async def orchestrate_lead(
    lead_id: int,
    force_stage: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if force_stage and force_stage in ["new", "engaging", "qualified", "meeting_booked", "closed"]:
        result = update_lifecycle(lead_id, force_stage, db, trigger_reason=f"Manual override to {force_stage}")
    else:
        state = evaluate_lead_state(lead_id, db)
        result = update_lifecycle(lead_id, state["recommended_stage"], db,
                                  trigger_reason="; ".join(state["triggers"]))

    return result


@router.get("/status")
async def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    status = get_global_status(db)
    return status


@router.get("/logs/{lead_id}")
async def get_lead_logs(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    logs = get_execution_logs(lead_id, db)
    return {"lead_id": lead_id, "logs": logs}


@router.get("/leads")
async def get_orchestrated_leads(
    stage: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.user_id == current_user.id)
    if stage:
        query = query.filter(Lead.lifecycle_stage == stage)
    leads = query.order_by(Lead.updated_at.desc()).limit(100).all()
    return {
        "leads": [
            {
                "id": l.id,
                "name": l.name,
                "company": l.company,
                "lifecycle_stage": l.lifecycle_stage or "new",
                "active_agent": l.active_agent,
                "intent_score": l.intent_score,
                "score": l.score,
                "status": l.status,
            }
            for l in leads
        ]
    }
