"""
Kanban API Endpoints
====================
RESTful endpoints for kanban board operations with webhook support
for all configured services.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import asyncio


class EndpointMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class Endpoint:
    """API endpoint definition."""
    path: str
    method: EndpointMethod
    handler: str
    description: str
    auth_required: bool = True
    rate_limit: int = 100  # requests per minute


class KanbanEndpoints:
    """
    Kanban API endpoint definitions for all services.

    Services supported:
    - Cloudflare Workers/KV/D1
    - Salesforce (REST/Bulk/Streaming)
    - Vercel Serverless
    - DigitalOcean Functions/Spaces
    - Claude API (Anthropic)
    - GitHub (Issues/Projects/Actions)
    - Termius (SSH automation)
    - Mobile: iSH, Shellfish, Working Copy, Pyto
    """

    # Base endpoints for board operations
    BOARD_ENDPOINTS = [
        Endpoint("/api/v1/boards", EndpointMethod.GET, "list_boards", "List all boards"),
        Endpoint("/api/v1/boards", EndpointMethod.POST, "create_board", "Create new board"),
        Endpoint("/api/v1/boards/{board_id}", EndpointMethod.GET, "get_board", "Get board details"),
        Endpoint("/api/v1/boards/{board_id}", EndpointMethod.PUT, "update_board", "Update board"),
        Endpoint("/api/v1/boards/{board_id}", EndpointMethod.DELETE, "delete_board", "Delete board"),
    ]

    # Card endpoints
    CARD_ENDPOINTS = [
        Endpoint("/api/v1/boards/{board_id}/cards", EndpointMethod.GET, "list_cards", "List all cards"),
        Endpoint("/api/v1/boards/{board_id}/cards", EndpointMethod.POST, "create_card", "Create new card"),
        Endpoint("/api/v1/boards/{board_id}/cards/{card_id}", EndpointMethod.GET, "get_card", "Get card"),
        Endpoint("/api/v1/boards/{board_id}/cards/{card_id}", EndpointMethod.PATCH, "update_card", "Update card"),
        Endpoint("/api/v1/boards/{board_id}/cards/{card_id}", EndpointMethod.DELETE, "delete_card", "Delete card"),
        Endpoint("/api/v1/boards/{board_id}/cards/{card_id}/move", EndpointMethod.POST, "move_card", "Move card"),
    ]

    # Sync endpoints
    SYNC_ENDPOINTS = [
        Endpoint("/api/v1/sync/cloudflare", EndpointMethod.POST, "sync_cloudflare", "Sync with Cloudflare"),
        Endpoint("/api/v1/sync/salesforce", EndpointMethod.POST, "sync_salesforce", "Sync with Salesforce"),
        Endpoint("/api/v1/sync/github", EndpointMethod.POST, "sync_github", "Sync with GitHub"),
        Endpoint("/api/v1/sync/vercel", EndpointMethod.POST, "sync_vercel", "Sync with Vercel"),
        Endpoint("/api/v1/sync/digitalocean", EndpointMethod.POST, "sync_digitalocean", "Sync with DigitalOcean"),
        Endpoint("/api/v1/sync/all", EndpointMethod.POST, "sync_all", "Sync with all services"),
    ]

    # Webhook endpoints (incoming)
    WEBHOOK_ENDPOINTS = [
        Endpoint("/api/v1/webhooks/cloudflare", EndpointMethod.POST, "webhook_cloudflare", "Cloudflare webhook", auth_required=False),
        Endpoint("/api/v1/webhooks/salesforce", EndpointMethod.POST, "webhook_salesforce", "Salesforce webhook", auth_required=False),
        Endpoint("/api/v1/webhooks/github", EndpointMethod.POST, "webhook_github", "GitHub webhook", auth_required=False),
        Endpoint("/api/v1/webhooks/vercel", EndpointMethod.POST, "webhook_vercel", "Vercel webhook", auth_required=False),
        Endpoint("/api/v1/webhooks/digitalocean", EndpointMethod.POST, "webhook_digitalocean", "DigitalOcean webhook", auth_required=False),
        Endpoint("/api/v1/webhooks/claude", EndpointMethod.POST, "webhook_claude", "Claude API callback", auth_required=False),
    ]

    # Agent endpoints
    AGENT_ENDPOINTS = [
        Endpoint("/api/v1/agents/tasks", EndpointMethod.GET, "list_agent_tasks", "List agent tasks"),
        Endpoint("/api/v1/agents/tasks", EndpointMethod.POST, "create_agent_task", "Create agent task"),
        Endpoint("/api/v1/agents/tasks/{task_id}/status", EndpointMethod.PATCH, "update_task_status", "Update task status"),
        Endpoint("/api/v1/agents/instructions", EndpointMethod.GET, "get_instructions", "Get agent instructions"),
    ]

    # Hash verification endpoints
    HASH_ENDPOINTS = [
        Endpoint("/api/v1/hash/sha256", EndpointMethod.POST, "compute_sha256", "Compute SHA-256 hash"),
        Endpoint("/api/v1/hash/sha-infinity", EndpointMethod.POST, "compute_sha_infinity", "Compute SHA-infinity hash"),
        Endpoint("/api/v1/hash/verify", EndpointMethod.POST, "verify_hash", "Verify content hash"),
    ]

    @classmethod
    def get_all_endpoints(cls) -> List[Endpoint]:
        """Get all defined endpoints."""
        return (
            cls.BOARD_ENDPOINTS +
            cls.CARD_ENDPOINTS +
            cls.SYNC_ENDPOINTS +
            cls.WEBHOOK_ENDPOINTS +
            cls.AGENT_ENDPOINTS +
            cls.HASH_ENDPOINTS
        )

    @classmethod
    def get_openapi_spec(cls) -> Dict:
        """Generate OpenAPI specification."""
        paths = {}
        for endpoint in cls.get_all_endpoints():
            if endpoint.path not in paths:
                paths[endpoint.path] = {}

            paths[endpoint.path][endpoint.method.value.lower()] = {
                "summary": endpoint.description,
                "operationId": endpoint.handler,
                "security": [{"bearerAuth": []}] if endpoint.auth_required else [],
                "responses": {
                    "200": {"description": "Success"},
                    "400": {"description": "Bad Request"},
                    "401": {"description": "Unauthorized"},
                    "500": {"description": "Server Error"}
                }
            }

        return {
            "openapi": "3.0.0",
            "info": {
                "title": "BlackRoad Kanban API",
                "version": "1.0.0",
                "description": "Kanban board API with multi-service sync"
            },
            "servers": [
                {"url": "https://api.blackroad.ai", "description": "Production"},
                {"url": "http://localhost:8000", "description": "Development"}
            ],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer"
                    }
                }
            }
        }


class EndpointRouter:
    """Route requests to appropriate handlers."""

    def __init__(self):
        self.routes: Dict[str, Dict[str, callable]] = {}
        self.middleware: List[callable] = []

    def register(self, path: str, method: str, handler: callable):
        """Register a route handler."""
        if path not in self.routes:
            self.routes[path] = {}
        self.routes[path][method.upper()] = handler

    def add_middleware(self, middleware: callable):
        """Add middleware function."""
        self.middleware.append(middleware)

    async def handle(self, path: str, method: str, request: Dict) -> Dict:
        """Handle an incoming request."""
        # Apply middleware
        for mw in self.middleware:
            request = await mw(request)
            if request.get('_abort'):
                return request.get('_response', {'error': 'Request aborted'})

        # Find matching route
        handler = self._find_handler(path, method)
        if not handler:
            return {'error': 'Not found', 'status': 404}

        try:
            return await handler(request)
        except Exception as e:
            return {'error': str(e), 'status': 500}

    def _find_handler(self, path: str, method: str) -> Optional[callable]:
        """Find handler for path (supports path parameters)."""
        # Direct match
        if path in self.routes and method in self.routes[path]:
            return self.routes[path][method]

        # Pattern match with path parameters
        for route_path, methods in self.routes.items():
            if self._match_path(route_path, path):
                if method in methods:
                    return methods[method]

        return None

    def _match_path(self, pattern: str, path: str) -> bool:
        """Check if path matches pattern with parameters."""
        pattern_parts = pattern.split('/')
        path_parts = path.split('/')

        if len(pattern_parts) != len(path_parts):
            return False

        for p, pp in zip(pattern_parts, path_parts):
            if p.startswith('{') and p.endswith('}'):
                continue  # Parameter placeholder
            if p != pp:
                return False

        return True


# Service-specific endpoint configurations
SERVICE_ENDPOINTS = {
    "cloudflare": {
        "base_url": "https://api.cloudflare.com/client/v4",
        "kv_namespace": "/accounts/{account_id}/storage/kv/namespaces/{namespace_id}",
        "workers": "/accounts/{account_id}/workers/scripts/{script_name}",
        "d1": "/accounts/{account_id}/d1/database/{database_id}"
    },
    "salesforce": {
        "base_url": "https://{instance}.salesforce.com",
        "rest": "/services/data/v{version}",
        "sobjects": "/services/data/v{version}/sobjects",
        "query": "/services/data/v{version}/query",
        "composite": "/services/data/v{version}/composite"
    },
    "vercel": {
        "base_url": "https://api.vercel.com",
        "deployments": "/v13/deployments",
        "projects": "/v9/projects",
        "env": "/v10/projects/{project_id}/env"
    },
    "digitalocean": {
        "base_url": "https://api.digitalocean.com/v2",
        "droplets": "/droplets",
        "functions": "/functions/namespaces/{namespace_id}/functions",
        "spaces": "https://{region}.digitaloceanspaces.com"
    },
    "claude": {
        "base_url": "https://api.anthropic.com",
        "messages": "/v1/messages",
        "completions": "/v1/complete"
    },
    "github": {
        "base_url": "https://api.github.com",
        "repos": "/repos/{owner}/{repo}",
        "issues": "/repos/{owner}/{repo}/issues",
        "projects": "/repos/{owner}/{repo}/projects",
        "actions": "/repos/{owner}/{repo}/actions"
    }
}
