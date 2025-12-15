import logfire

from src.agent import classify_message, process_message
from src.config import settings
from src.db.models import MessageType
from src.rag import get_context
from src.services.approval import create_approval_request
from src.services.tracking import log_action, log_message
from src.whatsapp.client import whatsapp_client
from src.whatsapp.models import ParsedMessage
from src.db.models import ActionType


async def handle_incoming_message(parsed: ParsedMessage, group_id: str, group_name: str | None = None):
    with logfire.span("handle_incoming_message", message_id=parsed.message_id):
        message_type = await classify_message(parsed.text)

        message = await log_message(
            wa_message_id=parsed.message_id,
            group_id=group_id,
            sender_phone=parsed.from_phone,
            sender_name=parsed.sender_name,
            content=parsed.text,
            message_type=message_type,
        )

        if not message:
            logfire.warn("Failed to log message")
            return

        if message_type == MessageType.CASUAL:
            await _forward_to_personal(message, parsed)
            return

        context = get_context(parsed.text)
        agent_response = await process_message(parsed.text, context=context)

        if message_type in (MessageType.COMPLAINT, MessageType.ERROR):
            await create_approval_request(
                message=message,
                draft_reply=agent_response.message,
                target_group=group_id,
            )

            notification = (
                f"New {message_type.value} from {parsed.sender_name}:\n"
                f"'{parsed.text[:100]}...'\n\n"
                f"Draft reply:\n'{agent_response.message[:200]}...'\n\n"
                f"Reply 'approve' or send edited response."
            )

            if settings.personal_phone:
                await whatsapp_client.send_message(settings.personal_phone, notification)

        logfire.info(
            "Message handled",
            message_id=str(message.id),
            message_type=message_type.value,
        )


async def _forward_to_personal(message, parsed: ParsedMessage):
    if not settings.personal_phone:
        logfire.warn("Personal phone not configured")
        return

    forward_text = (
        f"[Casual] From {parsed.sender_name}:\n"
        f"{parsed.text}"
    )

    await whatsapp_client.send_message(settings.personal_phone, forward_text)

    await log_action(
        message_id=message.id,
        action_type=ActionType.FORWARD_PERSONAL,
        action_data={"forwarded_to": settings.personal_phone},
    )


async def handle_approval_response(response_text: str, from_phone: str):
    if from_phone != settings.personal_phone:
        return

    response_lower = response_text.lower().strip()

    if response_lower == "approve":
        pass
    elif response_lower.startswith("edit:"):
        pass
    elif response_lower == "reject":
        pass
