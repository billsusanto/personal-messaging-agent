from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.classifier import classify_message
from src.agent.core import AgentResponse, process_message
from src.agent.prompts import CLASSIFICATION_PROMPT, SYSTEM_PROMPT
from src.agent.tools import AgentContext, draft_reply, escalate_to_dev, forward_to_personal
from src.db.models import MessageType


class TestPrompts:
    def test_system_prompt_exists(self):
        assert SYSTEM_PROMPT
        assert "PRB team" in SYSTEM_PROMPT

    def test_classification_prompt_has_placeholder(self):
        assert "{message}" in CLASSIFICATION_PROMPT

    def test_classification_prompt_lists_categories(self):
        assert "COMPLAINT" in CLASSIFICATION_PROMPT
        assert "ERROR" in CLASSIFICATION_PROMPT
        assert "CASUAL" in CLASSIFICATION_PROMPT
        assert "UNKNOWN" in CLASSIFICATION_PROMPT


class TestTools:
    def test_draft_reply(self):
        ctx = MagicMock()
        ctx.deps = AgentContext(
            message_content="Test message",
            sender_name="John",
            group_name="Support Group",
        )

        result = draft_reply(ctx, "Thank you for reaching out!")

        assert result["action"] == "draft_reply"
        assert result["reply"] == "Thank you for reaching out!"
        assert result["original_message"] == "Test message"
        assert result["sender"] == "John"

    def test_escalate_to_dev(self):
        ctx = MagicMock()
        ctx.deps = AgentContext(
            message_content="App crashed",
            sender_name="Jane",
            group_name="Tech Support",
        )

        result = escalate_to_dev(ctx, "Critical bug reported", priority="high")

        assert result["action"] == "escalate_to_dev"
        assert result["reason"] == "Critical bug reported"
        assert result["priority"] == "high"
        assert result["group"] == "Tech Support"

    def test_escalate_to_dev_default_priority(self):
        ctx = MagicMock()
        ctx.deps = AgentContext(message_content="Minor issue")

        result = escalate_to_dev(ctx, "Some bug")

        assert result["priority"] == "normal"

    def test_forward_to_personal(self):
        ctx = MagicMock()
        ctx.deps = AgentContext(
            message_content="Please call me when you can",
            sender_name="Boss",
        )

        result = forward_to_personal(ctx, "Personal request")

        assert result["action"] == "forward_to_personal"
        assert result["reason"] == "Personal request"
        assert result["sender"] == "Boss"

    def test_forward_to_personal_with_summary(self):
        ctx = MagicMock()
        ctx.deps = AgentContext(message_content="Long message content here")

        result = forward_to_personal(ctx, "Urgent", summary="Short summary")

        assert result["summary"] == "Short summary"


class TestClassifier:
    @pytest.mark.asyncio
    async def test_classify_complaint(self):
        mock_result = MagicMock()
        mock_result.data = "COMPLAINT"
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("src.agent.classifier.get_classifier_agent", return_value=mock_agent):
            result = await classify_message("I'm very frustrated with your service!")
            assert result == MessageType.COMPLAINT

    @pytest.mark.asyncio
    async def test_classify_error(self):
        mock_result = MagicMock()
        mock_result.data = "ERROR"
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("src.agent.classifier.get_classifier_agent", return_value=mock_agent):
            result = await classify_message("The app keeps crashing with error code 500")
            assert result == MessageType.ERROR

    @pytest.mark.asyncio
    async def test_classify_casual(self):
        mock_result = MagicMock()
        mock_result.data = "CASUAL"
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("src.agent.classifier.get_classifier_agent", return_value=mock_agent):
            result = await classify_message("Hey! Just wanted to say thank you!")
            assert result == MessageType.CASUAL

    @pytest.mark.asyncio
    async def test_classify_unknown(self):
        mock_result = MagicMock()
        mock_result.data = "UNKNOWN"
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("src.agent.classifier.get_classifier_agent", return_value=mock_agent):
            result = await classify_message("...")
            assert result == MessageType.UNKNOWN

    @pytest.mark.asyncio
    async def test_classify_handles_lowercase(self):
        mock_result = MagicMock()
        mock_result.data = "complaint"
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("src.agent.classifier.get_classifier_agent", return_value=mock_agent):
            result = await classify_message("Bad service")
            assert result == MessageType.COMPLAINT


class TestCoreAgent:
    @pytest.mark.asyncio
    async def test_process_message_returns_agent_response(self):
        mock_result = MagicMock()
        mock_result.data = "I'll help you with that."
        mock_result.all_messages.return_value = []
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("src.agent.core.get_prb_agent", return_value=mock_agent):
            result = await process_message("Hello, I need help")
            assert isinstance(result, AgentResponse)
            assert result.message == "I'll help you with that."
            assert result.actions == []

    @pytest.mark.asyncio
    async def test_process_message_with_context(self):
        mock_result = MagicMock()
        mock_result.data = "Got it."
        mock_result.all_messages.return_value = []
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("src.agent.core.get_prb_agent", return_value=mock_agent):
            await process_message("Help me", context="Previous conversation")
            call_args = mock_agent.run.call_args
            assert "Context:" in call_args[0][0]
            assert "Previous conversation" in call_args[0][0]


class TestAgentContext:
    def test_agent_context_required_fields(self):
        ctx = AgentContext(message_content="Test")
        assert ctx.message_content == "Test"
        assert ctx.sender_name is None
        assert ctx.group_name is None

    def test_agent_context_all_fields(self):
        ctx = AgentContext(
            message_content="Test",
            sender_name="John",
            group_name="Support",
        )
        assert ctx.message_content == "Test"
        assert ctx.sender_name == "John"
        assert ctx.group_name == "Support"
