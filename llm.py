import os

from dotenv import load_dotenv
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

MODEL = "openai/gpt-5.4-nano"
BASE_URL = "https://ai-gateway.vercel.sh/v1"
CACHE_PATH = ".langchain_cache.db"


def bootstrap() -> None:
    load_dotenv()
    # Cache LLM responses on disk: identical (prompt, model) calls skip the API.
    # Makes eval re-runs free + reproducible. Delete the .db to force fresh calls.
    set_llm_cache(SQLiteCache(database_path=CACHE_PATH))


def make_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=SecretStr(os.environ["AI_GATEWAY_API_KEY"]),
        max_retries=6,
    )
