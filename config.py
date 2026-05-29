import os
from pathlib import Path
from dotenv import load_dotenv

# Find .env relative to this file
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# Single model for all agents until Anthropic key added
ORCHESTRATOR_MODEL = "gpt-4o"
AGENT_MODEL = "gpt-4o"
SYNTHESIS_MODEL = "gpt-4o"

MAX_TOKENS = 4096
TEMPERATURE = 0.3