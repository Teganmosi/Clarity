from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from ..database import get_db
from ..models import User, Lead, Meeting
from ..auth import get_current_user
from ..services.scheduler_engine import get_available_slots, book_meeting

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.get("/slots")
async def available_slots(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    duration: int = Query(30, description="Meeting duration in minutes"),
    timezone: str = Query("UTC", description="Lead's timezone"),
    current_user: User = Depends(get_current_user),
):
    slots = get_available_slots(date, duration, timezone)
    if isinstance(slots, dict) and "error" in slots:
        raise HTTPException(status_code=400, detail=slots["error"])
    return {"date": date, "duration": duration, "timezone": timezone, "slots": slots}


@router.post("/book")
async def book_meeting_endpoint(
    lead_id: int,
    slot_utc: str,
    duration: int = 30,
    timezone: str = "UTC",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = book_meeting(
        lead_id=lead_id,
        slot_utc=slot_utc,
        duration=duration,
        timezone_str=timezone,
        lead_name=lead.name,
        lead_email=lead.email,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    meeting = Meeting(
        lead_id=lead_id,
        scheduled_time=datetime.fromisoformat(result["start_time"]),
        duration_minutes=result["duration_minutes"],
        timezone=result["timezone"],
        status="scheduled",
        meeting_link=result["meeting_link"],
        ics_content=result["ics_content"],
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    if lead.status != "Meeting Booked":
        lead.status = "Meeting Booked"
        db.commit()

    return {
        "meeting_id": meeting.id,
        "lead_id": lead_id,
        "start_time": result["start_time"],
        "end_time": result["end_time"],
        "duration_minutes": result["duration_minutes"],
        "timezone": result["timezone"],
        "meeting_link": result["meeting_link"],
        "ics_content": result["ics_content"],
    }


@router.get("/meetings/{lead_id}")
async def get_lead_meetings(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    meetings = db.query(Meeting).filter(Meeting.lead_id == lead_id).order_by(Meeting.scheduled_time.desc()).all()
    return {
        "lead_id": lead_id,
        "meetings": [
            {
                "id": m.id,
                "scheduled_time": m.scheduled_time.isoformat() if m.scheduled_time else None,
                "duration_minutes": m.duration_minutes,
                "timezone": m.timezone,
                "status": m.status,
                "meeting_link": m.meeting_link,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in meetings
        ],
    }


@router.post("/cancel/{meeting_id}")
async def cancel_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting.status = "cancelled"
    db.commit()
    return {"meeting_id": meeting_id, "status": "cancelled"}


@router.get("/upcoming")
async def list_upcoming_meetings(
    filter: str = Query("all", description="all/today/week"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import datetime as dt
    from datetime import timezone
    query = db.query(Meeting).join(Lead).filter(Lead.user_id == current_user.id)

    now = datetime.now(timezone.utc)
    if filter == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + dt.timedelta(days=1)
        query = query.filter(Meeting.scheduled_time >= start, Meeting.scheduled_time < end)
    elif filter == "week":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + dt.timedelta(days=7)
        query = query.filter(Meeting.scheduled_time >= start, Meeting.scheduled_time < end)

    meetings = query.order_by(Meeting.scheduled_time.asc()).all()
    return {
        "filter": filter,
        "meetings": [
            {
                "id": m.id,
                "lead_id": m.lead_id,
                "scheduled_time": m.scheduled_time.isoformat() if m.scheduled_time else None,
                "duration_minutes": m.duration_minutes,
                "timezone": m.timezone,
                "status": m.status,
                "meeting_link": m.meeting_link,
            }
            for m in meetings
        ],
    }
