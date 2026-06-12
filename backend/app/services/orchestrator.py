import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

LIFECYCLE_STAGES = [
    "new",
    "engaging",
    "qualified",
    "meeting_booked",
    "closed",
]

LIFECYCLE_TRANSITIONS = {
    "new": ["engaging"],
    "engaging": ["qualified", "new"],
    "qualified": ["meeting_booked", "engaging"],
    "meeting_booked": ["closed", "qualified"],
    "closed": [],
}

AGENT_MAP = {
    "enrichment": {"stages": ["new"], "description": "Data enrichment via Clearbit/Apollo"},
    "intent": {"stages": ["new", "engaging"], "description": "Intent signal detection"},
    "predictive": {"stages": ["engaging", "qualified"], "description": "Predictive scoring & CLV"},
    "outreach": {"stages": ["engaging", "qualified"], "description": "Multi-channel outreach"},
    "conversation": {"stages": ["qualified"], "description": "AI qualification conversation"},
    "scheduler": {"stages": ["qualified"], "description": "Meeting scheduling"},
}

_blackboard: List[Dict[str, Any]] = []


def evaluate_lead_state(lead_id: int, db: Session) -> Dict[str, Any]:
    from ..models import Lead, Conversation, Meeting
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"error": "Lead not found"}

    current_stage = lead.lifecycle_stage or "new"
    triggers = []
    recommended_agent = None

    intent = lead.intent_score or 0
    enrichment = lead.enrichment_status
    has_conversation = db.query(Conversation).filter(
        Conversation.lead_id == lead_id, Conversation.status == "active"
    ).first() is not None
    has_meeting = db.query(Meeting).filter(
        Meeting.lead_id == lead_id, Meeting.status == "scheduled"
    ).first() is not None

    if has_meeting:
        new_stage = "meeting_booked"
        recommended_agent = "scheduler"
        triggers.append("Meeting booked — transitioning to Meeting Booked stage")
    elif has_conversation:
        new_stage = "qualified"
        recommended_agent = "conversation"
        triggers.append("Active conversation detected — transitioning to Qualified stage")
    elif intent >= 75:
        new_stage = "engaging"
        recommended_agent = "outreach"
        triggers.append(f"High intent score ({intent}) — transitioning to Engaging stage")
    elif intent >= 40:
        new_stage = "engaging"
        recommended_agent = "intent"
        triggers.append(f"Medium intent score ({intent}) — transitioning to Engaging stage")
    elif enrichment in ("completed", "processing"):
        new_stage = "engaging"
        recommended_agent = "intent"
        triggers.append("Enrichment completed — transitioning to Engaging stage")
    else:
        new_stage = "new"
        recommended_agent = "enrichment"
        triggers.append("Lead is new — enrichment agent needed")

    if current_stage == "closed":
        new_stage = "closed"
        recommended_agent = None
        triggers = ["Lead is closed — no further action"]

    return {
        "lead_id": lead_id,
        "current_stage": current_stage,
        "recommended_stage": new_stage,
        "recommended_agent": recommended_agent,
        "triggers": triggers,
    }


def delegate_task(lead_id: int, db: Session) -> Dict[str, Any]:
    state = evaluate_lead_state(lead_id, db)
    if "error" in state:
        return state

    stage = state["recommended_stage"]
    agent = state["recommended_agent"]

    if not agent:
        return {"lead_id": lead_id, "agent": None, "action": None, "reason": "Lead is at terminal stage"}

    action_map = {
        "enrichment": {"agent": "enrichment", "action": "run_enrichment"},
        "intent": {"agent": "intent", "action": "analyze_intent"},
        "predictive": {"agent": "predictive", "action": "calculate_predictions"},
        "outreach": {"agent": "outreach", "action": "generate_draft"},
        "conversation": {"agent": "conversation", "action": "start_conversation"},
        "scheduler": {"agent": "scheduler", "action": "check_schedule"},
    }

    task = action_map.get(agent, {"agent": agent, "action": "monitor"})
    return {
        "lead_id": lead_id,
        "current_stage": state["current_stage"],
        "recommended_stage": stage,
        **task,
        "triggers": state["triggers"],
    }


def update_lifecycle(lead_id: int, new_stage: str, db: Session, trigger_reason: str = "") -> Dict[str, Any]:
    from ..models import Lead, AgentExecutionLog
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"error": "Lead not found"}

    old_stage = lead.lifecycle_stage or "new"
    if new_stage not in LIFECYCLE_STAGES:
        return {"error": f"Invalid stage: {new_stage}"}

    if old_stage != new_stage and new_stage not in LIFECYCLE_TRANSITIONS.get(old_stage, []):
        logger.warning(f"Invalid transition: {old_stage} -> {new_stage}, forcing anyway")

    task = delegate_task(lead_id, db)
    agent = task.get("agent") if "error" not in task else None

    lead.lifecycle_stage = new_stage
    lead.active_agent = agent
    db.commit()

    log = AgentExecutionLog(
        lead_id=lead_id,
        previous_stage=old_stage,
        new_stage=new_stage,
        trigger_reason=trigger_reason or "; ".join(task.get("triggers", [])),
        assigned_agent=agent,
        action=task.get("action", ""),
        outcome=f"Transitioned {old_stage} -> {new_stage}, assigned {agent}",
    )
    db.add(log)

    _blackboard.append({
        "lead_id": lead_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": f"lifecycle_change: {old_stage} -> {new_stage}",
        "agent": agent,
    })

    db.commit()
    return {
        "lead_id": lead_id,
        "previous_stage": old_stage,
        "new_stage": new_stage,
        "assigned_agent": agent,
        "action": task.get("action"),
        "log_id": log.id,
    }


def get_execution_logs(lead_id: int, db: Session) -> List[Dict[str, Any]]:
    from ..models import AgentExecutionLog
    logs = db.query(AgentExecutionLog).filter(
        AgentExecutionLog.lead_id == lead_id
    ).order_by(AgentExecutionLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": log.id,
            "previous_stage": log.previous_stage,
            "new_stage": log.new_stage,
            "trigger_reason": log.trigger_reason,
            "assigned_agent": log.assigned_agent,
            "action": log.action,
            "outcome": log.outcome,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


def get_global_status(db: Session) -> Dict[str, Any]:
    from ..models import Lead
    leads = db.query(Lead).all()
    stages = {}
    agents = {}
    for stage in LIFECYCLE_STAGES:
        stages[stage] = 0
    for lead in leads:
        s = lead.lifecycle_stage or "new"
        stages[s] = stages.get(s, 0) + 1
        if lead.active_agent:
            agents[lead.active_agent] = agents.get(lead.active_agent, 0) + 1
    return {
        "total_leads": len(leads),
        "stages": stages,
        "active_agents": agents,
        "blackboard_entries": len(_blackboard),
    }
