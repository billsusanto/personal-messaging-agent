import pytest
from httpx import ASGITransport, AsyncClient

from src.config import settings
from src.main import app
from src.whatsapp.client import WhatsAppClient
from src.whatsapp.models import ParsedMessage, WhatsAppWebhookPayload


class TestWhatsAppModels:
    def test_parse_webhook_payload(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15551234567",
                                    "phone_number_id": "123456789",
                                },
                                "contacts": [
                                    {"profile": {"name": "John Doe"}, "wa_id": "15559876543"}
                                ],
                                "messages": [
                                    {
                                        "from": "15559876543",
                                        "id": "wamid.abc123",
                                        "timestamp": "1699999999",
                                        "type": "text",
                                        "text": {"body": "Hello, world!"},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

        result = WhatsAppWebhookPayload.model_validate(payload)
        assert result.object == "whatsapp_business_account"
        assert len(result.entry) == 1
        assert len(result.entry[0].changes) == 1
        assert result.entry[0].changes[0].field == "messages"

        value = result.entry[0].changes[0].value
        assert value.messages is not None
        assert len(value.messages) == 1
        assert value.messages[0].from_ == "15559876543"
        assert value.messages[0].text.body == "Hello, world!"

    def test_parsed_message(self):
        msg = ParsedMessage(
            message_id="wamid.abc123",
            from_phone="15559876543",
            sender_name="John Doe",
            text="Hello, world!",
            timestamp="1699999999",
        )
        assert msg.message_id == "wamid.abc123"
        assert msg.from_phone == "15559876543"
        assert msg.sender_name == "John Doe"
        assert msg.text == "Hello, world!"


class TestWhatsAppClient:
    def test_client_initialization(self):
        client = WhatsAppClient(
            phone_number_id="test_phone_id",
            access_token="test_token",
        )
        assert client.phone_number_id == "test_phone_id"
        assert client.access_token == "test_token"
        assert "test_phone_id" in client.base_url

    def test_client_headers(self):
        client = WhatsAppClient(
            phone_number_id="test_phone_id",
            access_token="test_token",
        )
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"


class TestWebhookEndpoints:
    @pytest.fixture
    def async_client(self):
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    async def test_verify_webhook_success(self, async_client):
        async with async_client as client:
            response = await client.get(
                "/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": settings.wa_verify_token,
                    "hub.challenge": "123456",
                },
            )
        assert response.status_code == 200
        assert response.json() == 123456

    async def test_verify_webhook_failure(self, async_client):
        async with async_client as client:
            response = await client.get(
                "/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "wrong_token",
                    "hub.challenge": "123456",
                },
            )
        assert response.status_code == 403

    async def test_receive_webhook(self, async_client):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15551234567",
                                    "phone_number_id": "123456789",
                                },
                                "contacts": [
                                    {"profile": {"name": "John Doe"}, "wa_id": "15559876543"}
                                ],
                                "messages": [
                                    {
                                        "from": "15559876543",
                                        "id": "wamid.abc123",
                                        "timestamp": "1699999999",
                                        "type": "text",
                                        "text": {"body": "Hello, world!"},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

        async with async_client as client:
            response = await client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["messages_received"] == 1

    async def test_receive_webhook_status_update(self, async_client):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15551234567",
                                    "phone_number_id": "123456789",
                                },
                                "statuses": [
                                    {
                                        "id": "wamid.abc123",
                                        "status": "delivered",
                                        "timestamp": "1699999999",
                                        "recipient_id": "15559876543",
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

        async with async_client as client:
            response = await client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["messages_received"] == 0
