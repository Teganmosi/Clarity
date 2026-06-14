from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..database import get_db
from ..models import User, Lead, Account, RolePermission
from ..auth import get_current_user
from ..services.abm_engine import get_account_health, identify_buying_committee, list_accounts_with_health
from ..services.content_generator import get_battle_card, generate_one_pager

router = APIRouter(prefix="/abm", tags=["ABM"])


def require_role(role: str):
    """Simple RBAC middleware — checks the user's role permission."""
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role == "admin":
            return current_user
        if current_user.role == "manager" and role != "admin":
            return current_user
        if current_user.role == "sdr" and role in ("sdr",):
            return current_user
        raise HTTPException(status_code=403, detail=f"Requires {role} role or higher")
    return checker


@router.get("/accounts")
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = list_accounts_with_health(db)
    return {"accounts": accounts}


@router.post("/accounts/sync")
async def sync_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Auto-create Account records from lead companies."""
    leads = db.query(Lead).filter(Lead.user_id == current_user.id).all()
    companies = set()
    for l in leads:
        if l.company and l.company.strip():
            companies.add((l.company.strip(), l.industry or ""))

    created = 0
    for company_name, industry in companies:
        existing = db.query(Account).filter(Account.company_name == company_name).first()
        if not existing:
            account = Account(
                company_name=company_name,
                domain=company_name.lower().replace(" ", "") + ".com",
                industry=industry,
            )
            db.add(account)
            db.flush()
            created += 1
            for l in leads:
                if l.company and l.company.strip() == company_name:
                    l.account_id = account.id

    db.commit()
    return {"accounts_created": created, "total_companies": len(companies)}


@router.get("/accounts/{account_id}/health")
async def account_health(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = get_account_health(account_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/accounts/{account_id}/committee")
async def buying_committee(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = identify_buying_committee(account_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/content/generate")
async def generate_content(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    context = {
        "name": lead.name,
        "company": lead.company,
        "title": lead.title,
        "tech_stack": ", ".join(lead.technologies or []) if lead.technologies else "Unknown",
        "funding_stage": lead.funding_stage or "Unknown",
        "employee_count": lead.employee_count or "Unknown",
        "industry": lead.industry or "Unknown",
    }
    content = await generate_one_pager(context)
    return content


@router.get("/battle-card/{competitor}")
async def battle_card(
    competitor: str,
    current_user: User = Depends(get_current_user),
):
    return get_battle_card(competitor)


@router.get("/permissions")
async def get_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    perm = db.query(RolePermission).filter(RolePermission.user_id == current_user.id).first()
    if not perm:
        return {
            "user_id": current_user.id,
            "role": getattr(current_user, "role", "sdr"),
            "can_view_all_leads": False,
            "can_delete_leads": False,
            "can_manage_users": False,
            "can_edit_global_settings": False,
            "can_view_analytics": True,
        }
    return {
        "user_id": perm.user_id,
        "role": perm.role,
        "can_view_all_leads": perm.can_view_all_leads,
        "can_delete_leads": perm.can_delete_leads,
        "can_manage_users": perm.can_manage_users,
        "can_edit_global_settings": perm.can_edit_global_settings,
        "can_view_analytics": perm.can_view_analytics,
    }


@router.put("/permissions")
async def update_permissions(
    role: str,
    can_view_all_leads: bool = False,
    can_delete_leads: bool = False,
    can_manage_users: bool = False,
    can_edit_global_settings: bool = False,
    can_view_analytics: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    perm = db.query(RolePermission).filter(RolePermission.user_id == current_user.id).first()
    if not perm:
        perm = RolePermission(user_id=current_user.id, role=role)
        db.add(perm)
    perm.role = role
    perm.can_view_all_leads = can_view_all_leads
    perm.can_delete_leads = can_delete_leads
    perm.can_manage_users = can_manage_users
    perm.can_edit_global_settings = can_edit_global_settings
    perm.can_view_analytics = can_view_analytics
    db.commit()
    return {"status": "updated", "role": role}
