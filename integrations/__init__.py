"""
BlackRoad AI Integrations
=========================
Service integrations for kanban board sync and management.

Supported Services:
- Cloudflare (Workers, KV, D1, R2)
- Salesforce (CRM, Objects, Bulk API)
- Vercel (Deployments, Edge, Env)
- DigitalOcean (Droplets, Spaces, Functions)
- Claude (Anthropic AI)
- GitHub (Issues, Projects, Actions)
- Mobile (Termius, iSH, Shellfish, Working Copy, Pyto)
"""

from .base import BaseIntegration, IntegrationConfig, IntegrationError, WebhookHandler, SyncManager

__all__ = ["BaseIntegration", "IntegrationConfig", "IntegrationError", "WebhookHandler", "SyncManager"]


# Lazy imports for specific integrations
def get_cloudflare_integration():
    from .cloudflare.client import CloudflareIntegration, CloudflareConfig

    return CloudflareIntegration, CloudflareConfig


def get_salesforce_integration():
    from .salesforce.client import SalesforceIntegration, SalesforceConfig

    return SalesforceIntegration, SalesforceConfig


def get_vercel_integration():
    from .vercel.client import VercelIntegration, VercelConfig

    return VercelIntegration, VercelConfig


def get_digitalocean_integration():
    from .digitalocean.client import DigitalOceanIntegration, DigitalOceanConfig

    return DigitalOceanIntegration, DigitalOceanConfig


def get_claude_integration():
    from .claude.client import ClaudeIntegration, ClaudeConfig, ClaudeAgentIntegration

    return ClaudeIntegration, ClaudeConfig, ClaudeAgentIntegration


def get_github_integration():
    from .github.client import GitHubIntegration, GitHubConfig

    return GitHubIntegration, GitHubConfig


def get_mobile_integrations():
    from .mobile.clients import (
        TermiusIntegration,
        TermiusConfig,
        WorkingCopyIntegration,
        WorkingCopyConfig,
        ISHIntegration,
        ShellfishIntegration,
        PytoIntegration,
        PytoConfig,
    )

    return {
        "termius": (TermiusIntegration, TermiusConfig),
        "working_copy": (WorkingCopyIntegration, WorkingCopyConfig),
        "ish": ISHIntegration,
        "shellfish": ShellfishIntegration,
        "pyto": (PytoIntegration, PytoConfig),
    }
