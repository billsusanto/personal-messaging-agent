# PRB WA Agent

WhatsApp AI agent for PRB team operations. Handles complaints/errors, forwards issues to developers, and routes casual messages.

## Setup

```bash
# Install dependencies
pip install -e .

# Copy env file and fill in values
cp .env.example .env

# Run locally
uvicorn src.main:app --reload
```

## Environment Variables

See `.env.example` for required variables:
- WhatsApp Business API credentials
- Phone numbers (work, personal, Adrian, Kris)
- Anthropic API key
- Neon database URL
- Logfire token

## Deploy to Render

1. Connect GitHub repo
2. Set environment variables
3. Deploy with Dockerfile

## Message Flow

1. Messages arrive via WhatsApp webhook
2. Agent classifies: complaint/error vs casual
3. Complaints → draft reply, queue for approval
4. Casual → forward to personal number
5. Approve via WhatsApp → agent sends reply
