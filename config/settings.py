"""
Configuration Settings
======================
Central configuration management for BlackRoad Kanban system.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: str = "sqlite"  # sqlite, postgres, d1
    path: str = "./data/kanban.db"
    host: Optional[str] = None
    port: Optional[int] = None
    name: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit: int = 100  # requests per minute
    timeout: int = 30


@dataclass
class CloudflareSettings:
    """Cloudflare integration settings."""
    enabled: bool = False
    api_key: str = ""
    account_id: str = ""
    kv_namespace_id: str = ""
    d1_database_id: str = ""
    r2_bucket: str = ""


@dataclass
class SalesforceSettings:
    """Salesforce integration settings."""
    enabled: bool = False
    instance_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    username: str = ""
    api_version: str = "v59.0"


@dataclass
class VercelSettings:
    """Vercel integration settings."""
    enabled: bool = False
    api_key: str = ""
    team_id: str = ""
    project_id: str = ""


@dataclass
class DigitalOceanSettings:
    """DigitalOcean integration settings."""
    enabled: bool = False
    api_key: str = ""
    spaces_region: str = "nyc3"
    spaces_bucket: str = ""
    spaces_key: str = ""
    spaces_secret: str = ""
    function_namespace: str = ""


@dataclass
class ClaudeSettings:
    """Claude (Anthropic) integration settings."""
    enabled: bool = True
    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096


@dataclass
class GitHubSettings:
    """GitHub integration settings."""
    enabled: bool = True
    token: str = ""
    owner: str = ""
    repo: str = ""
    project_number: Optional[int] = None


@dataclass
class MobileSettings:
    """Mobile app integration settings."""
    termius_enabled: bool = False
    termius_api_key: str = ""
    working_copy_key: str = ""


@dataclass
class HashingSettings:
    """Hashing configuration."""
    sha_infinity_depth: int = 7
    include_timestamps: bool = True
    salt: str = ""  # Optional salt for additional security


@dataclass
class Settings:
    """Main settings container."""
    app_name: str = "BlackRoad Kanban"
    environment: str = "development"  # development, staging, production
    log_level: str = "INFO"

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)

    # Integration settings
    cloudflare: CloudflareSettings = field(default_factory=CloudflareSettings)
    salesforce: SalesforceSettings = field(default_factory=SalesforceSettings)
    vercel: VercelSettings = field(default_factory=VercelSettings)
    digitalocean: DigitalOceanSettings = field(default_factory=DigitalOceanSettings)
    claude: ClaudeSettings = field(default_factory=ClaudeSettings)
    github: GitHubSettings = field(default_factory=GitHubSettings)
    mobile: MobileSettings = field(default_factory=MobileSettings)

    hashing: HashingSettings = field(default_factory=HashingSettings)

    @classmethod
    def from_env(cls) -> 'Settings':
        """Load settings from environment variables."""
        settings = cls()

        # Core settings
        settings.environment = os.getenv('ENVIRONMENT', 'development')
        settings.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # API settings
        settings.api.host = os.getenv('API_HOST', '0.0.0.0')
        settings.api.port = int(os.getenv('API_PORT', '8000'))
        settings.api.debug = os.getenv('API_DEBUG', 'false').lower() == 'true'

        # Cloudflare
        settings.cloudflare.enabled = os.getenv('CLOUDFLARE_ENABLED', 'false').lower() == 'true'
        settings.cloudflare.api_key = os.getenv('CLOUDFLARE_API_KEY', '')
        settings.cloudflare.account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID', '')
        settings.cloudflare.kv_namespace_id = os.getenv('CLOUDFLARE_KV_NAMESPACE_ID', '')
        settings.cloudflare.d1_database_id = os.getenv('CLOUDFLARE_D1_DATABASE_ID', '')

        # Salesforce
        settings.salesforce.enabled = os.getenv('SALESFORCE_ENABLED', 'false').lower() == 'true'
        settings.salesforce.instance_url = os.getenv('SALESFORCE_INSTANCE_URL', '')
        settings.salesforce.client_id = os.getenv('SALESFORCE_CLIENT_ID', '')
        settings.salesforce.client_secret = os.getenv('SALESFORCE_CLIENT_SECRET', '')

        # Vercel
        settings.vercel.enabled = os.getenv('VERCEL_ENABLED', 'false').lower() == 'true'
        settings.vercel.api_key = os.getenv('VERCEL_API_KEY', '')
        settings.vercel.team_id = os.getenv('VERCEL_TEAM_ID', '')
        settings.vercel.project_id = os.getenv('VERCEL_PROJECT_ID', '')

        # DigitalOcean
        settings.digitalocean.enabled = os.getenv('DIGITALOCEAN_ENABLED', 'false').lower() == 'true'
        settings.digitalocean.api_key = os.getenv('DIGITALOCEAN_API_KEY', '')
        settings.digitalocean.spaces_region = os.getenv('DIGITALOCEAN_SPACES_REGION', 'nyc3')
        settings.digitalocean.spaces_bucket = os.getenv('DIGITALOCEAN_SPACES_BUCKET', '')

        # Claude
        settings.claude.enabled = os.getenv('CLAUDE_ENABLED', 'true').lower() == 'true'
        settings.claude.api_key = os.getenv('ANTHROPIC_API_KEY', '')
        settings.claude.model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')

        # GitHub
        settings.github.enabled = os.getenv('GITHUB_ENABLED', 'true').lower() == 'true'
        settings.github.token = os.getenv('GITHUB_TOKEN', '')
        settings.github.owner = os.getenv('GITHUB_OWNER', '')
        settings.github.repo = os.getenv('GITHUB_REPO', '')

        # Hashing
        settings.hashing.sha_infinity_depth = int(os.getenv('SHA_INFINITY_DEPTH', '7'))
        settings.hashing.salt = os.getenv('HASH_SALT', '')

        return settings

    @classmethod
    def from_file(cls, filepath: str) -> 'Settings':
        """Load settings from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict) -> 'Settings':
        """Create settings from dictionary."""
        settings = cls()
        # Would need full implementation for nested dataclasses
        return settings

    def to_dict(self) -> Dict:
        """Convert to dictionary (excluding secrets)."""
        return {
            'app_name': self.app_name,
            'environment': self.environment,
            'log_level': self.log_level,
            'integrations': {
                'cloudflare': self.cloudflare.enabled,
                'salesforce': self.salesforce.enabled,
                'vercel': self.vercel.enabled,
                'digitalocean': self.digitalocean.enabled,
                'claude': self.claude.enabled,
                'github': self.github.enabled,
            }
        }

    def save(self, filepath: str):
        """Save settings to file (without secrets)."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def reload_settings():
    """Reload settings from environment."""
    global _settings
    _settings = Settings.from_env()
    return _settings
