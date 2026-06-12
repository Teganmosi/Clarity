from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, Text, Float, JSON as SQLJSON
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..database import Base, get_db, engine
from ..models import User, Lead
from ..auth import get_current_user
from ..services.workflow_engine import WorkflowRule, evaluate_workflows, get_actions_log, get_logs_by_rule, clear_actions_log

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
    delay_minutes = Column(Integer, default=0)
    created_at = Column(String(30), default=lambda: datetime.utcnow().isoformat())


class WorkflowLogDB(Base):
    __tablename__ = "workflow_logs"
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False)
    rule_name = Column(String(200))
    lead_id = Column(Integer, nullable=False)
    lead_name = Column(String(200))
    action_type = Column(String(50))
    status = Column(String(20))
    execution_time = Column(Float, default=0.0)
    step_details = Column(SQLJSON)
    error_message = Column(Text)
    timestamp = Column(String(30), default=lambda: datetime.utcnow().isoformat())


Base.metadata.create_all(bind=engine, tables=[WorkflowDB.__table__, WorkflowLogDB.__table__])


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
        delay_minutes=db_row.delay_minutes or 0,
    )


def _log_to_db(db: Session, entry: Dict[str, Any]):
    log = WorkflowLogDB(
        rule_id=entry.get("rule_id", 0),
        rule_name=entry.get("rule_name", ""),
        lead_id=entry.get("lead_id", 0),
        lead_name=entry.get("lead_name", ""),
        action_type=entry.get("action_type", ""),
        status=entry.get("status", "unknown"),
        execution_time=entry.get("execution_time", 0.0),
        step_details=entry.get("step_details"),
        error_message=entry.get("error_message"),
        timestamp=entry.get("timestamp", datetime.utcnow().isoformat()),
    )
    db.add(log)
    db.commit()


@router.post("/rules")
async def create_rule(
    name: str,
    trigger_field: str,
    trigger_operator: str,
    trigger_value: str,
    action_type: str,
    action_params: Dict[str, Any] = {},
    delay_minutes: int = 0,
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
        delay_minutes=delay_minutes,
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
        "delay_minutes": rule.delay_minutes,
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
            "delay_minutes": r.delay_minutes,
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
    for entry in get_actions_log():
        if entry.get("rule_id"):
            try:
                _log_to_db(db, entry)
            except Exception:
                pass
    clear_actions_log()
    db.commit()
    return {"lead_id": lead_id, "matched_rules": len(results), "results": results}


@router.get("/logs")
async def get_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_logs = db.query(WorkflowLogDB).order_by(WorkflowLogDB.id.desc()).limit(100).all()
    return {
        "logs": [
            {
                "id": l.id,
                "rule_id": l.rule_id,
                "rule_name": l.rule_name,
                "lead_id": l.lead_id,
                "lead_name": l.lead_name,
                "action_type": l.action_type,
                "status": l.status,
                "execution_time": l.execution_time,
                "step_details": l.step_details,
                "error_message": l.error_message,
                "timestamp": l.timestamp,
            }
            for l in db_logs
        ]
    }


@router.get("/logs/{rule_id}")
async def get_logs_by_rule_id(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_logs = db.query(WorkflowLogDB).filter(WorkflowLogDB.rule_id == rule_id).order_by(WorkflowLogDB.id.desc()).limit(50).all()
    return {
        "rule_id": rule_id,
        "logs": [
            {
                "id": l.id,
                "lead_id": l.lead_id,
                "lead_name": l.lead_name,
                "action_type": l.action_type,
                "status": l.status,
                "execution_time": l.execution_time,
                "step_details": l.step_details,
                "error_message": l.error_message,
                "timestamp": l.timestamp,
            }
            for l in db_logs
        ]
    }


@router.post("/logs/clear")
async def clear_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(WorkflowLogDB).delete()
    db.commit()
    clear_actions_log()
    return {"cleared": True}
