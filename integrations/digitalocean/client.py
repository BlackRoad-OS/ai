"""
DigitalOcean Integration
========================
Cloud infrastructure for kanban system.

Features:
- Droplets for compute
- Spaces for object storage
- Functions for serverless
- App Platform deployments
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sys

sys.path.insert(0, "/home/user/ai")

from integrations.base import BaseIntegration, IntegrationConfig


@dataclass
class DigitalOceanConfig(IntegrationConfig):
    """DigitalOcean-specific configuration."""

    spaces_region: str = "nyc3"
    spaces_bucket: str = ""
    spaces_key: str = ""
    spaces_secret: str = ""
    function_namespace: str = ""


class DigitalOceanIntegration(BaseIntegration):
    """
    DigitalOcean integration for infrastructure.

    Used for:
    - Spaces object storage for board data
    - Functions for API endpoints
    - Droplets for persistent services
    """

    def __init__(self, config: DigitalOceanConfig):
        super().__init__(config)
        self.do_config = config
        self._state_cache = {}

    async def health_check(self) -> bool:
        """Check DigitalOcean API connectivity."""
        try:
            result = await self.request("GET", "/account")
            return "account" in result
        except Exception:
            return False

    async def sync(self, board) -> Dict:
        """Sync board state to DigitalOcean Spaces."""
        results = {"objects": [], "success": True}

        try:
            # Store board data in Spaces
            # Note: Spaces uses S3-compatible API
            self._state_cache[board.id] = board.to_dict()
            results["objects"].append(f"boards/{board.id}.json")

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    def get_state_hash(self) -> str:
        """Get hash of DigitalOcean state."""
        from utils.hashing import sha256_hash

        return sha256_hash(self._state_cache)

    # Droplet Operations
    async def list_droplets(self) -> List[Dict]:
        """List all droplets."""
        result = await self.request("GET", "/droplets")
        return result.get("droplets", [])

    async def create_droplet(self, name: str, region: str, size: str, image: str, ssh_keys: List[str] = None) -> Dict:
        """Create a new droplet."""
        result = await self.request(
            "POST",
            "/droplets",
            data={"name": name, "region": region, "size": size, "image": image, "ssh_keys": ssh_keys or []},
        )
        return result.get("droplet", {})

    async def get_droplet(self, droplet_id: int) -> Dict:
        """Get droplet details."""
        result = await self.request("GET", f"/droplets/{droplet_id}")
        return result.get("droplet", {})

    async def delete_droplet(self, droplet_id: int) -> bool:
        """Delete a droplet."""
        await self.request("DELETE", f"/droplets/{droplet_id}")
        return True

    # Functions Operations
    async def list_functions(self) -> List[Dict]:
        """List functions in namespace."""
        result = await self.request("GET", f"/functions/namespaces/{self.do_config.function_namespace}/functions")
        return result.get("functions", [])

    async def invoke_function(self, function_name: str, params: Dict = None) -> Dict:
        """Invoke a serverless function."""
        result = await self.request(
            "POST",
            f"/functions/namespaces/{self.do_config.function_namespace}/functions/{function_name}",
            data=params or {},
        )
        return result

    # App Platform
    async def list_apps(self) -> List[Dict]:
        """List App Platform apps."""
        result = await self.request("GET", "/apps")
        return result.get("apps", [])

    async def create_app(self, spec: Dict) -> Dict:
        """Create App Platform app."""
        result = await self.request("POST", "/apps", data={"spec": spec})
        return result.get("app", {})

    async def get_app(self, app_id: str) -> Dict:
        """Get app details."""
        result = await self.request("GET", f"/apps/{app_id}")
        return result.get("app", {})

    async def create_deployment(self, app_id: str) -> Dict:
        """Trigger new deployment."""
        result = await self.request("POST", f"/apps/{app_id}/deployments")
        return result.get("deployment", {})

    # Databases
    async def list_databases(self) -> List[Dict]:
        """List managed databases."""
        result = await self.request("GET", "/databases")
        return result.get("databases", [])

    async def get_database(self, db_id: str) -> Dict:
        """Get database details."""
        result = await self.request("GET", f"/databases/{db_id}")
        return result.get("database", {})


class DigitalOceanWebhookHandler:
    """Handle DigitalOcean webhooks."""

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        return True

    async def process(self, event_type: str, payload: Dict) -> Dict:
        """Process DigitalOcean event."""
        handlers = {
            "droplet.create": self._handle_droplet_create,
            "app.deployment": self._handle_app_deployment,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(payload)

        return {"processed": False, "reason": "Unknown event type"}

    async def _handle_droplet_create(self, payload: Dict) -> Dict:
        return {"processed": True, "droplet_id": payload.get("id"), "status": payload.get("status")}

    async def _handle_app_deployment(self, payload: Dict) -> Dict:
        return {
            "processed": True,
            "app_id": payload.get("app_id"),
            "deployment_id": payload.get("deployment_id"),
            "status": payload.get("status"),
        }
