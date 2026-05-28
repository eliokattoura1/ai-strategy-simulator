import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Single model for all agents until Anthropic key added
ORCHESTRATOR_MODEL = "gpt-4o"
AGENT_MODEL = "gpt-4o"
SYNTHESIS_MODEL = "gpt-4o"

MAX_TOKENS = 4096
TEMPERATURE = 0.3