import logfire
from fastapi import APIRouter, HTTPException, Query, Request

from src.config import settings
from src.whatsapp.models import ParsedMessage, WhatsAppWebhookPayload

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> int:
    if hub_mode == "subscribe" and hub_verify_token == settings.wa_verify_token:
        logfire.info("Webhook verified successfully")
        return int(hub_challenge)
    logfire.warn("Webhook verification failed", mode=hub_mode)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive_webhook(request: Request) -> dict:
    body = await request.json()
    logfire.info("Webhook received", payload=body)

    try:
        payload = WhatsAppWebhookPayload.model_validate(body)
    except Exception as e:
        logfire.error("Failed to parse webhook payload", error=str(e))
        return {"status": "error", "message": "Invalid payload"}

    messages: list[ParsedMessage] = []

    for entry in payload.entry:
        for change in entry.changes:
            if change.field != "messages":
                continue

            value = change.value
            if not value.messages or not value.contacts:
                continue

            contacts_map = {c.wa_id: c.profile.name for c in value.contacts}

            for msg in value.messages:
                if msg.type != "text" or not msg.text:
                    continue

                parsed = ParsedMessage(
                    message_id=msg.id,
                    from_phone=msg.from_,
                    sender_name=contacts_map.get(msg.from_, "Unknown"),
                    text=msg.text.body,
                    timestamp=msg.timestamp,
                )
                messages.append(parsed)
                logfire.info(
                    "Message parsed",
                    message_id=parsed.message_id,
                    from_phone=parsed.from_phone,
                    sender_name=parsed.sender_name,
                )

    return {"status": "ok", "messages_received": len(messages)}
