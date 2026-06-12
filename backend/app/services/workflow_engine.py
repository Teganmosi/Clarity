import logging
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

TRIGGER_OPERATORS = {
    "equals": lambda v, t: str(v).lower() == str(t).lower(),
    "not_equals": lambda v, t: str(v).lower() != str(t).lower(),
    "greater_than": lambda v, t: (v or 0) > float(t),
    "less_than": lambda v, t: (v or 0) < float(t),
    "greater_or_equal": lambda v, t: (v or 0) >= float(t),
    "less_or_equal": lambda v, t: (v or 0) <= float(t),
    "contains": lambda v, t: str(t).lower() in str(v or "").lower(),
    "not_contains": lambda v, t: str(t).lower() not in str(v or "").lower(),
    "is_set": lambda v, t: v is not None and v != "",
    "is_not_set": lambda v, t: v is None or v == "",
    "in_list": lambda v, t: str(v or "").lower() in [x.strip().lower() for x in t.split(",")],
    "matches_regex": lambda v, t: bool(re.search(t, str(v or ""), re.IGNORECASE)),
    "days_since": lambda v, t: _days_since(v, t),
    "changed_to": lambda v, t: str(v or "").lower() == str(t).lower(),
}

ACTION_TYPES = {
    "log": lambda lead, params: _do_log(lead, params),
    "update_field": lambda lead, params: _do_update_field(lead, params),
    "send_notification": lambda lead, params: _do_send_notification(lead, params),
    "enrich_lead": lambda lead, params: _do_enrich(lead, params),
    "change_status": lambda lead, params: _do_change_status(lead, params),
    "wait": lambda lead, params: _do_wait(lead, params),
    "webhook": lambda lead, params: _do_webhook(lead, params),
}

_actions_log: List[Dict[str, Any]] = []
_log_id_counter: int = 0


def _days_since(value: Any, target: str) -> bool:
    if not value:
        return False
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value)
        else:
            dt = value
        days = (datetime.utcnow() - dt).days
        return days >= int(target)
    except (ValueError, TypeError):
        return False


class WorkflowRule:
    def __init__(self, rule_id: int, name: str, trigger_field: str, trigger_operator: str,
                 trigger_value: str, action_type: str, action_params: Dict[str, Any],
                 active: bool = True, delay_minutes: int = 0):
        self.id = rule_id
        self.name = name
        self.trigger_field = trigger_field
        self.trigger_operator = trigger_operator
        self.trigger_value = trigger_value
        self.action_type = action_type
        self.action_params = action_params
        self.active = active
        self.delay_minutes = delay_minutes

    def evaluate(self, lead: Any) -> bool:
        if not self.active:
            return False
        operator_fn = TRIGGER_OPERATORS.get(self.trigger_operator)
        if not operator_fn:
            logger.warning(f"Unknown operator: {self.trigger_operator}")
            return False
        field_value = getattr(lead, self.trigger_field, None)
        return operator_fn(field_value, self.trigger_value)

    def execute(self, lead: Any) -> Dict[str, Any]:
        global _log_id_counter
        action_fn = ACTION_TYPES.get(self.action_type)
        if not action_fn:
            return {"rule_id": self.id, "status": "failed", "error": f"Unknown action: {self.action_type}"}
        start_time = time.time()
        _log_id_counter += 1
        log_id = _log_id_counter
        try:
            result = action_fn(lead, self.action_params)
            elapsed = round(time.time() - start_time, 4)
            entry = {
                "log_id": log_id,
                "rule_id": self.id,
                "rule_name": self.name,
                "lead_id": getattr(lead, "id", None),
                "lead_name": getattr(lead, "name", ""),
                "action_type": self.action_type,
                "status": "executed",
                "execution_time": elapsed,
                "step_details": {
                    "trigger_field": self.trigger_field,
                    "trigger_operator": self.trigger_operator,
                    "trigger_value": self.trigger_value,
                    "delay_minutes": self.delay_minutes,
                    "result": result,
                },
                "error_message": None,
                "timestamp": datetime.utcnow().isoformat(),
            }
            _actions_log.append(entry)
            return {"rule_id": self.id, "status": "executed", "log_id": log_id, **result}
        except Exception as e:
            elapsed = round(time.time() - start_time, 4)
            entry = {
                "log_id": log_id,
                "rule_id": self.id,
                "rule_name": self.name,
                "lead_id": getattr(lead, "id", None),
                "lead_name": getattr(lead, "name", ""),
                "action_type": self.action_type,
                "status": "failed",
                "execution_time": elapsed,
                "step_details": None,
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            _actions_log.append(entry)
            logger.error(f"Workflow execution failed for rule {self.id}: {e}")
            return {"rule_id": self.id, "status": "failed", "log_id": log_id, "error": str(e)}


def evaluate_workflows(lead: Any, rules: List[WorkflowRule]) -> List[Dict[str, Any]]:
    results = []
    for rule in rules:
        if rule.evaluate(lead):
            result = rule.execute(lead)
            results.append(result)
    return results


def get_actions_log() -> List[Dict[str, Any]]:
    return list(_actions_log)


def get_logs_by_rule(rule_id: int) -> List[Dict[str, Any]]:
    return [e for e in _actions_log if e["rule_id"] == rule_id]


def clear_actions_log():
    _actions_log.clear()


def _do_log(lead: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    message = params.get("message", "Workflow triggered").format(
        name=getattr(lead, "name", ""),
        company=getattr(lead, "company", ""),
        score=getattr(lead, "score", 0),
        intent_score=getattr(lead, "intent_score", 0),
    )
    logger.info(f"[Workflow Log] {message}")
    return {"logged": True, "message": message}


def _do_update_field(lead: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    field = params.get("field")
    value = params.get("value")
    if field and hasattr(lead, field):
        old = getattr(lead, field)
        setattr(lead, field, value)
        return {"updated": True, "field": field, "from": old, "to": value}
    return {"updated": False, "error": f"Field '{field}' not found"}


def _do_send_notification(lead: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    channel = params.get("channel", "log")
    message = params.get("message", "Action required for {name}").format(
        name=getattr(lead, "name", ""),
        company=getattr(lead, "company", ""),
        score=getattr(lead, "score", 0),
    )
    logger.info(f"[Workflow Notification] {channel.upper()}: {message}")
    return {"sent": True, "channel": channel, "message": message}


def _do_enrich(lead: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"[Workflow Enrich] Triggering enrichment for lead {getattr(lead, 'id', None)}")
    return {"enriched": True, "note": "Enrichment queued"}


def _do_change_status(lead: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    new_status = params.get("status", "contacted")
    if hasattr(lead, "status"):
        old_status = lead.status
        lead.status = new_status
        return {"changed": True, "from": old_status, "to": new_status}
    return {"changed": False, "error": "Lead has no status field"}


def _do_wait(lead: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    duration = params.get("duration_minutes", 0)
    logger.info(f"[Workflow Wait] Delaying action for {duration} minutes on lead {getattr(lead, 'id', None)}")
    return {"delayed": True, "duration_minutes": duration, "status": "scheduled"}


def _do_webhook(lead: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    url = params.get("url", "")
    payload = params.get("payload", {})
    logger.info(f"[Workflow Webhook] Would POST to {url} for lead {getattr(lead, 'id', None)}")
    return {"webhook": True, "url": url, "note": "Webhook call simulated"}
