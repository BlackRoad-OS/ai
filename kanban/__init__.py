"""
BlackRoad Kanban System
=======================
Salesforce-style project management with multi-service sync.

Features:
- Kanban boards with customizable columns
- Card management with priority and labels
- SHA-256 and SHA-infinity hashing for integrity
- Multi-service sync (Cloudflare, Salesforce, Vercel, DO, GitHub)
- Agent task management
"""

from .board import (
    CardStatus,
    Priority,
    KanbanCard,
    KanbanColumn,
    KanbanBoard,
    BoardManager
)

from .endpoints import (
    EndpointMethod,
    Endpoint,
    KanbanEndpoints,
    EndpointRouter,
    SERVICE_ENDPOINTS
)

__all__ = [
    # Board classes
    'CardStatus',
    'Priority',
    'KanbanCard',
    'KanbanColumn',
    'KanbanBoard',
    'BoardManager',
    # Endpoint classes
    'EndpointMethod',
    'Endpoint',
    'KanbanEndpoints',
    'EndpointRouter',
    'SERVICE_ENDPOINTS'
]

__version__ = '1.0.0'
