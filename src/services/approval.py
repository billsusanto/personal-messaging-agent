import uuid
from datetime import datetime, timedelta

import logfire
from sqlmodel import Session, select

from src.db.database import engine
from src.db.models import ActionStatus, ActionType, AgentAction, ApprovalQueue, Message


async def create_approval_request(
    message: Message,
    draft_reply: str,
    target_group: str,
    expires_hours: int = 24,
) -> ApprovalQueue | None:
    if not engine:
        logfire.warn("Database not configured")
        return None

    with Session(engine) as session:
        action = AgentAction(
            message_id=message.id,
            action_type=ActionType.DRAFT_REPLY,
            action_data={"draft": draft_reply, "target": target_group},
            status=ActionStatus.PENDING_APPROVAL,
        )
        session.add(action)
        session.commit()
        session.refresh(action)

        approval = ApprovalQueue(
            action_id=action.id,
            draft_message=draft_reply,
            target_group=target_group,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours),
        )
        session.add(approval)
        session.commit()
        session.refresh(approval)

        logfire.info(
            "Approval request created",
            approval_id=str(approval.id),
            action_id=str(action.id),
        )

        return approval


async def get_pending_approvals() -> list[ApprovalQueue]:
    if not engine:
        return []

    with Session(engine) as session:
        statement = (
            select(ApprovalQueue)
            .join(AgentAction)
            .where(AgentAction.status == ActionStatus.PENDING_APPROVAL)
            .where(ApprovalQueue.expires_at > datetime.utcnow())
        )
        results = session.exec(statement).all()
        return list(results)


async def approve_action(approval_id: uuid.UUID) -> AgentAction | None:
    if not engine:
        return None

    with Session(engine) as session:
        approval = session.get(ApprovalQueue, approval_id)
        if not approval:
            return None

        action = session.get(AgentAction, approval.action_id)
        if not action:
            return None

        action.status = ActionStatus.APPROVED
        action.approved_at = datetime.utcnow()
        session.add(action)
        session.commit()
        session.refresh(action)

        logfire.info("Action approved", action_id=str(action.id))
        return action


async def reject_action(approval_id: uuid.UUID) -> AgentAction | None:
    if not engine:
        return None

    with Session(engine) as session:
        approval = session.get(ApprovalQueue, approval_id)
        if not approval:
            return None

        action = session.get(AgentAction, approval.action_id)
        if not action:
            return None

        action.status = ActionStatus.REJECTED
        session.add(action)
        session.commit()
        session.refresh(action)

        logfire.info("Action rejected", action_id=str(action.id))
        return action


async def mark_action_sent(action_id: uuid.UUID) -> AgentAction | None:
    if not engine:
        return None

    with Session(engine) as session:
        action = session.get(AgentAction, action_id)
        if not action:
            return None

        action.status = ActionStatus.SENT
        session.add(action)
        session.commit()
        session.refresh(action)

        logfire.info("Action marked as sent", action_id=str(action.id))
        return action
