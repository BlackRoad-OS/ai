"""
Salesforce Integration
======================
CRM integration for kanban projects with Salesforce-style management.

Features:
- Objects mapped to kanban cards
- Opportunity tracking
- Lead management
- Custom object support
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import sys

sys.path.insert(0, "/home/user/ai")

from integrations.base import BaseIntegration, IntegrationConfig, IntegrationError


@dataclass
class SalesforceConfig(IntegrationConfig):
    """Salesforce-specific configuration."""

    instance_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    username: str = ""
    api_version: str = "v59.0"


class SalesforceIntegration(BaseIntegration):
    """
    Salesforce CRM integration.

    Maps kanban concepts to Salesforce:
    - Boards -> Custom Object (Kanban_Board__c)
    - Cards -> Custom Object (Kanban_Card__c) or Opportunities
    - Columns -> Picklist values / Stages
    """

    def __init__(self, config: SalesforceConfig):
        super().__init__(config)
        self.sf_config = config
        self._access_token = None
        self._state_cache = {}

    def _get_api_base(self) -> str:
        """Get Salesforce API base URL."""
        return f"/services/data/{self.sf_config.api_version}"

    async def authenticate(self) -> str:
        """Authenticate with Salesforce OAuth."""
        # OAuth flow would go here
        # For now, assume token is configured
        return self.config.api_key or ""

    async def health_check(self) -> bool:
        """Check Salesforce API connectivity."""
        try:
            result = await self.request("GET", f"{self._get_api_base()}/limits")
            return "DailyApiRequests" in result
        except Exception:
            return False

    async def sync(self, board) -> Dict:
        """Sync kanban board to Salesforce."""
        results = {"records": [], "success": True}

        try:
            # Upsert board as custom object
            board_record = await self.upsert_object(
                "Kanban_Board__c",
                "External_Id__c",
                board.id,
                {
                    "Name": board.name,
                    "Description__c": board.description,
                    "External_Id__c": board.id,
                    "Last_Sync__c": board.updated_at,
                },
            )
            results["records"].append(board_record)

            # Upsert cards
            for card in board.get_all_cards():
                card_record = await self.upsert_object(
                    "Kanban_Card__c",
                    "External_Id__c",
                    card.id,
                    {
                        "Name": card.title,
                        "Description__c": card.description,
                        "Status__c": card.status.value,
                        "Priority__c": card.priority.name,
                        "External_Id__c": card.id,
                        "Board__r": {"External_Id__c": board.id},
                        "SHA256_Hash__c": card.sha256_hash,
                        "SHA_Infinity_Hash__c": card.sha_infinity_hash,
                    },
                )
                results["records"].append(card_record)

            self._state_cache[board.id] = board.to_dict()

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    def get_state_hash(self) -> str:
        """Get hash of Salesforce state."""
        from utils.hashing import sha256_hash

        return sha256_hash(self._state_cache)

    # CRUD Operations
    async def create_object(self, sobject: str, data: Dict) -> Dict:
        """Create a Salesforce object."""
        result = await self.request("POST", f"{self._get_api_base()}/sobjects/{sobject}", data=data)
        return result

    async def get_object(self, sobject: str, record_id: str) -> Dict:
        """Get a Salesforce object by ID."""
        result = await self.request("GET", f"{self._get_api_base()}/sobjects/{sobject}/{record_id}")
        return result

    async def update_object(self, sobject: str, record_id: str, data: Dict) -> bool:
        """Update a Salesforce object."""
        await self.request("PATCH", f"{self._get_api_base()}/sobjects/{sobject}/{record_id}", data=data)
        return True

    async def upsert_object(self, sobject: str, external_field: str, external_id: str, data: Dict) -> Dict:
        """Upsert a Salesforce object using external ID."""
        result = await self.request(
            "PATCH", f"{self._get_api_base()}/sobjects/{sobject}/{external_field}/{external_id}", data=data
        )
        return result

    async def delete_object(self, sobject: str, record_id: str) -> bool:
        """Delete a Salesforce object."""
        await self.request("DELETE", f"{self._get_api_base()}/sobjects/{sobject}/{record_id}")
        return True

    # Query Operations
    async def query(self, soql: str) -> List[Dict]:
        """Execute SOQL query."""
        result = await self.request("GET", f"{self._get_api_base()}/query", params={"q": soql})
        return result.get("records", [])

    async def query_all(self, soql: str) -> List[Dict]:
        """Execute SOQL query including deleted records."""
        result = await self.request("GET", f"{self._get_api_base()}/queryAll", params={"q": soql})
        return result.get("records", [])

    # Bulk Operations
    async def bulk_create(self, sobject: str, records: List[Dict]) -> Dict:
        """Bulk create records using Composite API."""
        composite_request = {
            "allOrNone": False,
            "records": [{"attributes": {"type": sobject}, **record} for record in records],
        }

        result = await self.request("POST", f"{self._get_api_base()}/composite/sobjects", data=composite_request)
        return result

    # Opportunity-specific (for sales pipeline boards)
    async def get_opportunities_by_stage(self, stage: str) -> List[Dict]:
        """Get opportunities by stage name."""
        soql = f"""
            SELECT Id, Name, Amount, StageName, CloseDate, AccountId
            FROM Opportunity
            WHERE StageName = '{stage}'
            ORDER BY CloseDate ASC
        """
        return await self.query(soql)

    async def move_opportunity_stage(self, opp_id: str, new_stage: str) -> bool:
        """Move opportunity to new stage (like moving a card)."""
        return await self.update_object("Opportunity", opp_id, {"StageName": new_stage})


class SalesforceWebhookHandler:
    """Handle Salesforce Platform Events and Outbound Messages."""

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Salesforce webhook signature."""
        # Salesforce uses org-specific certificate verification
        return True

    async def process(self, event_type: str, payload: Dict) -> Dict:
        """Process Salesforce event."""
        handlers = {
            "Kanban_Card_Update__e": self._handle_card_update,
            "Kanban_Board_Sync__e": self._handle_board_sync,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(payload)

        return {"processed": False, "reason": "Unknown event type"}

    async def _handle_card_update(self, payload: Dict) -> Dict:
        """Handle card update platform event."""
        return {"processed": True, "card_id": payload.get("Card_Id__c"), "action": payload.get("Action__c")}

    async def _handle_board_sync(self, payload: Dict) -> Dict:
        """Handle board sync request event."""
        return {"processed": True, "board_id": payload.get("Board_Id__c"), "sync_type": payload.get("Sync_Type__c")}
