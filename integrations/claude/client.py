"""
Claude (Anthropic) Integration
==============================
AI assistant integration for intelligent kanban operations.

Features:
- Card content generation
- Priority suggestions
- Task breakdown
- Natural language queries
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import sys

sys.path.insert(0, "/home/user/ai")

from integrations.base import BaseIntegration, IntegrationConfig


@dataclass
class ClaudeConfig(IntegrationConfig):
    """Claude API configuration."""

    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096


class ClaudeIntegration(BaseIntegration):
    """
    Anthropic Claude API integration.

    Used for:
    - Generating card descriptions
    - Suggesting task breakdowns
    - Analyzing board health
    - Natural language board queries
    """

    def __init__(self, config: ClaudeConfig):
        config.base_url = "https://api.anthropic.com"
        config.headers = {"anthropic-version": "2023-06-01", "x-api-key": config.api_key or ""}
        super().__init__(config)
        self.claude_config = config
        self._state_cache = {}

    async def health_check(self) -> bool:
        """Check Claude API connectivity."""
        try:
            # Simple message to verify connectivity
            result = await self.send_message("Hello", max_tokens=10)
            return "content" in result
        except Exception:
            return False

    async def sync(self, board) -> Dict:
        """
        Sync doesn't apply to Claude in the traditional sense.
        Instead, we can analyze the board and provide insights.
        """
        results = {"analysis": None, "success": True}

        try:
            analysis = await self.analyze_board(board)
            results["analysis"] = analysis
            self._state_cache[board.id] = {"last_analysis": analysis, "board_id": board.id}
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    def get_state_hash(self) -> str:
        """Get hash of Claude interaction state."""
        from utils.hashing import sha256_hash

        return sha256_hash(self._state_cache)

    # Core Message API
    async def send_message(
        self, content: str, system: str = None, max_tokens: int = None, temperature: float = 0.7
    ) -> Dict:
        """Send a message to Claude."""
        data = {
            "model": self.claude_config.model,
            "max_tokens": max_tokens or self.claude_config.max_tokens,
            "messages": [{"role": "user", "content": content}],
            "temperature": temperature,
        }

        if system:
            data["system"] = system

        result = await self.request("POST", "/v1/messages", data=data)
        return result

    async def send_conversation(self, messages: List[Dict], system: str = None, max_tokens: int = None) -> Dict:
        """Send a multi-turn conversation."""
        data = {
            "model": self.claude_config.model,
            "max_tokens": max_tokens or self.claude_config.max_tokens,
            "messages": messages,
        }

        if system:
            data["system"] = system

        result = await self.request("POST", "/v1/messages", data=data)
        return result

    # Kanban-specific Operations
    async def generate_card_description(self, title: str, context: str = "") -> str:
        """Generate a detailed card description."""
        prompt = f"""Generate a clear, actionable description for a kanban card.

Title: {title}
Context: {context}

Provide:
1. Clear objective
2. Acceptance criteria (bullet points)
3. Suggested subtasks if applicable

Keep it concise but complete."""

        result = await self.send_message(prompt, temperature=0.5)
        return result.get("content", [{}])[0].get("text", "")

    async def suggest_priority(self, card_title: str, card_description: str, board_context: str = "") -> Dict:
        """Suggest priority for a card."""
        prompt = f"""Analyze this kanban card and suggest a priority level.

Title: {card_title}
Description: {card_description}
Board Context: {board_context}

Respond in JSON format:
{{"priority": "critical|high|medium|low", "reasoning": "brief explanation"}}"""

        result = await self.send_message(prompt, temperature=0.3)
        text = result.get("content", [{}])[0].get("text", "{}")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"priority": "medium", "reasoning": "Could not analyze"}

    async def breakdown_task(self, task_description: str, max_subtasks: int = 5) -> List[Dict]:
        """Break down a task into subtasks."""
        prompt = f"""Break down this task into smaller, actionable subtasks.

Task: {task_description}
Maximum subtasks: {max_subtasks}

Respond in JSON format:
[{{"title": "subtask title", "description": "brief description", "estimated_effort": "small|medium|large"}}]"""

        result = await self.send_message(prompt, temperature=0.5)
        text = result.get("content", [{}])[0].get("text", "[]")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return []

    async def analyze_board(self, board) -> Dict:
        """Analyze board health and provide insights."""
        board_data = board.to_dict()

        prompt = f"""Analyze this kanban board and provide insights.

Board Data:
{json.dumps(board_data, indent=2)}

Provide analysis in JSON format:
{{
    "health_score": 0-100,
    "bottlenecks": ["list of identified bottlenecks"],
    "suggestions": ["list of improvement suggestions"],
    "workload_balance": "assessment of work distribution",
    "risk_items": ["cards that may need attention"]
}}"""

        result = await self.send_message(prompt, temperature=0.4)
        text = result.get("content", [{}])[0].get("text", "{}")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"health_score": 0, "error": "Could not analyze"}

    async def natural_language_query(self, query: str, board_context: Dict) -> str:
        """Answer natural language questions about the board."""
        system = """You are a helpful assistant for a kanban board system.
Answer questions about the board state, cards, and workflow.
Be concise and actionable."""

        prompt = f"""Board Context:
{json.dumps(board_context, indent=2)}

User Question: {query}"""

        result = await self.send_message(prompt, system=system, temperature=0.6)
        return result.get("content", [{}])[0].get("text", "")


class ClaudeAgentIntegration(ClaudeIntegration):
    """
    Extended Claude integration for autonomous agent operations.

    Provides:
    - Task planning
    - Execution guidance
    - Error analysis
    """

    async def plan_execution(self, task: str, available_tools: List[str]) -> Dict:
        """Plan task execution steps."""
        prompt = f"""Plan the execution of this task.

Task: {task}
Available Tools: {', '.join(available_tools)}

Respond in JSON:
{{
    "steps": [
        {{"action": "tool_name", "params": {{}}, "reason": "why this step"}}
    ],
    "estimated_complexity": "low|medium|high",
    "potential_issues": ["list of things that could go wrong"]
}}"""

        result = await self.send_message(prompt, temperature=0.4)
        text = result.get("content", [{}])[0].get("text", "{}")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"steps": [], "error": "Could not plan"}

    async def analyze_error(self, error: str, context: str) -> Dict:
        """Analyze an error and suggest fixes."""
        prompt = f"""Analyze this error and suggest fixes.

Error: {error}
Context: {context}

Respond in JSON:
{{
    "root_cause": "likely cause",
    "fixes": ["ordered list of potential fixes"],
    "prevention": "how to prevent this in future"
}}"""

        result = await self.send_message(prompt, temperature=0.3)
        text = result.get("content", [{}])[0].get("text", "{}")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"root_cause": "Unknown", "fixes": [], "error": "Could not analyze"}
