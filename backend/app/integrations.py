"""
CRM Integration service for HubSpot and Pipedrive
Includes mock implementations for MVP
"""

import httpx
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .models import Lead, IntegrationLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CRMIntegration:
    """
    Base class for CRM integrations
    """
    
    def __init__(self, api_key: str, base_url: str):
        """
        Initialize CRM integration
        
        Args:
            api_key: API key for the CRM
            base_url: Base URL for the CRM API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.enabled = bool(api_key)
    
    async def create_contact(self, lead: Lead, db: Session) -> Dict:
        """
        Create a contact in the CRM
        
        Args:
            lead: Lead object
            db: Database session
            
        Returns:
            Response with CRM contact ID
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    async def update_contact(self, lead: Lead, db: Session) -> Dict:
        """
        Update a contact in the CRM
        
        Args:
            lead: Lead object
            db: Database session
            
        Returns:
            Response with update status
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    async def sync_leads(self, leads: List[Lead], db: Session) -> Dict:
        """
        Sync multiple leads to the CRM
        
        Args:
            leads: List of lead objects
            db: Database session
            
        Returns:
            Response with sync results
        """
        results = {"success": 0, "failed": 0, "errors": []}
        
        for lead in leads:
            try:
                if lead.hubspot_id or lead.pipedrive_id:
                    # Update existing contact
                    await self.update_contact(lead, db)
                else:
                    # Create new contact
                    await self.create_contact(lead, db)
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Lead {lead.id}: {str(e)}")
        
        return results
    
    def _log_integration(
        self,
        db: Session,
        lead_id: int,
        integration_type: str,
        action: str,
        external_id: str,
        request_data: str,
        response_data: str,
        status: str,
        error_message: str = None
    ):
        """
        Log integration activity to database
        
        Args:
            db: Database session
            lead_id: Lead ID
            integration_type: Type of integration (hubspot/pipedrive)
            action: Action performed (create/update/sync)
            external_id: External CRM ID
            request_data: Request data
            response_data: Response data
            status: Status (success/failed)
            error_message: Error message if failed
        """
        try:
            log = IntegrationLog(
                lead_id=lead_id,
                integration_type=integration_type,
                action=action,
                external_id=external_id,
                request_data=request_data,
                response_data=response_data,
                status=status,
                error_message=error_message
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log integration: {e}")


class HubSpotIntegration(CRMIntegration):
    """
    HubSpot CRM integration
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize HubSpot integration
        
        Args:
            api_key: HubSpot API key
        """
        api_key = api_key or os.getenv("HUBSPOT_API_KEY", "")
        base_url = "https://api.hubapi.com/crm/v3/objects/contacts"
        super().__init__(api_key, base_url)
    
    async def create_contact(self, lead: Lead, db: Session) -> Dict:
        """
        Create a contact in HubSpot
        
        Args:
            lead: Lead object
            db: Database session
            
        Returns:
            Response with HubSpot contact ID
        """
        if not self.enabled:
            logger.warning("HubSpot integration not enabled - no API key configured")
            return {
                "success": False,
                "error": "HubSpot integration is not configured. Please add your HubSpot API key in the environment variables.",
                "code": "INTEGRATION_NOT_CONFIGURED"
            }
        
        try:
            # Prepare contact data
            contact_data = {
                "properties": {
                    "email": lead.email,
                    "firstname": lead.name.split()[0] if lead.name else "",
                    "lastname": " ".join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else "",
                    "company": lead.company or "",
                    "phone": lead.phone or "",
                    "jobtitle": lead.title or "",
                    "lead_source": lead.source or "",
                    "lead_score": str(lead.score),
                    "conversion_probability": str(lead.conversion_probability),
                    "past_interactions": str(lead.past_interactions),
                    "company_size": lead.company_size or "",
                    "budget": lead.budget or ""
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # For MVP, we'll mock the API call
            # In production, uncomment the actual API call:
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         self.base_url,
            #         json=contact_data,
            #         headers=headers,
            #         timeout=10.0
            #     )
            #     response.raise_for_status()
            #     result = response.json()
            #     hubspot_id = result["id"]
            
            # Mock response for MVP
            hubspot_id = f"hubspot_{lead.id}_{datetime.now().timestamp()}"
            result = {"id": hubspot_id}
            
            # Update lead with HubSpot ID
            lead.hubspot_id = hubspot_id
            
            # Log integration
            self._log_integration(
                db=db,
                lead_id=lead.id,
                integration_type="hubspot",
                action="create",
                external_id=hubspot_id,
                request_data=str(contact_data),
                response_data=str(result),
                status="success"
            )
            
            logger.info(f"Created HubSpot contact {hubspot_id} for lead {lead.id}")
            return {"success": True, "hubspot_id": hubspot_id}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to create HubSpot contact: {error_msg}")
            
            # Log failed integration
            self._log_integration(
                db=db,
                lead_id=lead.id,
                integration_type="hubspot",
                action="create",
                external_id="",
                request_data=str(contact_data) if 'contact_data' in locals() else "",
                response_data="",
                status="failed",
                error_message=error_msg
            )
            
            return {"success": False, "error": error_msg}
    
    async def update_contact(self, lead: Lead, db: Session) -> Dict:
        """
        Update a contact in HubSpot
        
        Args:
            lead: Lead object
            db: Database session
            
        Returns:
            Response with update status
        """
        if not self.enabled:
            logger.warning("HubSpot integration not enabled - no API key configured")
            return {
                "success": False,
                "error": "HubSpot integration is not configured. Please add your HubSpot API key in the environment variables.",
                "code": "INTEGRATION_NOT_CONFIGURED"
            }
        
        if not lead.hubspot_id:
            logger.warning(f"Cannot update HubSpot contact - no HubSpot ID for lead {lead.id}")
            return {
                "success": False,
                "error": f"Lead {lead.id} is not synced with HubSpot. Please create the contact first.",
                "code": "NO_EXTERNAL_ID"
            }
        
        try:
            # Prepare contact data
            contact_data = {
                "properties": {
                    "email": lead.email,
                    "firstname": lead.name.split()[0] if lead.name else "",
                    "lastname": " ".join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else "",
                    "company": lead.company or "",
                    "phone": lead.phone or "",
                    "jobtitle": lead.title or "",
                    "lead_source": lead.source or "",
                    "lead_score": str(lead.score),
                    "conversion_probability": str(lead.conversion_probability),
                    "past_interactions": str(lead.past_interactions),
                    "company_size": lead.company_size or "",
                    "budget": lead.budget or ""
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # For MVP, we'll mock the API call
            # In production, uncomment the actual API call:
            # async with httpx.AsyncClient() as client:
            #     response = await client.patch(
            #         f"{self.base_url}/{lead.hubspot_id}",
            #         json=contact_data,
            #         headers=headers,
            #         timeout=10.0
            #     )
            #     response.raise_for_status()
            #     result = response.json()
            
            # Mock response for MVP
            result = {"id": lead.hubspot_id, "updated": True}
            
            # Log integration
            self._log_integration(
                db=db,
                lead_id=lead.id,
                integration_type="hubspot",
                action="update",
                external_id=lead.hubspot_id,
                request_data=str(contact_data),
                response_data=str(result),
                status="success"
            )
            
            logger.info(f"Updated HubSpot contact {lead.hubspot_id} for lead {lead.id}")
            return {"success": True, "hubspot_id": lead.hubspot_id}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to update HubSpot contact: {error_msg}")
            
            # Log failed integration
            self._log_integration(
                db=db,
                lead_id=lead.id,
                integration_type="hubspot",
                action="update",
                external_id=lead.hubspot_id,
                request_data=str(contact_data) if 'contact_data' in locals() else "",
                response_data="",
                status="failed",
                error_message=error_msg
            )
            
            return {"success": False, "error": error_msg}


class PipedriveIntegration(CRMIntegration):
    """
    Pipedrive CRM integration
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize Pipedrive integration
        
        Args:
            api_key: Pipedrive API key
        """
        api_key = api_key or os.getenv("PIPEDRIVE_API_KEY", "")
        base_url = f"https://{api_key}@api.pipedrive.com/v1/persons"
        super().__init__(api_key, base_url)
    
    async def create_contact(self, lead: Lead, db: Session) -> Dict:
        """
        Create a person in Pipedrive
        
        Args:
            lead: Lead object
            db: Database session
            
        Returns:
            Response with Pipedrive person ID
        """
        if not self.enabled:
            logger.warning("Pipedrive integration not enabled - no API key configured")
            return {
                "success": False,
                "error": "Pipedrive integration is not configured. Please add your Pipedrive API key in the environment variables.",
                "code": "INTEGRATION_NOT_CONFIGURED"
            }
        
        try:
            # Prepare person data
            person_data = {
                "name": lead.name,
                "email": [{"value": lead.email, "primary": True}],
                "phone": [{"value": lead.phone, "primary": True}] if lead.phone else [],
                "org_id": None,  # Would need to create organization first
                "job_title": lead.title or "",
                "lead_score": lead.score,
                "conversion_probability": lead.conversion_probability,
                "past_interactions": lead.past_interactions,
                "company_size": lead.company_size or "",
                "budget": lead.budget or "",
                "lead_source": lead.source or ""
            }
            
            # For MVP, we'll mock the API call
            # In production, uncomment the actual API call:
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         f"{self.base_url}",
            #         json=person_data,
            #         timeout=10.0
            #     )
            #     response.raise_for_status()
            #     result = response.json()
            #     pipedrive_id = str(result["data"]["id"])
            
            # Mock response for MVP
            pipedrive_id = f"pipedrive_{lead.id}_{datetime.now().timestamp()}"
            result = {"data": {"id": pipedrive_id}}
            
            # Update lead with Pipedrive ID
            lead.pipedrive_id = pipedrive_id
            
            # Log integration
            self._log_integration(
                db=db,
                lead_id=lead.id,
                integration_type="pipedrive",
                action="create",
                external_id=pipedrive_id,
                request_data=str(person_data),
                response_data=str(result),
                status="success"
            )
            
            logger.info(f"Created Pipedrive person {pipedrive_id} for lead {lead.id}")
            return {"success": True, "pipedrive_id": pipedrive_id}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to create Pipedrive person: {error_msg}")
            
            # Log failed integration
            self._log_integration(
                db=db,
                lead_id=lead.id,
                integration_type="pipedrive",
                action="create",
                external_id="",
                request_data=str(person_data) if 'person_data' in locals() else "",
                response_data="",
                status="failed",
                error_message=error_msg
            )
            
            return {"success": False, "error": error_msg}
    
    async def update_contact(self, lead: Lead, db: Session) -> Dict:
        """
        Update a person in Pipedrive
        
        Args:
            lead: Lead object
            db: Database session
            
        Returns:
            Response with update status
        """
        if not self.enabled:
            logger.warning("Pipedrive integration not enabled - no API key configured")
            return {
                "success": False,
                "error": "Pipedrive integration is not configured. Please add your Pipedrive API key in the environment variables.",
                "code": "INTEGRATION_NOT_CONFIGURED"
            }
        
        if not lead.pipedrive_id:
            logger.warning(f"Cannot update Pipedrive person - no Pipedrive ID for lead {lead.id}")
            return {
                "success": False,
                "error": f"Lead {lead.id} is not synced with Pipedrive. Please create the person first.",
                "code": "NO_EXTERNAL_ID"
            }
        
        try:
            # Prepare person data
            person_data = {
                "name": lead.name,
                "email": [{"value": lead.email, "primary": True}],
                "phone": [{"value": lead.phone, "primary": True}] if lead.phone else [],
                "job_title": lead.title or "",
                "lead_score": lead.score,
                "conversion_probability": lead.conversion_probability,
                "past_interactions": lead.past_interactions,
                "company_size": lead.company_size or "",
                "budget": lead.budget or "",
                "lead_source": lead.source or ""
            }
            
            # For MVP, we'll mock the API call
            # In production, uncomment the actual API call:
            # async with httpx.AsyncClient() as client:
            #     response = await client.put(
            #         f"{self.base_url}/{lead.pipedrive_id}",
            #         json=person_data,
            #         timeout=10.0
            #     )
            #     response.raise_for_status()
            #     result = response.json()
            
            # Mock response for MVP
            result = {"data": {"id": lead.pipedrive_id, "updated": True}}
            
            # Log integration
            self._log_integration(
                db=db,
                lead_id=lead.id,
                integration_type="pipedrive",
                action="update",
                external_id=lead.pipedrive_id,
                request_data=str(person_data),
                response_data=str(result),
                status="success"
            )
            
            logger.info(f"Updated Pipedrive person {lead.pipedrive_id} for lead {lead.id}")
            return {"success": True, "pipedrive_id": lead.pipedrive_id}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to update Pipedrive person: {error_msg}")
            
            # Log failed integration
            self._log_integration(
                db=db,
                lead_id=lead.id,
                integration_type="pipedrive",
                action="update",
                external_id=lead.pipedrive_id,
                request_data=str(person_data) if 'person_data' in locals() else "",
                response_data="",
                status="failed",
                error_message=error_msg
            )
            
            return {"success": False, "error": error_msg}


# Global integration instances
hubspot_integration = HubSpotIntegration()
pipedrive_integration = PipedriveIntegration()


async def sync_to_hubspot(lead: Lead, db: Session) -> Dict:
    """
    Sync a lead to HubSpot
    
    Args:
        lead: Lead object
        db: Database session
        
    Returns:
        Response with sync status
    """
    return await hubspot_integration.create_contact(lead, db)


async def sync_to_pipedrive(lead: Lead, db: Session) -> Dict:
    """
    Sync a lead to Pipedrive
    
    Args:
        lead: Lead object
        db: Database session
        
    Returns:
        Response with sync status
    """
    return await pipedrive_integration.create_contact(lead, db)


async def bulk_sync_to_hubspot(leads: List[Lead], db: Session) -> Dict:
    """
    Bulk sync leads to HubSpot
    
    Args:
        leads: List of lead objects
        db: Database session
        
    Returns:
        Response with sync results
    """
    return await hubspot_integration.sync_leads(leads, db)


async def bulk_sync_to_pipedrive(leads: List[Lead], db: Session) -> Dict:
    """
    Bulk sync leads to Pipedrive
    
    Args:
        leads: List of lead objects
        db: Database session
        
    Returns:
        Response with sync results
    """
    return await pipedrive_integration.sync_leads(leads, db)
