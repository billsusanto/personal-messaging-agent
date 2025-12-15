from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # WhatsApp Business API
    wa_phone_number_id: str = ""
    wa_business_account_id: str = ""
    wa_access_token: str = ""
    wa_verify_token: str = "prb-wa-agent-verify"

    # Phone Numbers
    work_phone: str = ""
    personal_phone: str = ""
    adrian_phone: str = ""
    kris_phone: str = ""

    # AI
    anthropic_api_key: str = ""

    # Database (Neon)
    database_url: str = ""

    # Logfire
    logfire_token: str = ""

    # App
    debug: bool = False


settings = Settings()
