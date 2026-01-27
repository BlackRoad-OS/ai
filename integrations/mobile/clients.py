"""
Mobile App Integrations
=======================
Support for iOS/mobile development and management apps.

Supported Apps:
- Termius: SSH and server management
- iSH: Linux shell on iOS
- Shellfish: SFTP and SSH client
- Working Copy: Git client for iOS
- Pyto: Python IDE for iOS
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import sys
sys.path.insert(0, '/home/user/ai')

from integrations.base import BaseIntegration, IntegrationConfig


# =============================================================================
# Termius Integration
# =============================================================================

@dataclass
class TermiusConfig(IntegrationConfig):
    """Termius-specific configuration."""
    team_id: Optional[str] = None
    sync_enabled: bool = True


class TermiusIntegration(BaseIntegration):
    """
    Termius SSH management integration.

    Features:
    - Host synchronization
    - Snippet management
    - Key management
    - Team access control
    """

    def __init__(self, config: TermiusConfig):
        config.base_url = "https://api.termius.com"
        super().__init__(config)
        self.termius_config = config
        self._state_cache = {}

    async def health_check(self) -> bool:
        """Check Termius API connectivity."""
        try:
            result = await self.request("GET", "/v1/user")
            return 'id' in result
        except Exception:
            return False

    async def sync(self, board) -> Dict:
        """Sync board-related hosts and snippets."""
        results = {'hosts': [], 'snippets': [], 'success': True}

        try:
            # Store kanban-related snippets for quick commands
            snippets = self._generate_kanban_snippets(board)
            for snippet in snippets:
                await self.create_snippet(snippet)
                results['snippets'].append(snippet['label'])

            self._state_cache[board.id] = board.to_dict()

        except Exception as e:
            results['success'] = False
            results['error'] = str(e)

        return results

    def get_state_hash(self) -> str:
        from utils.hashing import sha256_hash
        return sha256_hash(self._state_cache)

    def _generate_kanban_snippets(self, board) -> List[Dict]:
        """Generate useful snippets from board data."""
        return [
            {
                'label': f'kanban-status-{board.id}',
                'snippet': f'echo "Board: {board.name} | Cards: {len(board.get_all_cards())}"'
            },
            {
                'label': f'kanban-sync-{board.id}',
                'snippet': f'curl -X POST https://api.blackroad.ai/sync/{board.id}'
            }
        ]

    # Host Management
    async def list_hosts(self) -> List[Dict]:
        """List all hosts."""
        result = await self.request("GET", "/v1/hosts")
        return result.get('hosts', [])

    async def create_host(
        self,
        label: str,
        address: str,
        port: int = 22,
        username: str = None
    ) -> Dict:
        """Create a new host entry."""
        result = await self.request(
            "POST",
            "/v1/hosts",
            data={
                'label': label,
                'address': address,
                'port': port,
                'username': username
            }
        )
        return result

    # Snippet Management
    async def list_snippets(self) -> List[Dict]:
        """List all snippets."""
        result = await self.request("GET", "/v1/snippets")
        return result.get('snippets', [])

    async def create_snippet(self, data: Dict) -> Dict:
        """Create a new snippet."""
        result = await self.request("POST", "/v1/snippets", data=data)
        return result


# =============================================================================
# Working Copy Integration
# =============================================================================

@dataclass
class WorkingCopyConfig(IntegrationConfig):
    """Working Copy configuration via x-callback-url."""
    url_scheme: str = "working-copy"
    key: str = ""  # URL callback key


class WorkingCopyIntegration:
    """
    Working Copy Git client integration.

    Uses x-callback-url scheme for iOS automation.
    Works with Shortcuts app for automation.
    """

    def __init__(self, config: WorkingCopyConfig):
        self.config = config
        self._state_cache = {}

    def get_state_hash(self) -> str:
        from utils.hashing import sha256_hash
        return sha256_hash(self._state_cache)

    def generate_clone_url(self, repo_url: str, name: str = None) -> str:
        """Generate URL to clone a repository."""
        url = f"{self.config.url_scheme}://clone?remote={repo_url}"
        if name:
            url += f"&name={name}"
        if self.config.key:
            url += f"&key={self.config.key}"
        return url

    def generate_pull_url(self, repo: str) -> str:
        """Generate URL to pull changes."""
        url = f"{self.config.url_scheme}://pull?repo={repo}"
        if self.config.key:
            url += f"&key={self.config.key}"
        return url

    def generate_push_url(self, repo: str) -> str:
        """Generate URL to push changes."""
        url = f"{self.config.url_scheme}://push?repo={repo}"
        if self.config.key:
            url += f"&key={self.config.key}"
        return url

    def generate_commit_url(
        self,
        repo: str,
        message: str,
        files: List[str] = None
    ) -> str:
        """Generate URL to commit changes."""
        import urllib.parse
        url = f"{self.config.url_scheme}://commit?repo={repo}"
        url += f"&message={urllib.parse.quote(message)}"
        if files:
            url += f"&files={','.join(files)}"
        if self.config.key:
            url += f"&key={self.config.key}"
        return url

    def generate_read_url(self, repo: str, path: str) -> str:
        """Generate URL to read file contents."""
        url = f"{self.config.url_scheme}://read?repo={repo}&path={path}"
        if self.config.key:
            url += f"&key={self.config.key}"
        return url

    def generate_write_url(
        self,
        repo: str,
        path: str,
        text: str
    ) -> str:
        """Generate URL to write file contents."""
        import urllib.parse
        url = f"{self.config.url_scheme}://write?repo={repo}&path={path}"
        url += f"&text={urllib.parse.quote(text)}"
        if self.config.key:
            url += f"&key={self.config.key}"
        return url

    def generate_board_sync_urls(self, board, repo: str) -> Dict[str, str]:
        """Generate all URLs needed to sync board to repo."""
        import json
        board_json = json.dumps(board.to_dict(), indent=2)

        return {
            'write_board': self.generate_write_url(
                repo,
                f".kanban/boards/{board.id}.json",
                board_json
            ),
            'commit': self.generate_commit_url(
                repo,
                f"Sync kanban board: {board.name}",
                [f".kanban/boards/{board.id}.json"]
            ),
            'push': self.generate_push_url(repo)
        }


# =============================================================================
# iSH / Shellfish Integration
# =============================================================================

class ShellEnvironment:
    """
    Base class for shell-based mobile environments.
    Works with iSH (Alpine Linux on iOS) and Shellfish.
    """

    def __init__(self, name: str):
        self.name = name
        self.scripts: Dict[str, str] = {}

    def generate_kanban_scripts(self, board) -> Dict[str, str]:
        """Generate shell scripts for kanban operations."""
        board_id = board.id

        scripts = {
            'status.sh': f'''#!/bin/sh
# Kanban Board Status Script
# Board: {board.name}

BOARD_ID="{board_id}"
API_URL="${{KANBAN_API_URL:-https://api.blackroad.ai}}"

echo "=== Kanban Board Status ==="
echo "Board: {board.name}"
echo "ID: $BOARD_ID"
echo ""

curl -s "$API_URL/api/v1/boards/$BOARD_ID" | jq '.'
''',

            'sync.sh': f'''#!/bin/sh
# Sync Kanban Board
# Board: {board.name}

BOARD_ID="{board_id}"
API_URL="${{KANBAN_API_URL:-https://api.blackroad.ai}}"

echo "Syncing board $BOARD_ID..."

curl -X POST "$API_URL/api/v1/sync/all" \\
    -H "Content-Type: application/json" \\
    -d '{{"board_id": "'$BOARD_ID'"}}'

echo "\\nSync complete!"
''',

            'add_card.sh': '''#!/bin/sh
# Add Card to Kanban Board

BOARD_ID="${1:-}"
TITLE="${2:-}"
DESCRIPTION="${3:-}"

if [ -z "$BOARD_ID" ] || [ -z "$TITLE" ]; then
    echo "Usage: $0 <board_id> <title> [description]"
    exit 1
fi

API_URL="${KANBAN_API_URL:-https://api.blackroad.ai}"

curl -X POST "$API_URL/api/v1/boards/$BOARD_ID/cards" \\
    -H "Content-Type: application/json" \\
    -d "{
        \\"title\\": \\"$TITLE\\",
        \\"description\\": \\"$DESCRIPTION\\"
    }"
''',

            'move_card.sh': '''#!/bin/sh
# Move Card Between Columns

BOARD_ID="${1:-}"
CARD_ID="${2:-}"
STATUS="${3:-}"

if [ -z "$BOARD_ID" ] || [ -z "$CARD_ID" ] || [ -z "$STATUS" ]; then
    echo "Usage: $0 <board_id> <card_id> <status>"
    echo "Status: backlog|todo|in_progress|review|testing|done"
    exit 1
fi

API_URL="${KANBAN_API_URL:-https://api.blackroad.ai}"

curl -X POST "$API_URL/api/v1/boards/$BOARD_ID/cards/$CARD_ID/move" \\
    -H "Content-Type: application/json" \\
    -d "{\\"status\\": \\"$STATUS\\"}"
'''
        }

        self.scripts = scripts
        return scripts

    def get_install_script(self) -> str:
        """Get script to install kanban tools in shell environment."""
        return '''#!/bin/sh
# Install Kanban CLI Tools

INSTALL_DIR="${HOME}/.kanban/bin"
mkdir -p "$INSTALL_DIR"

# Download scripts
SCRIPTS="status.sh sync.sh add_card.sh move_card.sh"

for script in $SCRIPTS; do
    curl -sL "https://raw.githubusercontent.com/blackroad/ai/main/scripts/$script" \\
        -o "$INSTALL_DIR/$script"
    chmod +x "$INSTALL_DIR/$script"
done

# Add to PATH
echo 'export PATH="$HOME/.kanban/bin:$PATH"' >> ~/.profile

echo "Kanban CLI tools installed!"
echo "Run: source ~/.profile"
'''


class ISHIntegration(ShellEnvironment):
    """iSH (iOS Alpine Linux) specific integration."""

    def __init__(self):
        super().__init__("iSH")

    def get_setup_script(self) -> str:
        """Get iSH-specific setup script."""
        return '''#!/bin/sh
# iSH Setup for Kanban

# Install dependencies
apk update
apk add curl jq git openssh

# Setup kanban directory
mkdir -p ~/.kanban/{boards,config,bin}

# Create config
cat > ~/.kanban/config/settings.json << 'EOF'
{
    "api_url": "https://api.blackroad.ai",
    "sync_interval": 300,
    "offline_mode": true
}
EOF

echo "iSH Kanban environment configured!"
'''


class ShellfishIntegration(ShellEnvironment):
    """Shellfish (iOS SSH/SFTP) specific integration."""

    def __init__(self):
        super().__init__("Shellfish")

    def generate_sftp_commands(self, board) -> List[str]:
        """Generate SFTP commands for board sync."""
        return [
            f"mkdir -p /kanban/boards",
            f"put board_{board.id}.json /kanban/boards/",
            f"chmod 644 /kanban/boards/board_{board.id}.json"
        ]


# =============================================================================
# Pyto Integration
# =============================================================================

@dataclass
class PytoConfig:
    """Pyto Python IDE configuration."""
    scripts_dir: str = "kanban_scripts"


class PytoIntegration:
    """
    Pyto (iOS Python IDE) integration.

    Provides Python scripts for kanban management on iOS.
    """

    def __init__(self, config: PytoConfig = None):
        self.config = config or PytoConfig()
        self._state_cache = {}

    def get_state_hash(self) -> str:
        from utils.hashing import sha256_hash
        return sha256_hash(self._state_cache)

    def generate_kanban_module(self) -> str:
        """Generate Python module for Pyto kanban operations."""
        return '''"""
