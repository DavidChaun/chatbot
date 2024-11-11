from typing import Any, List, Dict

import uuid
import requests
from httpx import HTTPStatusError
from requests import HTTPError
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from duckduckgo_search import DDGS

from app import ZHIPUAI_API_KEY

client = DDGS()

@retry(
        wait=wait_random_exponential(multiplier=3, max=60),
        stop=stop_after_attempt(3),
    )
def net_search(keywords: str) -> List[Dict[str, Any]]:
    return client.text(keywords, region='wt-wt', max_results=10)


@retry(
        wait=wait_random_exponential(multiplier=3, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(HTTPError),
    )
def ai_consider(content: str):
    return client.chat(content)


@retry(
        wait=wait_random_exponential(multiplier=3, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(HTTPError),
    )
def web_search_pro(question: str) -> tuple[str, list[str], list[str]]:
    """
    直接返回适用于查询意图，llm的上下文（title+content），以及对应的ref links（title+link）
    :param question:
    :return:
    """
    msg = [
        {
            "role": "user",
            "content": question
        }
    ]
    tool = "web-search-pro"
    url = "https://open.bigmodel.cn/api/paas/v4/tools"
    request_id = str(uuid.uuid4())
    data = {
        "request_id": request_id,
        "tool": tool,
        "stream": False,
        "messages": msg
    }

    resp = requests.post(
        url,
        json=data,
        headers={'Authorization': ZHIPUAI_API_KEY},
        timeout=300
    )
    if resp.status_code != 200:
        raise HTTPError()

    tool_calls = resp.json()["choices"][0]["message"]["tool_calls"]

    contexts = []
    links = []
    # e1是意图，e2是结果
    # {'category': '天气', 'index': 0, 'intent': 'SEARCH_TOOL', 'keywords': '最近辽宁的天气', 'query': '最近辽宁的天气'}
    intent = tool_calls[0]["search_intent"][0]["category"]
    for t in tool_calls[-1]["search_result"]:
        contexts.append(
            f"title: {t.get('title', '')}\ncontent: {t.get('content', '')}"
        )
        links.append(
            f"标题: {t.get('title', '')}\n{t.get('link', '')}"
        )

    return intent, contexts, links