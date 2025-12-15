from dataclasses import dataclass

from pydantic_ai import RunContext


@dataclass
class AgentContext:
    message_content: str
    sender_name: str | None = None
    group_name: str | None = None


def draft_reply(ctx: RunContext[AgentContext], reply_text: str) -> dict:
    """Draft a reply message to send back to the sender.

    Args:
        ctx: The run context containing message information.
        reply_text: The text content of the reply to draft.

    Returns:
        A dict containing the action type and draft reply details.
    """
    return {
        "action": "draft_reply",
        "reply": reply_text,
        "original_message": ctx.deps.message_content,
        "sender": ctx.deps.sender_name,
    }


def escalate_to_dev(ctx: RunContext[AgentContext], reason: str, priority: str = "normal") -> dict:
    """Flag a message for developer escalation.

    Args:
        ctx: The run context containing message information.
        reason: The reason for escalating to a developer.
        priority: Priority level - 'low', 'normal', or 'high'.

    Returns:
        A dict containing the escalation details.
    """
    return {
        "action": "escalate_to_dev",
        "reason": reason,
        "priority": priority,
        "original_message": ctx.deps.message_content,
        "group": ctx.deps.group_name,
    }


def forward_to_personal(
    ctx: RunContext[AgentContext], reason: str, summary: str | None = None
) -> dict:
    """Flag a message for forwarding to a personal number.

    Args:
        ctx: The run context containing message information.
        reason: The reason for forwarding to personal.
        summary: Optional summary of the message to include.

    Returns:
        A dict containing the forwarding details.
    """
    return {
        "action": "forward_to_personal",
        "reason": reason,
        "summary": summary or ctx.deps.message_content[:200],
        "original_message": ctx.deps.message_content,
        "sender": ctx.deps.sender_name,
    }
