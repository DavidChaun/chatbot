from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel

from app.database import Base, get_db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, DateTime, Integer, JSON


class Completion(Base):
    __tablename__ = "completion"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_body = Column(JSONB)
    result = Column(String)
    response_body = Column(JSONB)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    begin_at = Column(DateTime, comment="request begin time")
    end_at = Column(DateTime)
    created_by = Column(String(255), index=True)


def save_llm_result(messages: List[Dict], result: BaseModel, begin_at: datetime, username: str) -> Completion:
    db = next(get_db())
    entity = Completion(
        request_body=messages,
        result=result.choices[0].message.content,
        response_body=result.model_dump(),
        prompt_tokens=result.usage.prompt_tokens,
        completion_tokens=result.usage.completion_tokens,
        begin_at=begin_at,
        end_at=datetime.now(),
        created_by=username,
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity