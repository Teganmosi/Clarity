import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_account_health(account_id: int, db: Session) -> Dict[str, Any]:
    from ..models import Account, Lead, Meeting, CommunicationLog

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"error": "Account not found"}

    leads = db.query(Lead).filter(Lead.account_id == account_id).all()
    total_leads = len(leads)
    if total_leads == 0:
        return {"account_id": account_id, "company_name": account.company_name, "health_score": 0, "total_leads": 0, "buying_stage": "unknown"}

    avg_intent = sum(l.intent_score or 0 for l in leads) / total_leads
    meetings = db.query(Meeting).filter(Meeting.lead_id.in_([l.id for l in leads])).count()
    conversations = sum(1 for l in leads if hasattr(l, 'intent_score') and l.intent_score > 0)
    enriched = sum(1 for l in leads if l.enrichment_status == "completed")

    health = int((avg_intent * 0.4) + (min(meetings, 10) * 5) + (enriched / max(total_leads, 1) * 20))

    if health >= 70:
        stage = "pipeline"
    elif health >= 40:
        stage = "engaging"
    elif health >= 20:
        stage = "awareness"
    else:
        stage = "new"

    account.health_score = health
    account.buying_stage = stage
    db.commit()

    return {
        "account_id": account_id,
        "company_name": account.company_name,
        "domain": account.domain,
        "health_score": health,
        "buying_stage": stage,
        "total_leads": total_leads,
        "avg_intent_score": round(avg_intent, 1),
        "meetings_booked": meetings,
        "contacts_enriched": enriched,
    }


def identify_buying_committee(account_id: int, db: Session) -> Dict[str, Any]:
    from ..models import Lead, Account

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"error": "Account not found"}

    leads = db.query(Lead).filter(Lead.account_id == account_id).all()
    committee = []

    for lead in leads:
        title_lower = (lead.title or "").lower()
        role = _infer_role(title_lower, lead.intent_score or 0)
        committee.append({
            "lead_id": lead.id,
            "name": lead.name,
            "title": lead.title,
            "email": lead.email,
            "intent_score": lead.intent_score or 0,
            "role": role,
            "status": lead.status,
        })

    score = sum(1 for c in committee if c["role"] == "dm") * 30
    score += sum(1 for c in committee if c["role"] == "influencer") * 20
    score += sum(1 for c in committee if c["role"] == "user") * 10
    coverage = min(score, 100)

    return {
        "account_id": account_id,
        "company_name": account.company_name,
        "committee": committee,
        "coverage_score": coverage,
        "missing_roles": _missing_roles(committee),
    }


def _infer_role(title: str, intent: int) -> str:
    dm_keywords = ["ceo", "cto", "cfo", "coo", "cmo", "chief", "vp", "s vice president", "head of", "director", "owner", "founder", "president"]
    influencer_keywords = ["manager", "lead", "senior", "team lead", "architect", "principal"]
    user_keywords = ["engineer", "analyst", "associate", "coordinator", "specialist", "representative"]

    if any(k in title for k in dm_keywords):
        return "dm"
    if any(k in title for k in influencer_keywords):
        return "influencer"
    if any(k in title for k in user_keywords):
        return "user"
    if intent >= 75:
        return "influencer"
    return "unknown"


def _missing_roles(committee: List[Dict]) -> List[str]:
    roles = {c["role"] for c in committee}
    missing = []
    if "dm" not in roles:
        missing.append("Decision Maker")
    if "influencer" not in roles and "dm" not in roles:
        missing.append("Influencer")
    return missing


def list_accounts_with_health(db: Session) -> List[Dict[str, Any]]:
    from ..models import Account
    accounts = db.query(Account).all()
    return [
        {
            "id": a.id,
            "company_name": a.company_name,
            "domain": a.domain,
            "industry": a.industry,
            "health_score": a.health_score or 0,
            "buying_stage": a.buying_stage or "unknown",
            "total_revenue": a.total_revenue or 0,
            "employee_count": a.employee_count,
        }
        for a in accounts
    ]
