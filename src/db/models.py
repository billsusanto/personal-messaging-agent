import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class MessageType(str, Enum):
    COMPLAINT = "complaint"
    ERROR = "error"
    CASUAL = "casual"
    UNKNOWN = "unknown"


class ActionType(str, Enum):
    DRAFT_REPLY = "draft_reply"
    FORWARD_DEV = "forward_dev"
    FORWARD_PERSONAL = "forward_personal"
    SEND_REPLY = "send_reply"


class ActionStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    wa_message_id: str = Field(index=True)
    group_id: str = Field(index=True)
    group_name: str | None = None
    sender_phone: str
    sender_name: str | None = None
    content: str
    message_type: MessageType = Field(default=MessageType.UNKNOWN)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    actions: list["AgentAction"] = Relationship(back_populates="message")


class AgentAction(SQLModel, table=True):
    __tablename__ = "agent_actions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    message_id: uuid.UUID = Field(foreign_key="messages.id", index=True)
    action_type: ActionType
    action_data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: ActionStatus = Field(default=ActionStatus.PENDING_APPROVAL)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: datetime | None = None

    message: Message = Relationship(back_populates="actions")
    approval: "ApprovalQueue | None" = Relationship(back_populates="action")


class ApprovalQueue(SQLModel, table=True):
    __tablename__ = "approval_queue"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    action_id: uuid.UUID = Field(foreign_key="agent_actions.id", unique=True, index=True)
    draft_message: str
    target_group: str
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    action: AgentAction = Relationship(back_populates="approval")
