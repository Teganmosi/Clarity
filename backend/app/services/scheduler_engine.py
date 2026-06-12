import os
import logging
import random
from datetime import datetime, timedelta, timezone, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

BUSINESS_HOURS_START = 9
BUSINESS_HOURS_END = 17
DEFAULT_DURATION = int(os.getenv("MEETING_DURATION_MINUTES", "30"))
MOCK_BOOKED_SLOTS: List[datetime] = []


def _generate_random_slots(base_date: date) -> List[datetime]:
    slots = []
    for hour in range(BUSINESS_HOURS_START, BUSINESS_HOURS_END):
        for minute in [0, 30]:
            slot_time = datetime(base_date.year, base_date.month, base_date.day, hour, minute, tzinfo=timezone.utc)
            if slot_time > datetime.now(timezone.utc):
                slots.append(slot_time)
    return slots


def get_available_slots(date_str: str, duration: int = DEFAULT_DURATION, timezone_str: str = "UTC") -> List[Dict[str, Any]]:
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    all_slots = _generate_random_slots(target_date)
    available = []

    for slot in all_slots:
        conflict = False
        for booked in MOCK_BOOKED_SLOTS:
            if abs((slot - booked).total_seconds()) < duration * 60:
                conflict = True
                break
        if not conflict:
            local_slot = slot
            if timezone_str and timezone_str != "UTC":
                try:
                    import pytz
                    tz = pytz.timezone(timezone_str)
                    local_slot = slot.astimezone(tz)
                except Exception:
                    pass
            available.append({
                "utc": slot.isoformat(),
                "local": local_slot.isoformat(),
                "timezone": timezone_str,
                "duration_minutes": duration,
                "display": local_slot.strftime("%a, %b %d at %I:%M %p"),
            })

    return available


def generate_calendar_invite(meeting_details: Dict[str, Any]) -> str:
    from icalendar import Calendar, Event, vText
    cal = Calendar()
    cal.add("prodid", "-//Clarity//Meeting Scheduler//EN")
    cal.add("version", "2.0")

    event = Event()
    event.add("uid", str(meeting_details.get("id", "")))
    event.add("summary", meeting_details.get("summary", "Meeting with Clarity"))
    event.add("dtstart", meeting_details["start_time"])
    event.add("dtend", meeting_details["end_time"])
    event.add("description", meeting_details.get("description", ""))
    event.add("location", vText(meeting_details.get("location", "Virtual")))

    lead_email = meeting_details.get("lead_email", "")
    if lead_email:
        event.add("attendee", vText(f"mailto:{lead_email}"))

    organizer = meeting_details.get("organizer_email", "scheduler@clarity.com")
    event.add("organizer", vText(f"mailto:{organizer}"))

    cal.add_component(event)
    return cal.to_ical().decode("utf-8")


def book_meeting(lead_id: int, slot_utc: str, duration: int = DEFAULT_DURATION,
                 timezone_str: str = "UTC", lead_name: str = "", lead_email: str = "",
                 meeting_link: str = "") -> Dict[str, Any]:
    try:
        start_time = datetime.fromisoformat(slot_utc)
    except ValueError:
        return {"error": "Invalid slot format. Use ISO datetime."}

    end_time = start_time + timedelta(minutes=duration)
    MOCK_BOOKED_SLOTS.append(start_time)

    meeting_id = random.randint(10000, 99999)
    meeting_link = meeting_link or f"https://meet.clarity.ai/{meeting_id}"

    details = {
        "id": meeting_id,
        "lead_id": lead_id,
        "lead_name": lead_name,
        "lead_email": lead_email,
        "summary": f"Clarity Demo with {lead_name}",
        "description": f"AI-powered lead scoring demo for {lead_name}. We'll cover intent detection, predictive analytics, and automate outreach.",
        "location": "Virtual - Clarity Meet",
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": duration,
        "timezone": timezone_str,
        "meeting_link": meeting_link,
        "organizer_email": "scheduler@clarity.com",
    }

    ics_content = generate_calendar_invite(details)

    return {
        "meeting_id": meeting_id,
        "lead_id": lead_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_minutes": duration,
        "timezone": timezone_str,
        "meeting_link": meeting_link,
        "ics_content": ics_content,
    }


def check_upcoming_reminders(db: Session) -> List[Dict[str, Any]]:
    from ..models import Meeting
    now = datetime.now(timezone.utc)
    reminder_window = now + timedelta(hours=1)
    upcoming = db.query(Meeting).filter(
        Meeting.status == "scheduled",
        Meeting.scheduled_time >= now,
        Meeting.scheduled_time <= reminder_window,
    ).all()
    return [
        {
            "id": m.id,
            "lead_id": m.lead_id,
            "scheduled_time": m.scheduled_time.isoformat(),
            "meeting_link": m.meeting_link,
        }
        for m in upcoming
    ]
