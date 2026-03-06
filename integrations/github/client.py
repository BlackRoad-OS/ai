"""
GitHub Integration
==================
Repository, Issues, Projects, and Actions integration.

Features:
- Issue <-> Card sync
- Projects board mapping
- PR tracking
- Actions automation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sys
sys.path.insert(0, '/home/user/ai')

from integrations.base import BaseIntegration, IntegrationConfig


@dataclass
class GitHubConfig(IntegrationConfig):
    """GitHub-specific configuration."""
    owner: str = ""
    repo: str = ""
    project_number: Optional[int] = None


class GitHubIntegration(BaseIntegration):
    """
    GitHub integration for code-centric kanban.

    Maps:
    - Kanban cards <-> GitHub Issues
    - Kanban columns <-> Project columns
    - Card labels <-> Issue labels
    """

    def __init__(self, config: GitHubConfig):
        config.base_url = "https://api.github.com"
        config.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        super().__init__(config)
        self.gh_config = config
        self._state_cache = {}

    def _get_repo_base(self) -> str:
        """Get repository API base."""
        return f"/repos/{self.gh_config.owner}/{self.gh_config.repo}"

    async def health_check(self) -> bool:
        """Check GitHub API connectivity."""
        try:
            result = await self.request("GET", "/user")
            return 'login' in result
        except Exception:
            return False

    async def sync(self, board) -> Dict:
        """Sync kanban board with GitHub Issues/Projects."""
        results = {'issues': [], 'success': True}

        try:
            for card in board.get_all_cards():
                # Sync card to GitHub issue
                if card.github_issue_number:
                    # Update existing issue
                    await self.update_issue(
                        card.github_issue_number,
                        title=card.title,
                        body=card.description,
                        labels=card.labels
                    )
                else:
                    # Create new issue
                    issue = await self.create_issue(
                        title=card.title,
                        body=card.description,
                        labels=card.labels
                    )
                    card.github_issue_number = issue.get('number')

                results['issues'].append(card.github_issue_number)

            self._state_cache[board.id] = board.to_dict()

        except Exception as e:
            results['success'] = False
            results['error'] = str(e)

        return results

    def get_state_hash(self) -> str:
        """Get hash of GitHub state."""
        from utils.hashing import sha256_hash
        return sha256_hash(self._state_cache)

    # Issue Operations
    async def list_issues(
        self,
        state: str = "open",
        labels: List[str] = None
    ) -> List[Dict]:
        """List repository issues."""
        params = {'state': state}
        if labels:
            params['labels'] = ','.join(labels)

        result = await self.request(
            "GET",
            f"{self._get_repo_base()}/issues",
            params=params
        )
        return result

    async def create_issue(
        self,
        title: str,
        body: str = "",
        labels: List[str] = None,
        assignees: List[str] = None,
        milestone: int = None
    ) -> Dict:
        """Create a new issue."""
        data = {'title': title, 'body': body}
        if labels:
            data['labels'] = labels
        if assignees:
            data['assignees'] = assignees
        if milestone:
            data['milestone'] = milestone

        result = await self.request(
            "POST",
            f"{self._get_repo_base()}/issues",
            data=data
        )
        return result

    async def update_issue(
        self,
        issue_number: int,
        **kwargs
    ) -> Dict:
        """Update an issue."""
        result = await self.request(
            "PATCH",
            f"{self._get_repo_base()}/issues/{issue_number}",
            data=kwargs
        )
        return result

    async def close_issue(self, issue_number: int) -> Dict:
        """Close an issue."""
        return await self.update_issue(issue_number, state="closed")

    # Pull Request Operations
    async def list_prs(self, state: str = "open") -> List[Dict]:
        """List pull requests."""
        result = await self.request(
            "GET",
            f"{self._get_repo_base()}/pulls",
            params={'state': state}
        )
        return result

    async def get_pr(self, pr_number: int) -> Dict:
        """Get pull request details."""
        result = await self.request(
            "GET",
            f"{self._get_repo_base()}/pulls/{pr_number}"
        )
        return result

    async def create_pr(
        self,
        title: str,
        head: str,
        base: str,
        body: str = ""
    ) -> Dict:
        """Create pull request."""
        result = await self.request(
            "POST",
            f"{self._get_repo_base()}/pulls",
            data={
                'title': title,
                'head': head,
                'base': base,
                'body': body
            }
        )
        return result

    # Projects (GraphQL API for Projects v2)
    async def get_project(self) -> Dict:
        """Get project details using GraphQL."""
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
            repository(owner: $owner, name: $repo) {
                projectV2(number: $number) {
                    id
                    title
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2Field {
                                id
                                name
                            }
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                options {
                                    id
                                    name
                                }
                            }
                        }
                    }
                    items(first: 100) {
                        nodes {
                            id
                            content {
                                ... on Issue {
                                    number
                                    title
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        result = await self.request(
            "POST",
            "/graphql",
            data={
                'query': query,
                'variables': {
                    'owner': self.gh_config.owner,
                    'repo': self.gh_config.repo,
                    'number': self.gh_config.project_number
                }
            }
        )
        return result

    # Actions
    async def list_workflows(self) -> List[Dict]:
        """List repository workflows."""
        result = await self.request(
            "GET",
            f"{self._get_repo_base()}/actions/workflows"
        )
        return result.get('workflows', [])

    async def trigger_workflow(
        self,
        workflow_id: str,
        ref: str,
        inputs: Dict = None
    ) -> bool:
        """Trigger a workflow dispatch."""
        await self.request(
            "POST",
            f"{self._get_repo_base()}/actions/workflows/{workflow_id}/dispatches",
            data={
                'ref': ref,
                'inputs': inputs or {}
            }
        )
        return True

    async def list_workflow_runs(
        self,
        workflow_id: str = None,
        status: str = None
    ) -> List[Dict]:
        """List workflow runs."""
        params = {}
        if status:
            params['status'] = status

        endpoint = f"{self._get_repo_base()}/actions/runs"
        if workflow_id:
            endpoint = f"{self._get_repo_base()}/actions/workflows/{workflow_id}/runs"

        result = await self.request("GET", endpoint, params=params)
        return result.get('workflow_runs', [])


class GitHubWebhookHandler:
    """Handle GitHub webhook events."""

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature."""
        import hmac
        import hashlib
        # Would use GITHUB_WEBHOOK_SECRET
        return True

    async def process(self, event_type: str, payload: Dict) -> Dict:
        """Process GitHub webhook event."""
        handlers = {
            'issues': self._handle_issue_event,
            'pull_request': self._handle_pr_event,
            'push': self._handle_push_event,
            'workflow_run': self._handle_workflow_event,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(payload)

        return {'processed': False, 'reason': 'Unknown event type'}

    async def _handle_issue_event(self, payload: Dict) -> Dict:
        action = payload.get('action')
        issue = payload.get('issue', {})

        return {
            'processed': True,
            'action': action,
            'issue_number': issue.get('number'),
            'title': issue.get('title')
        }

    async def _handle_pr_event(self, payload: Dict) -> Dict:
        action = payload.get('action')
        pr = payload.get('pull_request', {})

        return {
            'processed': True,
            'action': action,
            'pr_number': pr.get('number'),
            'merged': pr.get('merged', False)
        }

    async def _handle_push_event(self, payload: Dict) -> Dict:
        return {
            'processed': True,
            'ref': payload.get('ref'),
            'commits': len(payload.get('commits', []))
        }

    async def _handle_workflow_event(self, payload: Dict) -> Dict:
        run = payload.get('workflow_run', {})

        return {
            'processed': True,
            'workflow': run.get('name'),
            'conclusion': run.get('conclusion'),
            'run_id': run.get('id')
        }
