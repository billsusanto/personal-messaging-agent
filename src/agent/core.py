import os
from dataclasses import dataclass
from typing import Any

import logfire
from pydantic_ai import Agent

from src.config import settings

from .prompts import SYSTEM_PROMPT
from .tools import AgentContext, draft_reply, escalate_to_dev, forward_to_personal

os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)


@dataclass
class AgentResponse:
    message: str
    actions: list[dict[str, Any]]


_prb_agent: Agent[AgentContext, str] | None = None


def get_prb_agent() -> Agent[AgentContext, str]:
    global _prb_agent
    if _prb_agent is None:
        _prb_agent = Agent(
            "anthropic:claude-sonnet-4-20250514",
            system_prompt=SYSTEM_PROMPT,
            deps_type=AgentContext,
        )
        _prb_agent.tool(draft_reply)
        _prb_agent.tool(escalate_to_dev)
        _prb_agent.tool(forward_to_personal)
    return _prb_agent


async def process_message(message: str, context: str | None = None) -> AgentResponse:
    with logfire.span("process_message", message_preview=message[:100]):
        deps = AgentContext(message_content=message)

        prompt = message
        if context:
            prompt = f"Context: {context}\n\nMessage: {message}"

        agent = get_prb_agent()
        result = await agent.run(prompt, deps=deps)

        actions = []
        for call in result.all_messages():
            if hasattr(call, "parts"):
                for part in call.parts:
                    if hasattr(part, "content") and isinstance(part.content, dict):
                        actions.append(part.content)

        return AgentResponse(
            message=result.data,
            actions=actions,
        )