Kanban Module for Pyto
======================
Manage kanban boards from your iOS device.
"""

import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional

API_URL = "https://api.blackroad.ai"


class KanbanClient:
    """Simple kanban client for Pyto."""

    def __init__(self, api_url: str = API_URL, api_key: str = None):
        self.api_url = api_url
        self.api_key = api_key

    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make API request."""
        url = f"{self.api_url}{endpoint}"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())

    def list_boards(self) -> List[dict]:
        """List all boards."""
        return self._request("GET", "/api/v1/boards")

    def get_board(self, board_id: str) -> dict:
        """Get board details."""
        return self._request("GET", f"/api/v1/boards/{board_id}")

    def create_card(self, board_id: str, title: str, description: str = "") -> dict:
        """Create a new card."""
        return self._request("POST", f"/api/v1/boards/{board_id}/cards", {
            "title": title,
            "description": description
        })

    def move_card(self, board_id: str, card_id: str, status: str) -> dict:
        """Move card to new status."""
        return self._request("POST", f"/api/v1/boards/{board_id}/cards/{card_id}/move", {
            "status": status
        })

    def sync_all(self, board_id: str) -> dict:
        """Sync board with all services."""
        return self._request("POST", "/api/v1/sync/all", {"board_id": board_id})


# Quick access functions
_client = None

