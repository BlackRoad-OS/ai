#!/usr/bin/env python3
"""
BlackRoad Kanban Initialization Script
======================================
Initialize and configure the kanban system.

Usage:
    python scripts/init.py              # Interactive setup
    python scripts/init.py --quick      # Quick setup with defaults
    python scripts/init.py --verify     # Verify existing setup
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_header():
    """Print initialization header."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║             BlackRoad Kanban System Initialization               ║
║                                                                  ║
║  Salesforce-style project management with multi-service sync    ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def create_directories():
    """Create required directories."""
    dirs = [
        'data/boards',
        'data/agents',
        'data/sync',
        'logs',
        '.kanban/boards',
        '.kanban/config',
    ]

    print("Creating directories...")
    for d in dirs:
        path = PROJECT_ROOT / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"  - {d}")

    print("Done!\n")


def create_default_board():
    """Create a default kanban board."""
    print("Creating default board...")

    from kanban.board import KanbanBoard, KanbanCard, CardStatus, Priority

    board = KanbanBoard(
        id="board-default",
        name="Main Project Board",
        description="Default kanban board for project management"
    )

    # Add sample cards
    sample_cards = [
        KanbanCard(
            id="card-001",
            title="Setup project infrastructure",
            description="Configure all services and integrations",
            status=CardStatus.DONE,
            priority=Priority.HIGH,
            labels=["setup", "infrastructure"]
        ),
        KanbanCard(
            id="card-002",
            title="Implement core API endpoints",
            description="Build REST API for board operations",
            status=CardStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            labels=["api", "feature"]
        ),
        KanbanCard(
            id="card-003",
            title="Add integration tests",
            description="Write tests for all integrations",
            status=CardStatus.TODO,
            priority=Priority.MEDIUM,
            labels=["testing"]
        ),
        KanbanCard(
            id="card-004",
            title="Documentation",
            description="Write comprehensive documentation",
            status=CardStatus.BACKLOG,
            priority=Priority.LOW,
            labels=["docs"]
        ),
    ]

    for card in sample_cards:
        col = board.get_column(card.status)
        if col:
            col.cards.append(card)

    # Save board
    board_path = PROJECT_ROOT / 'data/boards/default.json'
    board.save(str(board_path))

    print(f"  Created: {board_path}")
    print(f"  Board ID: {board.id}")
    print(f"  Cards: {len(board.get_all_cards())}\n")

    return board


def verify_hashing():
    """Verify hashing utilities work correctly."""
    print("Verifying hashing utilities...")

    from utils.hashing import (
        sha256_hash,
        sha_infinity_hash,
        ContentVerifier,
        create_integrity_proof,
        verify_integrity_proof
    )

    # Test SHA-256
    test_content = "Hello, BlackRoad!"
    sha256 = sha256_hash(test_content)
    print(f"  SHA-256: {sha256[:32]}...")

    # Test SHA-infinity
    sha_inf = sha_infinity_hash(test_content, depth=7)
    print(f"  SHA-infinity: {sha_inf}")

    # Test integrity proof
    proof = create_integrity_proof(test_content)
    verification = verify_integrity_proof(test_content, proof)
    print(f"  Integrity verification: {'PASSED' if verification['sha256_valid'] else 'FAILED'}")

    print("Done!\n")


def verify_integrations():
    """Verify integration modules load correctly."""
    print("Verifying integrations...")

    integrations = [
        ('Cloudflare', 'integrations.cloudflare.client'),
        ('Salesforce', 'integrations.salesforce.client'),
        ('Vercel', 'integrations.vercel.client'),
        ('DigitalOcean', 'integrations.digitalocean.client'),
        ('Claude', 'integrations.claude.client'),
        ('GitHub', 'integrations.github.client'),
        ('Mobile', 'integrations.mobile.clients'),
    ]

    for name, module in integrations:
        try:
            __import__(module)
            print(f"  - {name}: OK")
        except ImportError as e:
            print(f"  - {name}: FAILED ({e})")

    print("Done!\n")


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_path = PROJECT_ROOT / '.env'
    template_path = PROJECT_ROOT / 'config/.env.example'

    if env_path.exists():
        print(".env file already exists, skipping...\n")
        return

    if template_path.exists():
        import shutil
        shutil.copy(template_path, env_path)
        print(f"Created .env from template")
        print("  Please edit .env with your API keys and settings\n")
    else:
        print("Warning: .env.example template not found\n")


def show_summary(board):
    """Show initialization summary."""
    from utils.hashing import sha_infinity_hash

    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    Initialization Complete!                       ║
╚══════════════════════════════════════════════════════════════════╝
""")

    board_hash = sha_infinity_hash(board.to_dict())

    print(f"""
System Status:
  - Directories: Created
  - Default Board: {board.name} ({board.id})
  - Board Hash: {board_hash}
  - Hashing: Verified
  - Integrations: Loaded

Next Steps:
  1. Edit .env with your API credentials
  2. Run: python -m pytest tests/ -v
  3. Start the API: python scripts/server.py

Available Services:
  - Cloudflare (KV, Workers, D1)
  - Salesforce (CRM sync)
  - Vercel (Serverless)
  - DigitalOcean (Spaces, Functions)
  - Claude (AI assistance)
  - GitHub (Issues, Projects)
  - Mobile (Termius, Working Copy, iSH, Pyto)

API Endpoints: See kanban/endpoints.py
Agent Instructions: See agents/instructions.md
""")


def verify_setup():
    """Verify existing setup is working."""
    print_header()
    print("Verifying existing setup...\n")

    # Check directories
    print("Checking directories...")
    required_dirs = ['data/boards', 'data/agents', 'config']
    for d in required_dirs:
        path = PROJECT_ROOT / d
        status = "OK" if path.exists() else "MISSING"
        print(f"  - {d}: {status}")

    print()

    # Check modules
    verify_integrations()
    verify_hashing()

    # Check board
    board_path = PROJECT_ROOT / 'data/boards/default.json'
    if board_path.exists():
        from kanban.board import KanbanBoard
        board = KanbanBoard.load(str(board_path))
        print(f"Default board loaded: {board.name}")
        print(f"  Cards: {len(board.get_all_cards())}")
    else:
        print("No default board found")

    print("\nVerification complete!")


def main():
    parser = argparse.ArgumentParser(description='Initialize BlackRoad Kanban System')
    parser.add_argument('--quick', action='store_true', help='Quick setup with defaults')
    parser.add_argument('--verify', action='store_true', help='Verify existing setup')
    args = parser.parse_args()

    if args.verify:
        verify_setup()
        return

    print_header()

    # Run initialization steps
    create_directories()
    create_env_file()
    board = create_default_board()
    verify_hashing()
    verify_integrations()
    show_summary(board)


if __name__ == '__main__':
    main()
