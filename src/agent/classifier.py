import logfire
from pydantic_ai import Agent

from src.config import settings
from src.db.models import MessageType

from .prompts import CLASSIFICATION_PROMPT

classifier_agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    system_prompt="You are a message classifier. Respond with only the category name.",
)


async def classify_message(content: str) -> MessageType:
    with logfire.span("classify_message", content_preview=content[:100]):
        prompt = CLASSIFICATION_PROMPT.format(message=content)

        result = await classifier_agent.run(
            prompt,
            model_settings={"api_key": settings.anthropic_api_key},
        )

        classification = result.data.strip().upper()

        if classification == "COMPLAINT":
            return MessageType.COMPLAINT
        elif classification == "ERROR":
            return MessageType.ERROR
        elif classification == "CASUAL":
            return MessageType.CASUAL
        else:
            return MessageType.UNKNOWN