def get_client(api_key: str = None) -> KanbanClient:
    """Get or create client instance."""
    global _client
    if _client is None or api_key:
        _client = KanbanClient(api_key=api_key)
    return _client

def boards() -> List[dict]:
    """List all boards."""
    return get_client().list_boards()

def board(board_id: str) -> dict:
    """Get board details."""
    return get_client().get_board(board_id)

def add_card(board_id: str, title: str, description: str = "") -> dict:
    """Add card to board."""
    return get_client().create_card(board_id, title, description)

def move(board_id: str, card_id: str, status: str) -> dict:
    """Move card to status."""
    return get_client().move_card(board_id, card_id, status)

def sync(board_id: str) -> dict:
    """Sync board."""
    return get_client().sync_all(board_id)


if __name__ == "__main__":
    # Interactive mode
    print("Kanban Module for Pyto")
    print("=" * 40)
    print("\\nAvailable functions:")
    print("  boards()              - List all boards")
    print("  board(id)             - Get board details")
    print("  add_card(bid, title)  - Add card to board")
    print("  move(bid, cid, stat)  - Move card")
    print("  sync(bid)             - Sync board")
'''

    def generate_ui_script(self) -> str:
        """Generate Pyto UI script for kanban management."""
        return '''"""
Kanban UI for Pyto
==================
Visual kanban board interface using Pyto's UI capabilities.
"""

