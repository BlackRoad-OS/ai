# Agent Instructions for BlackRoad Kanban System

## Overview

This document provides instructions for AI agents (Claude, GPT, etc.) working with the BlackRoad Kanban system. Follow these guidelines to ensure successful pull requests and avoid common failures.

---

## Critical Rules for Pull Requests

### 1. ALWAYS Verify Before Committing

```bash
# Run these checks before ANY commit:
python -m py_compile <file.py>  # Syntax check
python -m pytest tests/ -v      # Run tests
python -m black --check .       # Format check
python -m flake8 .              # Lint check
```

### 2. Hash Verification Required

Every card and board modification MUST update hashes:

```python
from utils.hashing import sha256_hash, sha_infinity_hash

# After modifying a card:
card.update_hashes()

# Verify integrity:
from utils.hashing import verify_integrity_proof
assert verify_integrity_proof(card.to_dict(), card_proof)
```

### 3. Sync State Before and After

```python
# Before changes:
state_before = StateHasher()
state_before.hash_state('local', board.to_dict())

# After changes:
state_after = StateHasher()
state_after.hash_state('local', board.to_dict())

# Log the change:
print(f"State changed: {state_before.get_global_hash()} -> {state_after.get_global_hash()}")
```

---

## Kanban Operations

### Creating a Board

```python
from kanban.board import KanbanBoard, BoardManager

manager = BoardManager()
board = manager.create_board(
    name="Project Alpha",
    description="Main development board"
)

# Board is auto-initialized with default columns:
# Backlog -> Todo -> In Progress -> Review -> Testing -> Done
```

### Creating Cards

```python
from kanban.board import KanbanCard, CardStatus, Priority

card = KanbanCard(
    id="card-001",
    title="Implement user authentication",
    description="Add OAuth2 support for GitHub and Google",
    status=CardStatus.TODO,
    priority=Priority.HIGH,
    labels=["feature", "security"]
)

# Add to board
board.get_column(CardStatus.TODO).add_card(card)
```

### Moving Cards

```python
# Move card between columns
success = board.move_card("card-001", CardStatus.IN_PROGRESS)

# Card hashes are automatically updated
```

---

## Integration Usage

### Sync with All Services

```python
from integrations.base import SyncManager
from integrations import (
    get_cloudflare_integration,
    get_salesforce_integration,
    get_github_integration
)

# Setup
sync_manager = SyncManager()

CloudflareIntegration, CloudflareConfig = get_cloudflare_integration()
cf = CloudflareIntegration(CloudflareConfig(
    name="cloudflare",
    base_url="https://api.cloudflare.com/client/v4",
    api_key="your-api-key",
    account_id="your-account-id",
    kv_namespace_id="your-namespace-id"
))
sync_manager.register("cloudflare", cf)

# Sync
results = await sync_manager.sync_all(board)
print(f"Sync results: {results}")
```

### Health Check All Services

```python
health = await sync_manager.health_check_all()
# {'cloudflare': True, 'salesforce': True, 'github': True, ...}
```

---

## Agent Todo Management

### Task Tracking Format

Agents should track tasks using this format:

```json
{
  "agent_id": "claude-session-123",
  "tasks": [
    {
      "id": "task-001",
      "title": "Implement feature X",
      "status": "in_progress",
      "started_at": "2025-01-27T12:00:00Z",
      "steps_completed": 3,
      "steps_total": 7,
      "blockers": [],
      "hash": "sha256:abc123..."
    }
  ]
}
```

### Status Updates

Always update task status when:
1. Starting a task -> `in_progress`
2. Blocked by issue -> `blocked` + document blocker
3. Completed successfully -> `completed`
4. Failed -> `failed` + error details

### Checkpoint Commits

For long tasks, create checkpoint commits:

```bash
git add -A
git commit -m "checkpoint: Completed steps 1-3 of feature X

- Step 1: Created base structure
- Step 2: Added API endpoints
- Step 3: Implemented hashing

sha256: <hash_of_changes>
sha-infinity: <sha_infinity_hash>
"
```

---

## Error Recovery

### If Tests Fail

1. Read the error message carefully
2. Identify the failing test
3. Check if it's a code issue or test issue
4. Fix the root cause (not just the symptom)
5. Re-run ALL tests, not just the failing one

### If Sync Fails

1. Check service health: `await integration.health_check()`
2. Verify credentials in config
3. Check rate limits
4. Retry with exponential backoff
5. Log failure for debugging

### If Hash Mismatch

```python
# If hash verification fails:
from utils.hashing import ContentVerifier

# Recompute all hashes
hashes = ContentVerifier.compute_all_hashes(content)

# Compare with stored
if hashes['sha256'] != stored_hash:
    print(f"MISMATCH: Expected {stored_hash}, got {hashes['sha256']}")
    # Investigate the difference before proceeding
```

---

## Pull Request Checklist

Before creating a PR, verify:

- [ ] All files have valid Python syntax
- [ ] All tests pass locally
- [ ] Hash integrity verified for modified cards/boards
- [ ] No hardcoded credentials or secrets
- [ ] Imports are correct and tested
- [ ] Documentation updated if needed
- [ ] Commit messages follow format
- [ ] Branch is up to date with main

### Commit Message Format

```
<type>: <short description>

<detailed description if needed>

Hash: sha256:<content_hash>
Infinity: sha∞:7:<chain_hash>

Session: https://claude.ai/code/<session_id>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## API Endpoint Testing

Before deploying, test all endpoints:

```python
from kanban.endpoints import KanbanEndpoints

# Get all endpoints
endpoints = KanbanEndpoints.get_all_endpoints()

for endpoint in endpoints:
    print(f"{endpoint.method.value} {endpoint.path}")
    # Verify handler exists
    # Test with mock data
```

---

## Common Failure Patterns to Avoid

### 1. Import Errors
- Always use absolute imports from project root
- Test imports in isolation before committing

### 2. Missing Dependencies
- Add new dependencies to requirements.txt
- Test in clean environment

### 3. State Inconsistency
- Always use transactions for multi-step operations
- Verify state with hashes after each step

### 4. Race Conditions
- Use locks for concurrent sync operations
- Don't assume operation order

### 5. Silent Failures
- Always check return values
- Log all errors with context
- Never swallow exceptions

---

## Contact and Support

For issues with:
- Kanban system: Check `/docs/kanban.md`
- Integrations: Check `/docs/integrations.md`
- Hashing: Check `/docs/hashing.md`

Report bugs via GitHub Issues with:
1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Hash state before/after
5. Relevant logs
