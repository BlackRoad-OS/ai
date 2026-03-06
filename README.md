# BlackRoad AI - Kanban Project System

[![CI](https://github.com/BlackRoad-OS/ai/actions/workflows/ci.yml/badge.svg)](https://github.com/BlackRoad-OS/ai/actions/workflows/ci.yml)

Artificial intelligence models, agents, and intelligence layers for the BlackRoad system.

Salesforce-style project management with multi-service synchronization, SHA-256/SHA-infinity hashing, and comprehensive API integrations.

## Features

- **Kanban Board System**: Full-featured board/column/card management
- **Multi-Service Sync**: Cloudflare, Salesforce, Vercel, DigitalOcean, GitHub
- **AI Integration**: Claude API for intelligent task management
- **Mobile Support**: Termius, iSH, Shellfish, Working Copy, Pyto
- **Integrity Hashing**: SHA-256 and SHA-infinity for state verification
- **Agent System**: Task tracking and instructions for AI agents

## Quick Start

```bash
# Initialize the system
python scripts/init.py

# Or quick setup with defaults
python scripts/init.py --quick

# Verify setup
python scripts/init.py --verify
```

## Project Structure

```
ai/
├── kanban/              # Core kanban system
│   ├── board.py         # Board, Column, Card classes
│   └── endpoints.py     # API endpoint definitions
├── integrations/        # Service integrations
│   ├── cloudflare/      # Cloudflare Workers/KV/D1
│   ├── salesforce/      # Salesforce CRM
│   ├── vercel/          # Vercel serverless
│   ├── digitalocean/    # DigitalOcean
│   ├── claude/          # Anthropic Claude API
│   ├── github/          # GitHub Issues/Projects
│   └── mobile/          # Mobile app integrations
├── utils/               # Utilities
│   └── hashing.py       # SHA-256 and SHA-infinity
├── agents/              # Agent management
│   ├── instructions.md  # Instructions for AI agents
│   └── todos.py         # Task tracking system
├── config/              # Configuration
│   ├── settings.py      # Settings management
│   └── .env.example     # Environment template
└── scripts/             # Scripts
    └── init.py          # Initialization script
```

## Configuration

1. Copy the environment template:
```bash
cp config/.env.example .env
```

2. Edit `.env` with your API credentials:
```bash
# Required for each service you want to use
CLOUDFLARE_API_KEY=your_key
SALESFORCE_CLIENT_ID=your_id
ANTHROPIC_API_KEY=your_key
GITHUB_TOKEN=your_token
```

## API Endpoints

### Board Operations
- `GET /api/v1/boards` - List all boards
- `POST /api/v1/boards` - Create board
- `GET /api/v1/boards/{id}` - Get board
- `PUT /api/v1/boards/{id}` - Update board
- `DELETE /api/v1/boards/{id}` - Delete board

### Card Operations
- `GET /api/v1/boards/{id}/cards` - List cards
- `POST /api/v1/boards/{id}/cards` - Create card
- `PATCH /api/v1/boards/{id}/cards/{card_id}` - Update card
- `POST /api/v1/boards/{id}/cards/{card_id}/move` - Move card

### Sync Operations
- `POST /api/v1/sync/cloudflare` - Sync with Cloudflare
- `POST /api/v1/sync/salesforce` - Sync with Salesforce
- `POST /api/v1/sync/github` - Sync with GitHub
- `POST /api/v1/sync/all` - Sync with all services

### Webhooks
- `POST /api/v1/webhooks/{service}` - Receive webhooks

## Hashing

### SHA-256
Standard cryptographic hash for content verification:
```python
from utils.hashing import sha256_hash
hash = sha256_hash("content")
```

### SHA-infinity
Recursive chain hashing for enhanced verification:
```python
from utils.hashing import sha_infinity_hash
hash = sha_infinity_hash("content", depth=7)
# Returns: sha∞:7:<hash>
```

### Integrity Proofs
```python
from utils.hashing import create_integrity_proof, verify_integrity_proof

proof = create_integrity_proof(data)
result = verify_integrity_proof(data, proof)
```

## Agent Instructions

AI agents working with this system should follow the guidelines in `agents/instructions.md`:

1. Always verify before committing
2. Update hashes after modifications
3. Sync state before and after changes
4. Use checkpoint commits for long tasks
5. Follow the PR checklist

## Mobile Integration

### Working Copy (iOS Git)
```python
from integrations.mobile.clients import WorkingCopyIntegration
wc = WorkingCopyIntegration(config)
urls = wc.generate_board_sync_urls(board, repo)
```

### iSH / Shellfish
```python
from integrations.mobile.clients import ISHIntegration
ish = ISHIntegration()
scripts = ish.generate_kanban_scripts(board)
```

### Pyto (iOS Python)
```python
from integrations.mobile.clients import PytoIntegration
pyto = PytoIntegration()
module = pyto.generate_kanban_module()
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Format code
black .

# Lint
flake8 .
```

## License

MIT License - BlackRoad Systems