try:
    import pyto_ui as ui
except ImportError:
    print("This script requires Pyto's UI module")
    exit(1)

import kanban


class KanbanUI:
    """Visual kanban interface."""

    def __init__(self):
        self.client = kanban.get_client()
        self.current_board = None

    def show_boards(self):
        """Show board selection."""
        boards = self.client.list_boards()

        view = ui.TableView()
        view.title = "Kanban Boards"

        items = []
        for board in boards:
            item = ui.TableViewCell()
            item.text = board.get("name", "Unnamed")
            item.detail = f"{len(board.get('cards', []))} cards"
            items.append(item)

        view.data_source = items
        ui.show_view(view)

    def show_board(self, board_id: str):
        """Show board details."""
        board = self.client.get_board(board_id)
        self.current_board = board

        # Create column views
        scroll = ui.ScrollView()
        scroll.content_width = len(board.get("columns", [])) * 200

        x = 10
        for column in board.get("columns", []):
            col_view = self._create_column_view(column)
            col_view.x = x
            scroll.add_subview(col_view)
            x += 210

        ui.show_view(scroll)

    def _create_column_view(self, column: dict) -> ui.View:
        """Create a column view."""
        view = ui.View()
        view.width = 200
        view.height = 500
        view.background_color = ui.Color.light_gray()

        title = ui.Label()
        title.text = column.get("name", "")
        title.font = ui.Font.bold_system_font(16)
        view.add_subview(title)

        y = 40
        for card in column.get("cards", []):
            card_view = self._create_card_view(card)
            card_view.y = y
            view.add_subview(card_view)
            y += 80

        return view

    def _create_card_view(self, card: dict) -> ui.View:
        """Create a card view."""
        view = ui.View()
        view.width = 180
        view.height = 70
        view.x = 10
        view.background_color = ui.Color.white()

        title = ui.Label()
        title.text = card.get("title", "")[:30]
        title.frame = (5, 5, 170, 25)
        view.add_subview(title)

        priority = ui.Label()
        priority.text = card.get("priority", "")
        priority.font = ui.Font.system_font(10)
        priority.frame = (5, 35, 170, 15)
        view.add_subview(priority)

        return view


if __name__ == "__main__":
    app = KanbanUI()
    app.show_boards()
'''
