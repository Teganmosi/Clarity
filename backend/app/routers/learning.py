from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import User, ABTest
from ..auth import get_current_user
from ..services.learning_engine import (
    record_outcome, analyze_success_patterns, optimize_intent_weights,
    create_ab_test, get_ab_test_winner,
)

router = APIRouter(prefix="/learning", tags=["Learning"])


@router.get("/insights")
async def get_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return analyze_success_patterns(db)


@router.post("/optimize")
async def optimize_weights(
    dry_run: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = optimize_intent_weights(db)
    if dry_run and result.get("status") == "optimized":
        from ..services.intent_engine import SIGNAL_WEIGHTS
        original = result["original_weights"]
        for k, v in original.items():
            SIGNAL_WEIGHTS[k] = v
        result["status"] = "dry_run"
        result["note"] = "Changes computed but rolled back (dry_run=True). Set dry_run=false to apply."
    return result


@router.get("/ab-tests")
async def list_ab_tests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tests = db.query(ABTest).order_by(ABTest.id.desc()).all()
    return {
        "tests": [
            {
                "id": t.id,
                "name": t.name,
                "variant_a": t.variant_a,
                "variant_b": t.variant_b,
                "metric": t.metric,
                "winner": t.winner,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tests
        ]
    }


@router.post("/ab-tests/create")
async def create_new_ab_test(
    name: str,
    variant_a_subject: str = "Default",
    variant_b_subject: str = "Alternative",
    variant_a_body: str = "Body A",
    variant_b_body: str = "Body B",
    metric: str = "reply_rate",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = create_ab_test(
        db, name,
        {"subject": variant_a_subject, "body": variant_a_body},
        {"subject": variant_b_subject, "body": variant_b_body},
        metric,
    )
    return result


@router.get("/ab-tests/{test_id}/winner")
async def get_winner(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = get_ab_test_winner(test_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/outcome")
async def log_outcome(
    lead_id: int,
    action_id: str,
    outcome_type: str,
    value: float = 1.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = record_outcome(db, lead_id, action_id, outcome_type, value)
    return {"id": log.id, "lead_id": lead_id, "outcome_type": outcome_type, "action_id": action_id}


@router.get("/outcomes/{lead_id}")
async def get_lead_outcomes(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..models import OutcomeLog
    logs = db.query(OutcomeLog).filter(OutcomeLog.lead_id == lead_id).order_by(OutcomeLog.created_at.desc()).limit(50).all()
    return {
        "lead_id": lead_id,
        "outcomes": [
            {
                "id": l.id,
                "action_id": l.action_id,
                "outcome_type": l.outcome_type,
                "value": l.value,
                "extra_data": l.extra_data,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }
