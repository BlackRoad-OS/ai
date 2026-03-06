"""Tests for the kanban board module."""

import pytest
from kanban.board import KanbanBoard, KanbanCard, KanbanColumn, CardStatus, Priority


def test_kanban_card_creation():
    """Test basic kanban card creation."""
    card = KanbanCard(id="card-1", title="Test Card")
    assert card.id == "card-1"
    assert card.title == "Test Card"
    assert card.status == CardStatus.BACKLOG
    assert card.priority == Priority.MEDIUM


def test_kanban_board_creation():
    """Test kanban board initialization."""
    board = KanbanBoard(id="board-1", name="Test Board")
    assert board.id == "board-1"
    assert board.name == "Test Board"
    assert isinstance(board.columns, list)


def test_kanban_board_add_column():
    """Test adding a column to the board."""
    board = KanbanBoard(id="board-1", name="Test Board")
    initial_count = len(board.columns)
    column = KanbanColumn(id="col-custom", name="Custom", status=CardStatus.TODO)
    board.columns.append(column)
    assert len(board.columns) == initial_count + 1
    assert board.columns[-1].name == "Custom"


def test_kanban_card_status_transition():
    """Test card status can be changed."""
    card = KanbanCard(id="card-1", title="Test Card")
    card.status = CardStatus.IN_PROGRESS
    assert card.status == CardStatus.IN_PROGRESS


def test_card_priority_values():
    """Test priority enum values."""
    assert Priority.CRITICAL.value < Priority.LOW.value
    assert Priority.HIGH.value < Priority.MEDIUM.value
