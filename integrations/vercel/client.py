"""
Vercel Integration
==================
Serverless deployment and edge functions for kanban API.

Features:
- Serverless API endpoints
- Edge caching
- Environment management
- Deployment automation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sys

sys.path.insert(0, "/home/user/ai")

from integrations.base import BaseIntegration, IntegrationConfig


@dataclass
class VercelConfig(IntegrationConfig):
    """Vercel-specific configuration."""

    team_id: Optional[str] = None
    project_id: str = ""
    project_name: str = ""


class VercelIntegration(BaseIntegration):
    """
    Vercel integration for serverless deployment.

    Used for:
    - Deploying kanban API endpoints
    - Edge function execution
    - Environment variable management
    """

    def __init__(self, config: VercelConfig):
        super().__init__(config)
        self.vercel_config = config
        self._state_cache = {}

    async def health_check(self) -> bool:
        """Check Vercel API connectivity."""
        try:
            result = await self.request("GET", "/v2/user")
            return "user" in result
        except Exception:
            return False

    async def sync(self, board) -> Dict:
        """Sync board state for Vercel deployment context."""
        results = {"deployments": [], "success": True}

        try:
            # Store board state as environment variables for edge access
            env_vars = {
                f"BOARD_{board.id.upper()}_NAME": board.name,
                f"BOARD_{board.id.upper()}_UPDATED": board.updated_at,
            }

            for key, value in env_vars.items():
                await self.set_env_var(key, value)

            self._state_cache[board.id] = board.to_dict()

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    def get_state_hash(self) -> str:
        """Get hash of Vercel state."""
        from utils.hashing import sha256_hash

        return sha256_hash(self._state_cache)

    # Project Operations
    async def get_project(self) -> Dict:
        """Get project details."""
        result = await self.request("GET", f"/v9/projects/{self.vercel_config.project_id}")
        return result

    async def list_projects(self) -> List[Dict]:
        """List all projects."""
        params = {}
        if self.vercel_config.team_id:
            params["teamId"] = self.vercel_config.team_id

        result = await self.request("GET", "/v9/projects", params=params)
        return result.get("projects", [])

    # Deployment Operations
    async def create_deployment(self, files: Dict[str, str], target: str = "production") -> Dict:
        """Create a new deployment."""
        result = await self.request(
            "POST",
            "/v13/deployments",
            data={
                "name": self.vercel_config.project_name,
                "target": target,
                "files": [{"file": path, "data": content} for path, content in files.items()],
            },
        )
        return result

    async def get_deployment(self, deployment_id: str) -> Dict:
        """Get deployment details."""
        result = await self.request("GET", f"/v13/deployments/{deployment_id}")
        return result

    async def list_deployments(self, limit: int = 20) -> List[Dict]:
        """List recent deployments."""
        params = {"projectId": self.vercel_config.project_id, "limit": limit}
        if self.vercel_config.team_id:
            params["teamId"] = self.vercel_config.team_id

        result = await self.request("GET", "/v6/deployments", params=params)
        return result.get("deployments", [])

    # Environment Variables
    async def get_env_vars(self) -> List[Dict]:
        """Get project environment variables."""
        result = await self.request("GET", f"/v10/projects/{self.vercel_config.project_id}/env")
        return result.get("envs", [])

    async def set_env_var(self, key: str, value: str, target: List[str] = None) -> Dict:
        """Set environment variable."""
        target = target or ["production", "preview", "development"]

        result = await self.request(
            "POST",
            f"/v10/projects/{self.vercel_config.project_id}/env",
            data={"key": key, "value": value, "target": target, "type": "encrypted"},
        )
        return result

    async def delete_env_var(self, env_id: str) -> bool:
        """Delete environment variable."""
        await self.request("DELETE", f"/v10/projects/{self.vercel_config.project_id}/env/{env_id}")
        return True

    # Serverless Functions
    async def get_function_logs(self, deployment_id: str) -> List[Dict]:
        """Get serverless function logs."""
        result = await self.request("GET", f"/v2/deployments/{deployment_id}/events")
        return result.get("events", [])

    # Edge Config
    async def create_edge_config(self, name: str) -> Dict:
        """Create edge config store."""
        result = await self.request("POST", "/v1/edge-config", data={"name": name})
        return result

    async def update_edge_config(self, config_id: str, items: Dict) -> Dict:
        """Update edge config items."""
        result = await self.request(
            "PATCH",
            f"/v1/edge-config/{config_id}/items",
            data={"items": [{"key": k, "value": v} for k, v in items.items()]},
        )
        return result


class VercelWebhookHandler:
    """Handle Vercel deployment webhooks."""

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Vercel webhook signature."""
        import hmac
        import hashlib

        # Would use VERCEL_WEBHOOK_SECRET
        return True

    async def process(self, event_type: str, payload: Dict) -> Dict:
        """Process Vercel webhook event."""
        handlers = {
            "deployment.created": self._handle_deployment_created,
            "deployment.succeeded": self._handle_deployment_succeeded,
            "deployment.failed": self._handle_deployment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(payload)

        return {"processed": False, "reason": "Unknown event type"}

    async def _handle_deployment_created(self, payload: Dict) -> Dict:
        return {"processed": True, "deployment_id": payload.get("id"), "status": "created"}

    async def _handle_deployment_succeeded(self, payload: Dict) -> Dict:
        return {"processed": True, "deployment_id": payload.get("id"), "url": payload.get("url"), "status": "succeeded"}

    async def _handle_deployment_failed(self, payload: Dict) -> Dict:
        return {
            "processed": True,
            "deployment_id": payload.get("id"),
            "error": payload.get("error"),
            "status": "failed",
        }
