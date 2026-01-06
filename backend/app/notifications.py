"""
Notification service for sending alerts about high-priority leads
Supports email and Slack notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .models import Lead, NotificationLog
from .schemas import NotificationConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications about high-priority leads
    """
    
    def __init__(self):
        """Initialize notification service"""
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.notification_email = os.getenv("NOTIFICATION_EMAIL", "")
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.high_score_threshold = float(os.getenv("SCORE_THRESHOLD_HIGH", "80"))
    
    async def send_high_priority_alert(self, lead: Lead, db: Session) -> bool:
        """
        Send notification for high-priority lead
        
        Args:
            lead: Lead object
            db: Database session
            
        Returns:
            True if notification sent successfully
        """
        if lead.score < self.high_score_threshold:
            logger.info(f"Lead {lead.id} score {lead.score} below threshold {self.high_score_threshold}")
            return False
        
        success = True
        
        # Send email notification
        if self.notification_email and self.smtp_user and self.smtp_password:
            email_success = await self.send_email_notification(lead, db)
            success = success and email_success
        
        # Send Slack notification
        if self.slack_webhook_url:
            slack_success = await self.send_slack_notification(lead, db)
            success = success and slack_success
        
        return success
    
    async def send_email_notification(self, lead: Lead, db: Session) -> bool:
        """
        Send email notification about a lead
        
        Args:
            lead: Lead object
            db: Database session
            
        Returns:
            True if email sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.notification_email
            msg['Subject'] = f"🔥 High Priority Lead: {lead.name}"
            
            # Create email body
            body = self._create_email_body(lead)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            # Log notification
            self._log_notification(
                db=db,
                lead_id=lead.id,
                notification_type="email",
                recipient=self.notification_email,
                subject=f"High Priority Lead: {lead.name}",
                message=body,
                status="sent"
            )
            
            logger.info(f"Email notification sent for lead {lead.id}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email notification: {error_msg}")
            
            # Log failed notification
            self._log_notification(
                db=db,
                lead_id=lead.id,
                notification_type="email",
                recipient=self.notification_email,
                subject=f"High Priority Lead: {lead.name}",
                message=body if 'body' in locals() else "",
                status="failed",
                error_message=error_msg
            )
            
            return False
    
    async def send_slack_notification(self, lead: Lead, db: Session) -> bool:
        """
        Send Slack notification about a lead
        
        Args:
            lead: Lead object
            db: Database session
            
        Returns:
            True if Slack notification sent successfully
        """
        try:
            # Create Slack message
            message = self._create_slack_message(lead)
            
            # Send to Slack webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=message,
                    timeout=10.0
                )
                response.raise_for_status()
            
            # Log notification
            self._log_notification(
                db=db,
                lead_id=lead.id,
                notification_type="slack",
                recipient=self.slack_webhook_url,
                subject=f"High Priority Lead: {lead.name}",
                message=str(message),
                status="sent"
            )
            
            logger.info(f"Slack notification sent for lead {lead.id}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send Slack notification: {error_msg}")
            
            # Log failed notification
            self._log_notification(
                db=db,
                lead_id=lead.id,
                notification_type="slack",
                recipient=self.slack_webhook_url,
                subject=f"High Priority Lead: {lead.name}",
                message=str(message) if 'message' in locals() else "",
                status="failed",
                error_message=error_msg
            )
            
            return False
    
    def _create_email_body(self, lead: Lead) -> str:
        """
        Create HTML email body for lead notification
        
        Args:
            lead: Lead object
            
        Returns:
            HTML email body
        """
        score_color = "#10b981" if lead.score >= 80 else "#f59e0b" if lead.score >= 50 else "#ef4444"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 20px; border-radius: 0 0 10px 10px; }}
                .score-box {{ background: {score_color}; color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; }}
                .score-value {{ font-size: 36px; font-weight: bold; }}
                .info-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }}
                .info-label {{ font-weight: bold; color: #6b7280; }}
                .info-value {{ color: #111827; }}
                .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔥 High Priority Lead Alert</h1>
                    <p>A new high-scoring lead needs your attention!</p>
                </div>
                <div class="content">
                    <div class="score-box">
                        <div>Lead Score</div>
                        <div class="score-value">{lead.score:.1f}</div>
                        <div>{lead.score_category.upper()}</div>
                    </div>
                    
                    <h2>Lead Information</h2>
                    <div class="info-row">
                        <span class="info-label">Name:</span>
                        <span class="info-value">{lead.name}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Email:</span>
                        <span class="info-value">{lead.email}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Company:</span>
                        <span class="info-value">{lead.company or 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Title:</span>
                        <span class="info-value">{lead.title or 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Source:</span>
                        <span class="info-value">{lead.source or 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Campaign:</span>
                        <span class="info-value">{lead.campaign or 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Interactions:</span>
                        <span class="info-value">{lead.past_interactions}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Company Size:</span>
                        <span class="info-value">{lead.company_size or 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Budget:</span>
                        <span class="info-value">{lead.budget or 'N/A'}</span>
                    </div>
                    
                    <p><strong>Conversion Probability:</strong> {lead.conversion_probability * 100:.1f}%</p>
                    
                    <div style="text-align: center;">
                        <a href="#" class="cta-button">View Lead Details</a>
                    </div>
                    
                    <div class="footer">
                        <p>Lead Scoring Engine | Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _create_slack_message(self, lead: Lead) -> Dict:
        """
        Create Slack message for lead notification
        
        Args:
            lead: Lead object
            
        Returns:
            Slack message dictionary
        """
        emoji = "🔥" if lead.score >= 80 else "⚡" if lead.score >= 50 else "❄️"
        
        message = {
            "text": f"{emoji} High Priority Lead Alert",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} High Priority Lead Alert"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Name:*\n{lead.name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Email:*\n{lead.email}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Company:*\n{lead.company or 'N/A'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Title:*\n{lead.title or 'N/A'}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Score:*\n{lead.score:.1f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Category:*\n{lead.score_category.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Source:*\n{lead.source or 'N/A'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Campaign:*\n{lead.campaign or 'N/A'}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Conversion Probability:* {lead.conversion_probability * 100:.1f}%"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Lead Details"
                            },
                            "url": f"http://localhost:5173/leads/{lead.id}",
                            "style": "primary"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
        
        return message
    
    def _log_notification(
        self,
        db: Session,
        lead_id: int,
        notification_type: str,
        recipient: str,
        subject: str,
        message: str,
        status: str,
        error_message: str = None
    ):
        """
        Log notification to database
        
        Args:
            db: Database session
            lead_id: Lead ID
            notification_type: Type of notification (email/slack)
            recipient: Recipient address
            subject: Subject line
            message: Message content
            status: Status (sent/failed)
            error_message: Error message if failed
        """
        try:
            log = NotificationLog(
                lead_id=lead_id,
                notification_type=notification_type,
                recipient=recipient,
                subject=subject,
                message=message,
                status=status,
                error_message=error_message
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
    
    async def send_bulk_notifications(
        self,
        leads: List[Lead],
        db: Session,
        config: Optional[NotificationConfig] = None
    ) -> Dict[str, int]:
        """
        Send notifications for multiple leads
        
        Args:
            leads: List of lead objects
            db: Database session
            config: Optional notification config
            
        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0}
        
        for lead in leads:
            success = await self.send_high_priority_alert(lead, db)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results


# Global notification service instance
notification_service = NotificationService()


async def send_lead_notification(lead: Lead, db: Session) -> bool:
    """
    Send notification for a lead
    
    Args:
        lead: Lead object
        db: Database session
        
    Returns:
        True if notification sent successfully
    """
    return await notification_service.send_high_priority_alert(lead, db)


async def send_bulk_lead_notifications(leads: List[Lead], db: Session) -> Dict[str, int]:
    """
    Send notifications for multiple leads
    
    Args:
        leads: List of lead objects
        db: Database session
        
    Returns:
        Dictionary with success/failure counts
    """
    return await notification_service.send_bulk_notifications(leads, db)
