from typing import Any, List, Dict, Union

import openai
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    retry_if_exception_type,
    RetryError,
)
from pydantic import BaseModel, Field

from app.logging_ import logger

SYSTEM_ROLE = "system"
USER_ROLE = "user"

client = openai.OpenAI()

class LlmMessage(BaseModel):
    role: str
    content: str | List[Dict[str, Union[str, Dict[str, str]]]]

@retry(
        wait=wait_random_exponential(multiplier=3, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(
            (
                openai.RateLimitError,
                openai.APIError,
                openai.InternalServerError,
                openai.APITimeoutError,
            )
        ),
    )
def chat_completions(messages: List[LlmMessage], model: str = "gpt-4o-mini", **kwargs):
    return client.chat.completions.create(
        messages=[m.model_dump() for m in messages],
        model=model,
        **kwargs,
    )


def ai_consider(content: str):
    resp = chat_completions([LlmMessage(role=USER_ROLE, content=content)])
    return resp.choices[0].message.content
