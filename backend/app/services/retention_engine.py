import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CHURN_THRESHOLD = int(__import__("os").getenv("CHURN_THRESHOLD", "70"))
EXPANSION_THRESHOLD = int(__import__("os").getenv("EXPANSION_THRESHOLD", "80"))


def calculate_churn_score(account_id: int, db: Session) -> Dict[str, Any]:
    from ..models import Account, Lead, CommunicationLog, OutcomeLog, Conversation

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"error": "Account not found"}

    leads = db.query(Lead).filter(Lead.account_id == account_id).all()
    risk_factors = []
    score = 0

    current_avg_intent = sum(l.intent_score or 0 for l in leads) / max(len(leads), 1)
    if current_avg_intent < 20:
        score += 30
        risk_factors.append({"factor": "Low intent engagement", "impact": 30, "detail": f"Average intent score is {current_avg_intent:.0f}/100"})
    elif current_avg_intent < 40:
        score += 15
        risk_factors.append({"factor": "Declining intent", "impact": 15, "detail": f"Average intent is {current_avg_intent:.0f} — below healthy threshold"})

    recent_negative = 0
    conversations = db.query(Conversation).filter(Conversation.lead_id.in_([l.id for l in leads])).all()
    for c in conversations:
        bant = c.bant_scores or {}
        if bant.get("sentiment") == "Negative":
            recent_negative += 1
    if recent_negative >= 2:
        score += 25
        risk_factors.append({"factor": "Negative conversation sentiment", "impact": 25, "detail": f"{recent_negative} conversations with negative sentiment"})

    aged_leads = sum(1 for l in leads if l.status in ("new", "") and (l.created_at and (datetime.now(timezone.utc) - l.created_at).days > 90))
    if aged_leads >= 2:
        score += 20
        risk_factors.append({"factor": "Stale leads", "impact": 20, "detail": f"{aged_leads} leads untouched for 90+ days"})

    if not any(l.enrichment_status == "completed" for l in leads):
        score += 15
        risk_factors.append({"factor": "No enrichment completed", "impact": 15, "detail": "Account has no enriched leads"})

    no_meetings = sum(1 for l in leads if l.status not in ("Meeting Booked", "converted"))
    if no_meetings == len(leads) and len(leads) > 0:
        score += 10
        risk_factors.append({"factor": "No meetings booked", "impact": 10, "detail": "None of the leads have moved to meeting stage"})

    score = min(score, 100)
    risk_factors = sorted(risk_factors, key=lambda x: x["impact"], reverse=True)[:3]

    account.churn_risk_score = score
    account.health_status = "critical" if score >= CHURN_THRESHOLD else "at_risk" if score >= 40 else "healthy"
    account.last_health_check = datetime.now(timezone.utc)
    db.commit()

    return {
        "account_id": account_id,
        "company_name": account.company_name,
        "churn_risk_score": score,
        "risk_factors": risk_factors,
        "health_status": account.health_status,
    }


def calculate_expansion_score(account_id: int, db: Session) -> Dict[str, Any]:
    from ..models import Account, Lead

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"error": "Account not found"}

    leads = db.query(Lead).filter(Lead.account_id == account_id).all()
    score = 0
    signals = []

    avg_intent = sum(l.intent_score or 0 for l in leads) / max(len(leads), 1)
    if avg_intent >= 75:
        score += 30
        signals.append({"signal": "High intent engagement", "weight": 30})
    elif avg_intent >= 40:
        score += 15
        signals.append({"signal": "Moderate intent engagement", "weight": 15})

    funded = [l for l in leads if l.funding_stage and l.funding_stage.lower() not in ("", "none", "bootstrapped")]
    if funded:
        score += 25
        signals.append({"signal": f"Recent funding ({funded[0].funding_stage})", "weight": 25})

    meeting_booked = sum(1 for l in leads if l.status == "Meeting Booked")
    if meeting_booked >= 1:
        score += 20
        signals.append({"signal": f"{meeting_booked} meeting(s) booked", "weight": 20})

    employee_count = account.employee_count or 0
    if employee_count > 200:
        score += 15
        signals.append({"signal": f"Enterprise size ({employee_count} employees)", "weight": 15})
    elif employee_count > 50:
        score += 10
        signals.append({"signal": f"Mid-market size ({employee_count} employees)", "weight": 10})

    enriched = sum(1 for l in leads if l.enrichment_status == "completed")
    if enriched >= 3:
        score += 10
        signals.append({"signal": f"{enriched} enriched contacts", "weight": 10})

    score = min(score, 100)

    recommended_product = "Enterprise Plan" if score >= EXPANSION_THRESHOLD else "Growth Plan" if score >= 50 else "Retain on Current Plan"

    account.expansion_score = score
    db.commit()

    return {
        "account_id": account_id,
        "company_name": account.company_name,
        "expansion_score": score,
        "signals": sorted(signals, key=lambda x: x["weight"], reverse=True),
        "recommended_product": recommended_product,
    }


def trigger_retention_workflow(account_id: int, db: Session) -> Dict[str, Any]:
    churn = calculate_churn_score(account_id, db)
    if "error" in churn:
        return churn

    actions = []
    if churn.get("churn_risk_score", 0) >= CHURN_THRESHOLD:
        actions.append({
            "type": "alert",
            "priority": "high",
            "action": "Notify account manager immediately",
        })
        actions.append({
            "type": "email",
            "priority": "high",
            "action": f"Send personalized check-in email to {churn.get('company_name')}",
        })
    elif churn.get("churn_risk_score", 0) >= 40:
        actions.append({
            "type": "task",
            "priority": "medium",
            "action": "Schedule a health check call with the account team",
        })

    expansion = calculate_expansion_score(account_id, db)
    if "error" not in expansion:
        if expansion.get("expansion_score", 0) >= EXPANSION_THRESHOLD:
            actions.append({
                "type": "upsell",
                "priority": "high",
                "action": f"Send {expansion.get('recommended_product')} proposal",
            })

    return {
        "account_id": account_id,
        "company_name": churn.get("company_name"),
        "churn_risk_score": churn.get("churn_risk_score", 0),
        "expansion_score": expansion.get("expansion_score", 0) if "error" not in expansion else 0,
        "health_status": churn.get("health_status", "unknown"),
        "recommended_actions": actions,
    }


def get_health_trends(db: Session, account_id: int = None) -> List[Dict[str, Any]]:
    from ..models import HealthSnapshot
    query = db.query(HealthSnapshot)
    if account_id:
        query = query.filter(HealthSnapshot.account_id == account_id)
    snapshots = query.order_by(HealthSnapshot.snapshot_date.desc()).limit(30).all()
    return [
        {
            "id": s.id,
            "account_id": s.account_id,
            "health_score": s.health_score,
            "churn_risk": s.churn_risk,
            "expansion_score": s.expansion_score,
            "snapshot_date": s.snapshot_date.isoformat() if s.snapshot_date else None,
        }
        for s in reversed(snapshots)
    ]


def snapshot_all_accounts(db: Session):
    from ..models import Account, HealthSnapshot
    accounts = db.query(Account).all()
    for acc in accounts:
        churn = calculate_churn_score(acc.id, db)
        expansion = calculate_expansion_score(acc.id, db)
        if "error" not in churn and "error" not in expansion:
            shot = HealthSnapshot(
                account_id=acc.id,
                health_score=acc.health_score,
                churn_risk=churn.get("churn_risk_score", 0),
                expansion_score=expansion.get("expansion_score", 0),
            )
            db.add(shot)
    db.commit()
