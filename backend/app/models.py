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
    
    # Enrichment Data (Sprint 1: API Integration Framework)
    technologies = Column(JSON, default=list)
    funding_stage = Column(String(50))
    funding_amount = Column(Integer)
    employee_count = Column(Integer)
    company_description = Column(Text)
    logo_url = Column(String(500))
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))

    # Intent Signals (Sprint 2)
    intent_score = Column(Integer, default=0)
    intent_signals = Column(JSON, default=list)
    last_intent_update = Column(DateTime(timezone=True))

    # Enrichment Metadata
    enriched_at = Column(DateTime(timezone=True))
    enrichment_source = Column(String(50))
    enrichment_data = Column(JSON, default=dict)

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
