from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""

    model_config = {
        "env_file": str(Path(__file__).parent / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def openai_key_required(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "OPENAI_API_KEY is required. Add it to your .env file or environment."
            )
        return v


settings = Settings()

# Module-level constants — all existing imports continue to work unchanged
OPENAI_API_KEY = settings.OPENAI_API_KEY
ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
ALPHA_VANTAGE_API_KEY = settings.ALPHA_VANTAGE_API_KEY

ORCHESTRATOR_MODEL = "gpt-4o"
AGENT_MODEL        = "gpt-4o"
SYNTHESIS_MODEL    = "gpt-4o"

MAX_TOKENS  = 4096
TEMPERATURE = 0.3
