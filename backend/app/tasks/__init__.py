from celery import Celery
from celery.schedules import crontab
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "clarity_tasks",
    broker=redis_url,
    backend=redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "analyze-all-leads-intent": {
        "task": "backend.app.tasks.analyze_all_leads_task",
        "schedule": crontab(hour=0, minute=0),
    },
}


@celery_app.task
def analyze_all_leads_task():
    from app.database import SessionLocal
    from app.models import Lead
    from app.services.intent_engine import calculate_intent_score

    db = SessionLocal()
    try:
        leads = db.query(Lead).all()
        for lead in leads:
            result = calculate_intent_score(lead)
            lead.intent_score = result["intent_score"]
            lead.intent_signals = result["intent_signals"]
            lead.last_intent_check = result["last_intent_check"]
        db.commit()
        return {"status": "success", "analyzed": len(leads)}
    except Exception as e:
        db.rollback()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
