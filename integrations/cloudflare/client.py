"""
Cloudflare Integration
======================
Integration with Cloudflare Workers, KV, D1, and R2.

Features:
- KV store for kanban state
- Workers for serverless endpoints
- D1 for relational data
- R2 for file storage
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import sys

sys.path.insert(0, "/home/user/ai")

from integrations.base import BaseIntegration, IntegrationConfig, IntegrationError


@dataclass
class CloudflareConfig(IntegrationConfig):
    """Cloudflare-specific configuration."""

    account_id: str = ""
    kv_namespace_id: str = ""
    d1_database_id: str = ""
    r2_bucket: str = ""


class CloudflareIntegration(BaseIntegration):
    """
    Cloudflare integration for state management.

    KV is used as the primary state store with:
    - Board states synced to KV
    - Real-time worker endpoints
    - Edge caching for performance
    """

    def __init__(self, config: CloudflareConfig):
        super().__init__(config)
        self.cf_config = config
        self._state_cache = {}

    def _get_kv_base(self) -> str:
        """Get KV namespace base URL."""
        return f"/accounts/{self.cf_config.account_id}/storage/kv/namespaces/{self.cf_config.kv_namespace_id}"

    async def health_check(self) -> bool:
        """Check Cloudflare API connectivity."""
        try:
            result = await self.request("GET", "/user")
            return result.get("success", False)
        except Exception:
            return False

    async def sync(self, board) -> Dict:
        """Sync kanban board to Cloudflare KV."""
        results = {"kv": [], "success": True}

        try:
            # Store board metadata
            await self.kv_put(
                f"board:{board.id}:meta",
                json.dumps({"id": board.id, "name": board.name, "updated_at": board.updated_at}),
            )

            # Store each card
            for card in board.get_all_cards():
                await self.kv_put(f"board:{board.id}:card:{card.id}", json.dumps(card.to_dict()))
                results["kv"].append(card.id)

            # Update state cache
            self._state_cache[board.id] = board.to_dict()

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    def get_state_hash(self) -> str:
        """Get hash of Cloudflare state."""
        from utils.hashing import sha256_hash

        return sha256_hash(self._state_cache)

    # KV Operations
    async def kv_get(self, key: str) -> Optional[str]:
        """Get value from KV store."""
        try:
            result = await self.request("GET", f"{self._get_kv_base()}/values/{key}")
            return result
        except IntegrationError as e:
            if e.status == 404:
                return None
            raise

    async def kv_put(self, key: str, value: str, metadata: Dict = None) -> bool:
        """Put value to KV store."""
        data = {"value": value}
        if metadata:
            data["metadata"] = metadata

        result = await self.request("PUT", f"{self._get_kv_base()}/values/{key}", data=data)
        return result.get("success", False)

    async def kv_delete(self, key: str) -> bool:
        """Delete value from KV store."""
        result = await self.request("DELETE", f"{self._get_kv_base()}/values/{key}")
        return result.get("success", False)

    async def kv_list(self, prefix: str = None) -> List[str]:
        """List keys in KV store."""
        params = {}
        if prefix:
            params["prefix"] = prefix

        result = await self.request("GET", f"{self._get_kv_base()}/keys", params=params)
        return [key["name"] for key in result.get("result", [])]

    # D1 Operations
    async def d1_query(self, sql: str, params: List = None) -> List[Dict]:
        """Execute D1 SQL query."""
        d1_base = f"/accounts/{self.cf_config.account_id}/d1/database/{self.cf_config.d1_database_id}"

        result = await self.request("POST", f"{d1_base}/query", data={"sql": sql, "params": params or []})
        return result.get("result", [])

    # Worker Operations
    async def deploy_worker(self, script_name: str, script_content: str) -> Dict:
        """Deploy a Cloudflare Worker script."""
        workers_base = f"/accounts/{self.cf_config.account_id}/workers/scripts/{script_name}"

        result = await self.request("PUT", workers_base, data={"script": script_content})
        return result

    async def get_worker_routes(self) -> List[Dict]:
        """Get worker routes."""
        result = await self.request("GET", f"/accounts/{self.cf_config.account_id}/workers/routes")
        return result.get("result", [])


class CloudflareWebhookHandler:
    """Handle Cloudflare webhook events."""

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Cloudflare webhook signature."""
        # Cloudflare uses different verification per service
        # This is a placeholder for actual implementation
        return True

    async def process(self, event_type: str, payload: Dict) -> Dict:
        """Process Cloudflare webhook event."""
        handlers = {
            "workers.deployment": self._handle_deployment,
            "kv.update": self._handle_kv_update,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(payload)

        return {"processed": False, "reason": "Unknown event type"}

    async def _handle_deployment(self, payload: Dict) -> Dict:
        """Handle worker deployment event."""
        return {"processed": True, "script": payload.get("script_name"), "status": payload.get("status")}

    async def _handle_kv_update(self, payload: Dict) -> Dict:
        """Handle KV update event."""
        return {"processed": True, "key": payload.get("key"), "action": payload.get("action")}
