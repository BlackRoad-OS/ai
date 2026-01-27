"""
Kanban Board System for BlackRoad AI
=====================================
Salesforce-style project management with state sync across CRM, Cloudflare, and Git.

This module provides:
- Board/Column/Card management
- State synchronization with external services
- SHA-256 and SHA-infinity hashing for integrity
- Webhook endpoints for all configured services
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class CardStatus(Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    ARCHIVED = "archived"


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    NONE = 5


@dataclass
class KanbanCard:
    """Individual card/task in the kanban board."""
    id: str
    title: str
    description: str = ""
    status: CardStatus = CardStatus.BACKLOG
    priority: Priority = Priority.MEDIUM
    assignee: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    due_date: Optional[str] = None
    sha256_hash: str = ""
    sha_infinity_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Integration references
    salesforce_id: Optional[str] = None
    cloudflare_kv_key: Optional[str] = None
    github_issue_number: Optional[int] = None

    def __post_init__(self):
        self.update_hashes()

    def update_hashes(self):
        """Update SHA-256 and SHA-infinity hashes."""
        from utils.hashing import sha256_hash, sha_infinity_hash
        content = f"{self.id}:{self.title}:{self.description}:{self.status.value}"
        self.sha256_hash = sha256_hash(content)
        self.sha_infinity_hash = sha_infinity_hash(content)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'KanbanCard':
        data['status'] = CardStatus(data['status'])
        data['priority'] = Priority(data['priority'])
        return cls(**data)


@dataclass
class KanbanColumn:
    """Column in the kanban board."""
    id: str
    name: str
    status: CardStatus
    cards: List[KanbanCard] = field(default_factory=list)
    wip_limit: Optional[int] = None  # Work in progress limit

    def add_card(self, card: KanbanCard):
        if self.wip_limit and len(self.cards) >= self.wip_limit:
            raise ValueError(f"WIP limit ({self.wip_limit}) reached for column {self.name}")
        card.status = self.status
        card.update_hashes()
        self.cards.append(card)

    def remove_card(self, card_id: str) -> Optional[KanbanCard]:
        for i, card in enumerate(self.cards):
            if card.id == card_id:
                return self.cards.pop(i)
        return None


@dataclass
class KanbanBoard:
    """Main kanban board with Salesforce-style project management."""
    id: str
    name: str
    description: str = ""
    columns: List[KanbanColumn] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Sync state tracking
    last_sync: Dict[str, str] = field(default_factory=dict)  # service -> timestamp
    sync_enabled: Dict[str, bool] = field(default_factory=dict)

    def __post_init__(self):
        if not self.columns:
            self._create_default_columns()

    def _create_default_columns(self):
        """Create Salesforce-style default columns."""
        self.columns = [
            KanbanColumn(id="col-backlog", name="Backlog", status=CardStatus.BACKLOG),
            KanbanColumn(id="col-todo", name="To Do", status=CardStatus.TODO, wip_limit=10),
            KanbanColumn(id="col-progress", name="In Progress", status=CardStatus.IN_PROGRESS, wip_limit=5),
            KanbanColumn(id="col-review", name="Review", status=CardStatus.REVIEW, wip_limit=3),
            KanbanColumn(id="col-testing", name="Testing", status=CardStatus.TESTING, wip_limit=3),
            KanbanColumn(id="col-done", name="Done", status=CardStatus.DONE),
        ]

    def get_column(self, status: CardStatus) -> Optional[KanbanColumn]:
        for col in self.columns:
            if col.status == status:
                return col
        return None

    def move_card(self, card_id: str, to_status: CardStatus) -> bool:
        """Move a card between columns."""
        card = None
        for col in self.columns:
            card = col.remove_card(card_id)
            if card:
                break

        if not card:
            return False

        target_col = self.get_column(to_status)
        if target_col:
            target_col.add_card(card)
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def get_all_cards(self) -> List[KanbanCard]:
        """Get all cards across all columns."""
        cards = []
        for col in self.columns:
            cards.extend(col.cards)
        return cards

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'columns': [
                {
                    'id': col.id,
                    'name': col.name,
                    'status': col.status.value,
                    'wip_limit': col.wip_limit,
                    'cards': [card.to_dict() for card in col.cards]
                }
                for col in self.columns
            ],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_sync': self.last_sync,
            'sync_enabled': self.sync_enabled
        }

    def save(self, filepath: str):
        """Save board state to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'KanbanBoard':
        """Load board state from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        board = cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            last_sync=data.get('last_sync', {}),
            sync_enabled=data.get('sync_enabled', {})
        )

        board.columns = []
        for col_data in data['columns']:
            col = KanbanColumn(
                id=col_data['id'],
                name=col_data['name'],
                status=CardStatus(col_data['status']),
                wip_limit=col_data.get('wip_limit')
            )
            for card_data in col_data.get('cards', []):
                col.cards.append(KanbanCard.from_dict(card_data))
            board.columns.append(col)

        return board


class BoardManager:
    """Manages multiple kanban boards with sync capabilities."""

    def __init__(self, storage_path: str = "./data/boards"):
        self.storage_path = storage_path
        self.boards: Dict[str, KanbanBoard] = {}
        self._integrations = {}

    def register_integration(self, name: str, integration):
        """Register an API integration for syncing."""
        self._integrations[name] = integration

    def create_board(self, name: str, description: str = "") -> KanbanBoard:
        """Create a new kanban board."""
        import uuid
        board_id = f"board-{uuid.uuid4().hex[:8]}"
        board = KanbanBoard(id=board_id, name=name, description=description)
        self.boards[board_id] = board
        return board

    def get_board(self, board_id: str) -> Optional[KanbanBoard]:
        return self.boards.get(board_id)

    async def sync_board(self, board_id: str, services: List[str] = None):
        """Sync board state with configured services."""
        board = self.get_board(board_id)
        if not board:
            raise ValueError(f"Board {board_id} not found")

        services = services or list(self._integrations.keys())

        for service in services:
            if service in self._integrations:
                integration = self._integrations[service]
                await integration.sync(board)
                board.last_sync[service] = datetime.utcnow().isoformat()
