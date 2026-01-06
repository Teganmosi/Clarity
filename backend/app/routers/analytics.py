"""
Analytics router
Provides analytics endpoints for conversion rates, score distribution, and insights
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from typing import List, Dict
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Lead, User, NotificationLog
from ..schemas import ConversionRateResponse, ScoreDistributionResponse, AnalyticsResponse
from ..auth import get_current_user

# Create router
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/conversion-rate", response_model=ConversionRateResponse)
async def get_conversion_rate(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get conversion rate analytics
    
    Returns:
    - Total leads
    - Converted leads
    - Overall conversion rate
    - Conversion rate by source
    - Conversion rate by campaign
    """
    # Get total leads
    total_leads = db.query(Lead).filter(Lead.user_id == current_user.id).count()
    
    # Get converted leads
    converted_leads = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.converted == True
    ).count()
    
    # Calculate overall conversion rate
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
    
    # Get conversion rate by source
    source_stats = db.query(
        Lead.source,
        func.count(Lead.id).label('total'),
        func.sum(func.cast(Lead.converted, Integer)).label('converted')
    ).filter(
        Lead.user_id == current_user.id
    ).group_by(Lead.source).all()
    
    by_source = {}
    for source, total, converted in source_stats:
        if source:
            by_source[source] = {
                'total': total,
                'converted': int(converted or 0),
                'conversion_rate': round((int(converted or 0) / total * 100), 2) if total > 0 else 0.0
            }
    
    # Get conversion rate by campaign
    campaign_stats = db.query(
        Lead.campaign,
        func.count(Lead.id).label('total'),
        func.sum(func.cast(Lead.converted, Integer)).label('converted')
    ).filter(
        Lead.user_id == current_user.id
    ).group_by(Lead.campaign).all()
    
    by_campaign = {}
    for campaign, total, converted in campaign_stats:
        if campaign:
            by_campaign[campaign] = {
                'total': total,
                'converted': int(converted or 0),
                'conversion_rate': round((int(converted or 0) / total * 100), 2) if total > 0 else 0.0
            }
    
    return {
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'conversion_rate': round(conversion_rate, 2),
        'by_source': by_source,
        'by_campaign': by_campaign
    }


@router.get("/score-distribution", response_model=ScoreDistributionResponse)
async def get_score_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get score distribution analytics
    
    Returns:
    - Count of hot leads (score >= 80)
    - Count of warm leads (50 <= score < 80)
    - Count of cold leads (score < 50)
    - Average score
    - Score ranges distribution
    """
    # Get count by score category
    hot_count = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score_category == 'hot'
    ).count()
    
    warm_count = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score_category == 'warm'
    ).count()
    
    cold_count = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score_category == 'cold'
    ).count()
    
    # Get average score
    avg_score_result = db.query(func.avg(Lead.score)).filter(
        Lead.user_id == current_user.id
    ).first()
    
    average_score = round(float(avg_score_result[0] or 0), 2)
    
    # Get score ranges
    score_ranges = {
        '0-20': 0,
        '21-40': 0,
        '41-60': 0,
        '61-80': 0,
        '81-100': 0
    }
    
    range_0_20 = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score >= 0,
        Lead.score <= 20
    ).count()
    score_ranges['0-20'] = range_0_20
    
    range_21_40 = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score >= 21,
        Lead.score <= 40
    ).count()
    score_ranges['21-40'] = range_21_40
    
    range_41_60 = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score >= 41,
        Lead.score <= 60
    ).count()
    score_ranges['41-60'] = range_41_60
    
    range_61_80 = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score >= 61,
        Lead.score <= 80
    ).count()
    score_ranges['61-80'] = range_61_80
    
    range_81_100 = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score >= 81,
        Lead.score <= 100
    ).count()
    score_ranges['81-100'] = range_81_100
    
    return {
        'hot': hot_count,
        'warm': warm_count,
        'cold': cold_count,
        'average_score': average_score,
        'score_ranges': score_ranges
    }


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete dashboard analytics
    
    Returns comprehensive analytics including:
    - Conversion rate analytics
    - Score distribution
    - Recent activity
    """
    # Get conversion rate
    conversion_rate = await get_conversion_rate(current_user, db)
    
    # Get score distribution
    score_distribution = await get_score_distribution(current_user, db)
    
    # Get recent activity (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    recent_leads = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= seven_days_ago
    ).order_by(Lead.created_at.desc()).limit(10).all()
    
    recent_activity = []
    for lead in recent_leads:
        activity = {
            'type': 'new_lead',
            'lead_id': lead.id,
            'lead_name': lead.name,
            'lead_email': lead.email,
            'score': lead.score,
            'score_category': lead.score_category,
            'timestamp': lead.created_at.isoformat() if lead.created_at else None
        }
        recent_activity.append(activity)
    
    # Get recent conversions
    recent_conversions = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.converted == True,
        Lead.conversion_date >= seven_days_ago
    ).order_by(Lead.conversion_date.desc()).limit(5).all()
    
    for lead in recent_conversions:
        activity = {
            'type': 'conversion',
            'lead_id': lead.id,
            'lead_name': lead.name,
            'lead_email': lead.email,
            'score': lead.score,
            'timestamp': lead.conversion_date.isoformat() if lead.conversion_date else None
        }
        recent_activity.append(activity)
    
    # Sort by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'] or '', reverse=True)

    # Get trends (last 30 days)
    trends = await get_trends(30, current_user, db)
    
    return {
        'conversion_rate': conversion_rate,
        'score_distribution': score_distribution,
        'recent_activity': recent_activity[:15],  # Limit to 15 items
        'trends': trends
    }


