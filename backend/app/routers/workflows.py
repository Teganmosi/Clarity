from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, Text, JSON as SQLJSON
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..database import Base, get_db, engine
from ..models import User, Lead
from ..auth import get_current_user
from ..services.workflow_engine import WorkflowRule, evaluate_workflows, get_actions_log, clear_actions_log

router = APIRouter(prefix="/workflows", tags=["Workflows"])


class WorkflowDB(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    trigger_field = Column(String(100), nullable=False)
    trigger_operator = Column(String(50), nullable=False)
    trigger_value = Column(String(200), nullable=False)
    action_type = Column(String(50), nullable=False)
    action_params = Column(SQLJSON, default=dict)
    active = Column(Boolean, default=True)
    created_at = Column(String(30), default=lambda: datetime.utcnow().isoformat())


Base.metadata.create_all(bind=engine, tables=[WorkflowDB.__table__])


def _db_to_rule(db_row: WorkflowDB) -> WorkflowRule:
    return WorkflowRule(
        rule_id=db_row.id,
        name=db_row.name,
        trigger_field=db_row.trigger_field,
        trigger_operator=db_row.trigger_operator,
        trigger_value=db_row.trigger_value,
        action_type=db_row.action_type,
        action_params=db_row.action_params or {},
        active=db_row.active,
    )


@router.post("/rules")
async def create_rule(
    name: str,
    trigger_field: str,
    trigger_operator: str,
    trigger_value: str,
    action_type: str,
    action_params: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = WorkflowDB(
        user_id=current_user.id,
        name=name,
        trigger_field=trigger_field,
        trigger_operator=trigger_operator,
        trigger_value=trigger_value,
        action_type=action_type,
        action_params=action_params,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {
        "id": rule.id,
        "name": rule.name,
        "trigger_field": rule.trigger_field,
        "trigger_operator": rule.trigger_operator,
        "trigger_value": rule.trigger_value,
        "action_type": rule.action_type,
        "action_params": rule.action_params,
        "active": rule.active,
    }


@router.get("/rules")
async def list_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rules = db.query(WorkflowDB).filter(WorkflowDB.user_id == current_user.id).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "trigger_field": r.trigger_field,
            "trigger_operator": r.trigger_operator,
            "trigger_value": r.trigger_value,
            "action_type": r.action_type,
            "action_params": r.action_params,
            "active": r.active,
            "created_at": r.created_at,
        }
        for r in rules
    ]


@router.put("/rules/{rule_id}/toggle")
async def toggle_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = db.query(WorkflowDB).filter(WorkflowDB.id == rule_id, WorkflowDB.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.active = not rule.active
    db.commit()
    return {"id": rule.id, "active": rule.active}


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = db.query(WorkflowDB).filter(WorkflowDB.id == rule_id, WorkflowDB.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"deleted": True}


@router.post("/evaluate/{lead_id}")
async def evaluate_lead_workflows(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    rules_db = db.query(WorkflowDB).filter(WorkflowDB.user_id == current_user.id, WorkflowDB.active == True).all()
    rules = [_db_to_rule(r) for r in rules_db]
    results = evaluate_workflows(lead, rules)
    db.commit()
    return {"lead_id": lead_id, "matched_rules": len(results), "results": results}


@router.get("/logs")
async def get_logs(
    current_user: User = Depends(get_current_user),
):
    return {"logs": get_actions_log()}


@router.post("/logs/clear")
async def clear_logs(
    current_user: User = Depends(get_current_user),
):
    clear_actions_log()
    return {"cleared": True}
