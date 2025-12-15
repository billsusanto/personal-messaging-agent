import httpx
import logfire

from src.config import settings

BASE_URL = "https://graph.facebook.com/v21.0"


class WhatsAppClient:
    def __init__(
        self,
        phone_number_id: str | None = None,
        access_token: str | None = None,
    ):
        self.phone_number_id = phone_number_id or settings.wa_phone_number_id
        self.access_token = access_token or settings.wa_access_token
        self.base_url = f"{BASE_URL}/{self.phone_number_id}"

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def send_message(self, to: str, message: str) -> dict:
        url = f"{self.base_url}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            result = response.json()
            msg_id = result.get("messages", [{}])[0].get("id")
            logfire.info("WhatsApp message sent", to=to, message_id=msg_id)
            return result

    async def send_template(self, to: str, template_name: str, params: list[str]) -> dict:
        url = f"{self.base_url}/messages"
        components = []
        if params:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in params],
            })

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"},
                "components": components,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            result = response.json()
            logfire.info("WhatsApp template sent", to=to, template=template_name)
            return result

    async def mark_as_read(self, message_id: str) -> dict:
        url = f"{self.base_url}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            result = response.json()
            logfire.info("WhatsApp message marked as read", message_id=message_id)
            return result


whatsapp_client = WhatsAppClient()
