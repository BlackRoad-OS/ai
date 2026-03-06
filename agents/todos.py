"""
Agent Todo System
=================
Task management for AI agents working on the BlackRoad Kanban system.

Provides:
- Task tracking with state
- Progress monitoring
- Checkpoint management
- Failure recovery
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import uuid
import sys

sys.path.insert(0, '/home/user/ai')
from utils.hashing import sha256_hash, sha_infinity_hash, create_integrity_proof


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TaskStep:
    """Individual step within a task."""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None

    def start(self):
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow().isoformat()

    def complete(self, output: str = None):
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow().isoformat()
        self.output = output

    def fail(self, error: str):
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow().isoformat()
        self.error = error


@dataclass
class AgentTask:
    """Task for an AI agent to complete."""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    steps: List[TaskStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    blockers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict] = field(default_factory=list)
    hash: str = ""

    def __post_init__(self):
        self.update_hash()

    def update_hash(self):
        """Update task hash."""
        content = f"{self.id}:{self.title}:{self.status.value}"
        self.hash = sha256_hash(content)

    def start(self):
        """Start the task."""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow().isoformat()
        self.update_hash()

    def complete(self):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow().isoformat()
        self.update_hash()

    def fail(self, reason: str):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow().isoformat()
        self.blockers.append(f"FAILED: {reason}")
        self.update_hash()

    def block(self, blocker: str):
        """Mark task as blocked."""
        self.status = TaskStatus.BLOCKED
        self.blockers.append(blocker)
        self.update_hash()

    def unblock(self):
        """Remove blocked status."""
        if self.status == TaskStatus.BLOCKED:
            self.status = TaskStatus.IN_PROGRESS
            self.update_hash()

    def add_step(self, description: str) -> TaskStep:
        """Add a step to the task."""
        step = TaskStep(
            id=f"step-{len(self.steps)+1}",
            description=description
        )
        self.steps.append(step)
        return step

    def checkpoint(self, message: str, data: Dict = None):
        """Create a checkpoint."""
        checkpoint = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'steps_completed': sum(1 for s in self.steps if s.status == TaskStatus.COMPLETED),
            'steps_total': len(self.steps),
            'data': data or {},
            'hash': sha256_hash(f"{self.id}:{message}:{time.time()}")
        }
        self.checkpoints.append(checkpoint)
        return checkpoint

    @property
    def progress(self) -> float:
        """Get completion progress (0.0 - 1.0)."""
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == TaskStatus.COMPLETED)
        return completed / len(self.steps)

    @property
    def current_step(self) -> Optional[TaskStep]:
        """Get current in-progress step."""
        for step in self.steps:
            if step.status == TaskStatus.IN_PROGRESS:
                return step
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority.value,
            'steps': [asdict(s) for s in self.steps],
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'blockers': self.blockers,
            'metadata': self.metadata,
            'checkpoints': self.checkpoints,
            'hash': self.hash,
            'progress': self.progress
        }


@dataclass
class AgentSession:
    """Tracks an agent's work session."""
    id: str
    agent_type: str  # 'claude', 'gpt', 'custom'
    tasks: List[AgentTask] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> AgentTask:
        """Create and add a new task."""
        task = AgentTask(
            id=f"task-{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            priority=priority
        )
        self.tasks.append(task)
        return task

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Get task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_active_tasks(self) -> List[AgentTask]:
        """Get all in-progress tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.IN_PROGRESS]

    def get_blocked_tasks(self) -> List[AgentTask]:
        """Get all blocked tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.BLOCKED]

    def end_session(self):
        """End the session."""
        self.ended_at = datetime.utcnow().isoformat()

    def get_summary(self) -> Dict:
        """Get session summary."""
        return {
            'session_id': self.id,
            'agent_type': self.agent_type,
            'duration': self._calculate_duration(),
            'tasks': {
                'total': len(self.tasks),
                'completed': sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED),
                'failed': sum(1 for t in self.tasks if t.status == TaskStatus.FAILED),
                'blocked': sum(1 for t in self.tasks if t.status == TaskStatus.BLOCKED),
                'in_progress': sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)
            },
            'integrity_hash': sha_infinity_hash([t.to_dict() for t in self.tasks])
        }

    def _calculate_duration(self) -> Optional[float]:
        """Calculate session duration in seconds."""
        if not self.ended_at:
            return None
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.ended_at)
        return (end - start).total_seconds()


class TodoManager:
    """Manages agent todos and sessions."""

    def __init__(self, storage_path: str = "./data/agents"):
        self.storage_path = storage_path
        self.sessions: Dict[str, AgentSession] = {}
        self._current_session: Optional[str] = None

    def create_session(self, agent_type: str = "claude") -> AgentSession:
        """Create a new agent session."""
        session = AgentSession(
            id=f"session-{uuid.uuid4().hex[:8]}",
            agent_type=agent_type
        )
        self.sessions[session.id] = session
        self._current_session = session.id
        return session

    def get_current_session(self) -> Optional[AgentSession]:
        """Get current active session."""
        if self._current_session:
            return self.sessions.get(self._current_session)
        return None

    def add_todo(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> AgentTask:
        """Add a todo to current session."""
        session = self.get_current_session()
        if not session:
            session = self.create_session()
        return session.create_task(title, description, priority)

    def complete_todo(self, task_id: str) -> bool:
        """Mark a todo as complete."""
        session = self.get_current_session()
        if session:
            task = session.get_task(task_id)
            if task:
                task.complete()
                return True
        return False

    def save(self, filepath: str = None):
        """Save all sessions to file."""
        filepath = filepath or f"{self.storage_path}/sessions.json"
        data = {
            'sessions': {
                sid: {
                    'id': s.id,
                    'agent_type': s.agent_type,
                    'tasks': [t.to_dict() for t in s.tasks],
                    'started_at': s.started_at,
                    'ended_at': s.ended_at,
                    'context': s.context
                }
                for sid, s in self.sessions.items()
            },
            'current_session': self._current_session
        }
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'TodoManager':
        """Load sessions from file."""
        manager = cls()
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            # Reconstruct sessions
            manager._current_session = data.get('current_session')
            # Note: Full reconstruction would need more work
        except FileNotFoundError:
            pass
        return manager


# Convenience functions for quick task management
_manager: Optional[TodoManager] = None


def get_manager() -> TodoManager:
    """Get or create global todo manager."""
    global _manager
    if _manager is None:
        _manager = TodoManager()
    return _manager


def todo(title: str, description: str = "") -> AgentTask:
    """Quick add a todo."""
    return get_manager().add_todo(title, description)


def done(task_id: str) -> bool:
    """Quick complete a todo."""
    return get_manager().complete_todo(task_id)


def todos() -> List[AgentTask]:
    """Get all todos in current session."""
    session = get_manager().get_current_session()
    return session.tasks if session else []


def summary() -> Dict:
    """Get current session summary."""
    session = get_manager().get_current_session()
    return session.get_summary() if session else {}
