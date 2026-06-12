from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/workflow-templates", tags=["Workflow Templates"])

TEMPLATES = [
    {
        "id": "high-intent-alert",
        "name": "High Intent Lead Alert",
        "description": "Notify sales team when a lead shows strong buying intent",
        "category": "Lead Scoring",
        "icon": "Zap",
        "rules": [
            {
                "name": "High Intent Detection",
                "trigger_field": "intent_score",
                "trigger_operator": "greater_than",
                "trigger_value": "75",
                "action_type": "send_notification",
                "action_params": {"channel": "log", "message": "High intent lead detected: {name} ({company}) - Score: {intent_score}"},
                "delay_minutes": 0,
            }
        ],
    },
    {
        "id": "stalled-deal-revival",
        "name": "Stalled Deal Revival",
        "description": "Re-engage leads that haven't been contacted in 30+ days",
        "category": "Sales",
        "icon": "RefreshCw",
        "rules": [
            {
                "name": "Stalled Lead Check",
                "trigger_field": "last_interaction_date",
                "trigger_operator": "days_since",
                "trigger_value": "30",
                "action_type": "change_status",
                "action_params": {"status": "contacted"},
                "delay_minutes": 0,
            },
            {
                "name": "Notify Owner",
                "trigger_field": "status",
                "trigger_operator": "changed_to",
                "trigger_value": "contacted",
                "action_type": "log",
                "action_params": {"message": "Stalled deal revived: {name} - last interaction was 30+ days ago"},
                "delay_minutes": 0,
            },
        ],
    },
    {
        "id": "series-b-outreach",
        "name": "Series B Outreach",
        "description": "Auto-enrich and prioritize leads that raised Series B funding",
        "category": "Enrichment",
        "icon": "TrendingUp",
        "rules": [
            {
                "name": "Series B Detection",
                "trigger_field": "funding_stage",
                "trigger_operator": "contains",
                "trigger_value": "series b",
                "action_type": "enrich_lead",
                "action_params": {},
                "delay_minutes": 0,
            },
            {
                "name": "Update Score",
                "trigger_field": "funding_stage",
                "trigger_operator": "contains",
                "trigger_value": "series b",
                "action_type": "update_field",
                "action_params": {"field": "score", "value": 85},
                "delay_minutes": 0,
            },
        ],
    },
    {
        "id": "tech-adoption-signal",
        "name": "Tech Stack Change Alert",
        "description": "Get notified when a lead adopts new technologies (5+ techs detected)",
        "category": "Intent",
        "icon": "Cpu",
        "rules": [
            {
                "name": "Tech Stack Size Check",
                "trigger_field": "employee_count",
                "trigger_operator": "greater_than",
                "trigger_value": "50",
                "action_type": "log",
                "action_params": {"message": "Growing company ({name}) with {employee_count} employees - potential tech buyer"},
                "delay_minutes": 0,
            }
        ],
    },
    {
        "id": "enterprise-pipeline",
        "name": "Enterprise Pipeline Builder",
        "description": "Flag and enrich enterprise-sized leads for senior sales",
        "category": "Sales",
        "icon": "Building2",
        "rules": [
            {
                "name": "Enterprise Size Check",
                "trigger_field": "employee_count",
                "trigger_operator": "greater_than",
                "trigger_value": "200",
                "action_type": "change_status",
                "action_params": {"status": "qualified"},
                "delay_minutes": 0,
            },
            {
                "name": "Enterprise Notification",
                "trigger_field": "score",
                "trigger_operator": "greater_than",
                "trigger_value": "60",
                "action_type": "send_notification",
                "action_params": {"channel": "log", "message": "Enterprise lead qualified: {name} ({company}) - Score: {score}"},
                "delay_minutes": 0,
            },
        ],
    },
    {
        "id": "revenue-milestone",
        "name": "Revenue Milestone Tracker",
        "description": "Track leads with reported revenue growth signals",
        "category": "Analytics",
        "icon": "DollarSign",
        "rules": [
            {
                "name": "Revenue Signal",
                "trigger_field": "annual_revenue",
                "trigger_operator": "is_set",
                "trigger_value": "",
                "action_type": "log",
                "action_params": {"message": "Revenue data available for {name} ({company}): {annual_revenue}"},
                "delay_minutes": 0,
            }
        ],
    },
]


@router.get("/")
async def list_templates():
    return {"templates": TEMPLATES}


@router.get("/{template_id}")
async def get_template(template_id: str):
    for t in TEMPLATES:
        if t["id"] == template_id:
            return t
    return {"error": "Template not found"}
