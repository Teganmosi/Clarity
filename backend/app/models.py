"""
Database models for the Lead Scoring Engine
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """
    User model for authentication
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for backward compatibility
    api_key = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    leads = relationship("Lead", back_populates="user", cascade="all, delete-orphan")


class Lead(Base):
    """
    Lead model - stores lead information and scores
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # ABM / Account association (Sprint 11)
    account_id = Column(Integer, ForeignKey("accounts.id"))

    # Lead basic information
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    company = Column(String(100))
    phone = Column(String(20))
    title = Column(String(100))
    
    # Lead source information
    source = Column(String(50), index=True)  # website, referral, paid_ads, etc.
    campaign = Column(String(100))
    medium = Column(String(50))  # organic, cpc, email, etc.
    
    # Lead engagement metrics
    past_interactions = Column(Integer, default=0)
    last_interaction_date = Column(DateTime(timezone=True))
    pages_visited = Column(Integer, default=0)
    time_on_site = Column(Float, default=0.0)  # in minutes
    
    # Lead qualification
    company_size = Column(String(50))  # small, medium, large, enterprise
    industry = Column(String(100))
    budget = Column(String(50))  # low, medium, high, enterprise
    
    # Scoring information
    score = Column(Float, default=0.0)  # 0-100 conversion probability
    score_category = Column(String(20))  # hot, warm, cold
    conversion_probability = Column(Float, default=0.0)
    
    # Status
    status = Column(String(20), default="new")  # new, contacted, qualified, converted, lost
    converted = Column(Boolean, default=False)
    conversion_date = Column(DateTime(timezone=True))
    
    # External CRM IDs
    hubspot_id = Column(String(50))
    pipedrive_id = Column(String(50))
    
    # Predictive Analytics (Sprint 3: Advanced Analytics & Automation)
    predicted_closure_prob = Column(Float, default=0.0)
    estimated_clv = Column(Float, default=0.0)
    forecast_close_date = Column(String(20))

    # Intent Detection (Sprint 2: Intent Detection Engine)
    intent_score = Column(Integer, default=0)
    last_intent_check = Column(DateTime(timezone=True))
    intent_signals = Column(JSON, default=list)

    # Enrichment Data (Sprint 1: API Integration Framework)
    technologies = Column(JSON, default=list)              # Tech stack array
    lifecycle_stage = Column(String(30), default="new")     # new, engaging, qualified, meeting_booked, closed
    active_agent = Column(String(30))                       # enrichment, intent, predictive, outreach, conversation, scheduler
    preferred_language = Column(String(10), default="en")   # Sprint 12: Multi-language
    region = Column(String(20))                              # Sprint 12: Region for compliance
    compliance_flags = Column(JSON, default=dict)            # Sprint 12: GDPR/CCPA flags

    funding_stage = Column(String(50))                     # Seed, Series A, etc.
    employee_count = Column(Integer)                       # Company size
    logo_url = Column(String(500))                         # Company logo URL
    linkedin_url = Column(String(500))                     # LinkedIn profile URL
    twitter_handle = Column(String(100))                   # Twitter/X handle
    annual_revenue = Column(String(50))                    # Annual revenue range
    headquarters_location = Column(String(200))            # HQ city/country
    founded_year = Column(Integer)                         # Year founded
    industry_tags = Column(JSON, default=list)             # Industry classification tags
    tech_stack_last_updated = Column(DateTime(timezone=True))  # When tech stack was refreshed
    enrichment_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    enrichment_source = Column(String(50))                 # clearbit, apollo, etc.
    last_enriched_at = Column(DateTime(timezone=True))     # Last enrichment timestamp

    # Metadata
    notes = Column(Text)
    tags = Column(Text)  # Comma-separated tags
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="leads")


class NotificationLog(Base):
    """
    Log of all notifications sent
    """
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    notification_type = Column(String(20))  # email, slack
    recipient = Column(String(200))
    subject = Column(String(200))
    message = Column(Text)
    status = Column(String(20))  # sent, failed
    error_message = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())


class GlobalSuppression(Base):
    __tablename__ = "global_suppressions"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), index=True)
    phone = Column(String(50), index=True)
    reason = Column(String(100), default="user_request")
    added_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommunicationLog(Base):
    __tablename__ = "communication_logs"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    channel = Column(String(20), nullable=False)
    status = Column(String(20), default="sent")
    subject = Column(String(200))
    body = Column(Text)
    message_id = Column(String(100))
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "channel": self.channel,
            "status": self.status,
            "subject": self.subject,
            "body": self.body,
            "message_id": self.message_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


class EmailOutreach(Base):
    __tablename__ = "email_outreach"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    subject = Column(String(200))
    body = Column(Text)
    status = Column(String(20), default="draft")
    sent_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    ai_model_used = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    channel = Column(String(20), default="chat")
    messages = Column(JSON, default=list)
    bant_scores = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    previous_stage = Column(String(30))
    new_stage = Column(String(30))
    trigger_reason = Column(Text)
    assigned_agent = Column(String(30))
    action = Column(String(200))
    outcome = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VoiceCallLog(Base):
    __tablename__ = "voice_call_logs"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    status = Column(String(20), default="initiated")
    phone_number = Column(String(30))
    language = Column(String(10), default="en")
    transcript = Column(Text)
    recording_url = Column(String(500))
    call_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30)
    timezone = Column(String(50), default="UTC")
    status = Column(String(20), default="scheduled")
    meeting_link = Column(String(500))
    ics_content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OutcomeLog(Base):
    __tablename__ = "outcome_logs"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    action_id = Column(String(100))
    outcome_type = Column(String(50))
    value = Column(Float, default=1.0)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ABTest(Base):
    __tablename__ = "ab_tests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    variant_a = Column(JSON, default=dict)
    variant_b = Column(JSON, default=dict)
    metric = Column(String(50), default="reply_rate")
    winner = Column(String(10))
    status = Column(String(20), default="running")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False)
    domain = Column(String(200), index=True)
    industry = Column(String(100))
    total_revenue = Column(Float, default=0.0)
    employee_count = Column(Integer)
    health_score = Column(Integer, default=0)
    churn_risk_score = Column(Integer, default=0)
    expansion_score = Column(Integer, default=0)
    health_status = Column(String(20), default="healthy")
    last_health_check = Column(DateTime(timezone=True))
    buying_stage = Column(String(30), default="awareness")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    leads = relationship("Lead", backref="account", foreign_keys="Lead.account_id")


class HealthSnapshot(Base):
    __tablename__ = "health_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    health_score = Column(Integer)
    churn_risk = Column(Integer)
    expansion_score = Column(Integer)
    snapshot_date = Column(DateTime(timezone=True), server_default=func.now())


class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(30), default="sdr")
    can_view_all_leads = Column(Boolean, default=False)
    can_delete_leads = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    can_edit_global_settings = Column(Boolean, default=False)
    can_view_analytics = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnonymizedOutcome(Base):
    __tablename__ = "anonymized_outcomes"
    id = Column(Integer, primary_key=True, index=True)
    hashed_identifier = Column(String(64), index=True)
    industry_tag = Column(String(100))
    funding_stage = Column(String(50))
    action = Column(String(100))
    action_type = Column(String(50))
    success = Column(Boolean, default=False)
    channel = Column(String(20), default="email")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NetworkInsight(Base):
    __tablename__ = "network_insights"
    id = Column(Integer, primary_key=True, index=True)
    segment = Column(JSON, default=dict)
    insight_type = Column(String(50))
    metric_value = Column(Float)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    value = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    contract_content = Column(Text)
    status = Column(String(20), default="draft")
    signing_url = Column(String(500))
    payment_link = Column(String(500))
    payment_intent_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    signed_at = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))


class ContractLog(Base):
    __tablename__ = "contract_logs"
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    action = Column(String(50))
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IntegrationLog(Base):
    """
    Log of CRM integration activities
    """
    __tablename__ = "integration_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    integration_type = Column(String(20))  # hubspot, pipedrive
    action = Column(String(50))  # create, update, sync
    external_id = Column(String(50))
    request_data = Column(Text)
    response_data = Column(Text)
    status = Column(String(20))  # success, failed
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
