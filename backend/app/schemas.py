"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation"""
    pass


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    api_key: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Lead Schemas
class LeadBase(BaseModel):
    """Base lead schema"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    company: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    title: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=50)
    campaign: Optional[str] = Field(None, max_length=100)
    medium: Optional[str] = Field(None, max_length=50)
    past_interactions: int = Field(default=0, ge=0)
    pages_visited: int = Field(default=0, ge=0)
    time_on_site: float = Field(default=0.0, ge=0.0)
    company_size: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    budget: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    tags: Optional[str] = None


class LeadCreate(LeadBase):
    """Schema for lead creation"""
    pass


class LeadUpdate(BaseModel):
    """Schema for lead update"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    company: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    title: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=50)
    campaign: Optional[str] = Field(None, max_length=100)
    medium: Optional[str] = Field(None, max_length=50)
    past_interactions: Optional[int] = Field(None, ge=0)
    pages_visited: Optional[int] = Field(None, ge=0)
    time_on_site: Optional[float] = Field(None, ge=0.0)
    company_size: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    budget: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    converted: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class LeadResponse(LeadBase):
    """Schema for lead response"""
    id: int
    user_id: int
    last_interaction_date: Optional[datetime] = None
    score: float
    score_category: str
    conversion_probability: float
    status: str
    converted: bool
    conversion_date: Optional[datetime] = None
    hubspot_id: Optional[str] = None
    pipedrive_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    """Schema for paginated lead list"""
    leads: List[LeadResponse]
    total: int
    page: int
    page_size: int


# Bulk Lead Upload Schemas
class BulkLeadUpload(BaseModel):
    """Schema for bulk lead upload"""
    leads: List[LeadCreate]


class BulkLeadUploadResponse(BaseModel):
    """Schema for bulk upload response"""
    success_count: int
    failed_count: int
    leads: List[LeadResponse]
    errors: List[str]


# Analytics Schemas
class ConversionRateResponse(BaseModel):
    """Schema for conversion rate analytics"""
    total_leads: int
    converted_leads: int
    conversion_rate: float
    by_source: dict
    by_campaign: dict


class ScoreDistributionResponse(BaseModel):
    """Schema for score distribution"""
    hot: int
    warm: int
    cold: int
    average_score: float
    score_ranges: dict


class AnalyticsResponse(BaseModel):
    """Schema for full analytics response"""
    conversion_rate: ConversionRateResponse
    score_distribution: ScoreDistributionResponse
    recent_activity: List[dict]
    trends: List[dict]


# Notification Schemas
class NotificationConfig(BaseModel):
    """Schema for notification configuration"""
    email_enabled: bool = True
    slack_enabled: bool = False
    high_score_threshold: float = Field(default=80.0, ge=0, le=100)
    email_recipient: Optional[EmailStr] = None
    slack_webhook_url: Optional[str] = None


class NotificationSend(BaseModel):
    """Schema for sending notification"""
    lead_id: int
    notification_type: str = Field(..., pattern="^(email|slack)$")
    recipient: str
    subject: Optional[str] = None
    message: str


# Integration Schemas
class IntegrationConfig(BaseModel):
    """Schema for integration configuration"""
    hubspot_api_key: Optional[str] = None
    pipedrive_api_key: Optional[str] = None
    hubspot_enabled: bool = False
    pipedrive_enabled: bool = False


class IntegrationSyncRequest(BaseModel):
    """Schema for integration sync request"""
    lead_ids: Optional[List[int]] = None
    sync_all: bool = False


class IntegrationSyncResponse(BaseModel):
    """Schema for integration sync response"""
    success: bool
    synced_count: int
    failed_count: int
    errors: List[str]


# Auth Schemas
class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class APIKeyAuth(BaseModel):
    """Schema for API key authentication"""
    api_key: str


# Filter Schemas
class LeadFilter(BaseModel):
    """Schema for lead filtering"""
    source: Optional[str] = None
    campaign: Optional[str] = None
    status: Optional[str] = None
    score_min: Optional[float] = Field(None, ge=0, le=100)
    score_max: Optional[float] = Field(None, ge=0, le=100)
    score_category: Optional[str] = Field(None, pattern="^(hot|warm|cold)$")
    company_size: Optional[str] = None
    industry: Optional[str] = None
    converted: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = Field(default="score", pattern="^(score|created_at|name|company)$")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")


# Export Schema
class ExportRequest(BaseModel):
    """Schema for exporting leads"""
    filters: Optional[LeadFilter] = None
    format: str = Field(default="csv", pattern="^(csv|json)$")