@router.get("/source-performance")
async def get_source_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance metrics by lead source
    
    Returns:
    - Total leads by source
    - Average score by source
    - Conversion rate by source
    """
    source_stats = db.query(
        Lead.source,
        func.count(Lead.id).label('total'),
        func.avg(Lead.score).label('avg_score'),
        func.sum(func.cast(Lead.converted, Integer)).label('converted')
    ).filter(
        Lead.user_id == current_user.id
    ).group_by(Lead.source).all()
    
    performance = []
    for source, total, avg_score, converted in source_stats:
        if source:
            performance.append({
                'source': source,
                'total_leads': total,
                'average_score': round(float(avg_score or 0), 2),
                'converted_leads': int(converted or 0),
                'conversion_rate': round((int(converted or 0) / total * 100), 2) if total > 0 else 0.0
            })
    
    # Sort by conversion rate descending
    performance.sort(key=lambda x: x['conversion_rate'], reverse=True)
    
    return performance


@router.get("/campaign-performance")
async def get_campaign_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance metrics by campaign
    
    Returns:
    - Total leads by campaign
    - Average score by campaign
    - Conversion rate by campaign
    """
    campaign_stats = db.query(
        Lead.campaign,
        func.count(Lead.id).label('total'),
        func.avg(Lead.score).label('avg_score'),
        func.sum(func.cast(Lead.converted, Integer)).label('converted')
    ).filter(
        Lead.user_id == current_user.id
    ).group_by(Lead.campaign).all()
    
    performance = []
    for campaign, total, avg_score, converted in campaign_stats:
        if campaign:
            performance.append({
                'campaign': campaign,
                'total_leads': total,
                'average_score': round(float(avg_score or 0), 2),
                'converted_leads': int(converted or 0),
                'conversion_rate': round((int(converted or 0) / total * 100), 2) if total > 0 else 0.0
            })
    
    # Sort by conversion rate descending
    performance.sort(key=lambda x: x['conversion_rate'], reverse=True)
    
    return performance


@router.get("/trends")
async def get_trends(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get lead trends over time
    
    Args:
        days: Number of days to analyze (default: 30)
    
    Returns:
    - Daily lead counts
    - Daily conversion counts
    - Average scores over time
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # Get daily lead counts
    daily_leads = db.query(
        func.date(Lead.created_at).label('date'),
        func.count(Lead.id).label('count')
    ).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= start_date
    ).group_by(func.date(Lead.created_at)).all()
    
    # Get daily conversion counts
    daily_conversions = db.query(
        func.date(Lead.conversion_date).label('date'),
        func.count(Lead.id).label('count')
    ).filter(
        Lead.user_id == current_user.id,
        Lead.converted == True,
        Lead.conversion_date >= start_date
    ).group_by(func.date(Lead.conversion_date)).all()
    
    # Get daily average scores
    daily_scores = db.query(
        func.date(Lead.created_at).label('date'),
        func.avg(Lead.score).label('avg_score')
    ).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= start_date
    ).group_by(func.date(Lead.created_at)).all()
    
    # Convert to dictionaries
    leads_by_date = {str(date): count for date, count in daily_leads}
    conversions_by_date = {str(date): count for date, count in daily_conversions}
    scores_by_date = {str(date): round(float(avg_score), 2) for date, avg_score in daily_scores}
    
    # Generate all dates in range
    trends = []
    current_date = start_date.date()
    end_date = datetime.now().date()
    
    while current_date <= end_date:
        date_str = str(current_date)
        trends.append({
            'date': date_str,
            'leads': leads_by_date.get(date_str, 0),
            'conversions': conversions_by_date.get(date_str, 0),
            'average_score': scores_by_date.get(date_str, 0.0)
        })
        current_date += timedelta(days=1)
    
    return trends


@router.get("/notifications-summary")
async def get_notifications_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summary of sent notifications
    
    Returns:
    - Total notifications sent
    - Notifications by type (email/slack)
    - Success rate
    - Recent notifications
    """
    # Get lead IDs for current user
    user_lead_ids = db.query(Lead.id).filter(Lead.user_id == current_user.id).subquery()
    
    # Get total notifications
    total_notifications = db.query(NotificationLog).filter(
        NotificationLog.lead_id.in_(user_lead_ids)
    ).count()
    
    # Get notifications by type
    email_count = db.query(NotificationLog).filter(
        NotificationLog.lead_id.in_(user_lead_ids),
        NotificationLog.notification_type == 'email'
    ).count()
    
    slack_count = db.query(NotificationLog).filter(
        NotificationLog.lead_id.in_(user_lead_ids),
        NotificationLog.notification_type == 'slack'
    ).count()
    
    # Get success rate
    success_count = db.query(NotificationLog).filter(
        NotificationLog.lead_id.in_(user_lead_ids),
        NotificationLog.status == 'sent'
    ).count()
    
    success_rate = round((success_count / total_notifications * 100), 2) if total_notifications > 0 else 0.0
    
    # Get recent notifications
    recent_notifications = db.query(NotificationLog).filter(
        NotificationLog.lead_id.in_(user_lead_ids)
    ).order_by(NotificationLog.sent_at.desc()).limit(10).all()
    
    recent = []
    for notif in recent_notifications:
        recent.append({
            'id': notif.id,
            'lead_id': notif.lead_id,
            'notification_type': notif.notification_type,
            'recipient': notif.recipient,
            'subject': notif.subject,
            'status': notif.status,
            'sent_at': notif.sent_at.isoformat() if notif.sent_at else None
        })
    
    return {
        'total_notifications': total_notifications,
        'by_type': {
            'email': email_count,
            'slack': slack_count
        },
        'success_rate': success_rate,
        'recent_notifications': recent
    }
