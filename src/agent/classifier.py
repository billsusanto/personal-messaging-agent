import os

import logfire
from pydantic_ai import Agent

from src.config import settings
from src.db.models import MessageType

from .prompts import CLASSIFICATION_PROMPT

os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)

_classifier_agent: Agent[None, str] | None = None


def get_classifier_agent() -> Agent[None, str]:
    global _classifier_agent
    if _classifier_agent is None:
        _classifier_agent = Agent(
            "anthropic:claude-sonnet-4-20250514",
            system_prompt="You are a message classifier. Respond with only the category name.",
        )
    return _classifier_agent


async def classify_message(content: str) -> MessageType:
    with logfire.span("classify_message", content_preview=content[:100]):
        prompt = CLASSIFICATION_PROMPT.format(message=content)
        agent = get_classifier_agent()

        result = await agent.run(prompt)

        classification = result.data.strip().upper()

        if classification == "COMPLAINT":
            return MessageType.COMPLAINT
        elif classification == "ERROR":
            return MessageType.ERROR
        elif classification == "CASUAL":
            return MessageType.CASUAL
        else:
            return MessageType.UNKNOWN
