import uuid
from datetime import datetime
from typing import Any

import logfire
from sqlmodel import Session, select

from src.db.database import engine
from src.db.models import ActionType, AgentAction, Message, MessageType


async def log_message(
    wa_message_id: str,
    group_id: str,
    sender_phone: str,
    content: str,
    group_name: str | None = None,
    sender_name: str | None = None,
    message_type: MessageType = MessageType.UNKNOWN,
) -> Message | None:
    if not engine:
        logfire.warn("Database not configured")
        return None

    with Session(engine) as session:
        message = Message(
            wa_message_id=wa_message_id,
            group_id=group_id,
            group_name=group_name,
            sender_phone=sender_phone,
            sender_name=sender_name,
            content=content,
            message_type=message_type,
        )
        session.add(message)
        session.commit()
        session.refresh(message)

        logfire.info(
            "Message logged",
            message_id=str(message.id),
            wa_message_id=wa_message_id,
            message_type=message_type.value,
        )

        return message


async def log_action(
    message_id: uuid.UUID,
    action_type: ActionType,
    action_data: dict[str, Any] | None = None,
) -> AgentAction | None:
    if not engine:
        return None

    with Session(engine) as session:
        action = AgentAction(
            message_id=message_id,
            action_type=action_type,
            action_data=action_data or {},
        )
        session.add(action)
        session.commit()
        session.refresh(action)

        logfire.info(
            "Action logged",
            action_id=str(action.id),
            action_type=action_type.value,
        )

        return action


async def get_message_history(
    group_id: str | None = None,
    limit: int = 50,
) -> list[Message]:
    if not engine:
        return []

    with Session(engine) as session:
        statement = select(Message).order_by(Message.created_at.desc()).limit(limit)
        if group_id:
            statement = statement.where(Message.group_id == group_id)

        results = session.exec(statement).all()
        return list(results)


async def get_actions_for_message(message_id: uuid.UUID) -> list[AgentAction]:
    if not engine:
        return []

    with Session(engine) as session:
        statement = (
            select(AgentAction)
            .where(AgentAction.message_id == message_id)
            .order_by(AgentAction.created_at.desc())
        )
        results = session.exec(statement).all()
        return list(results)


async def get_recent_actions(limit: int = 50) -> list[AgentAction]:
    if not engine:
        return []

    with Session(engine) as session:
        statement = (
            select(AgentAction).order_by(AgentAction.created_at.desc()).limit(limit)
        )
        results = session.exec(statement).all()
        return list(results)
