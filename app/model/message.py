from collections.abc import Collection
from datetime import datetime
from typing import List

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy import Column, String, Text, JSON, Integer, DateTime, ForeignKey, Boolean

from app.database import Base, get_db
from sqlalchemy.sql.operators import or_


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type_ = Column(String(255), index=True, comment="消息类型, `text`|`pic`|`link`|`video`", name="type")
    content = Column(Text, comment="消息内容")
    from_ = Column(String(255), index=True, comment="发送者", name="from")
    to = Column(String(255), index=True, comment="接收者")
    session_id = Column(String(255), comment="itchat 发送消息过来时的user id，每次重启就会变化，只能当session id")
    is_group = Column(Boolean, comment="是否是群聊")
    is_clear = Column(Boolean, comment="清除记忆")
    created_at = Column(DateTime)

    message_extra = relationship(
        "MessageExtra",
        back_populates="message",
        passive_deletes=True,
        uselist=False,
    )


class MessageExtra(Base):
    __tablename__ = "message_extra"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey(f"{Message.__tablename__}.id", ondelete="CASCADE"), index=True, nullable=False)
    content_meta = Column(JSON, comment="消息的元信息")
    content_bytes = Column(BYTEA, comment="消息内容，一般是图片、链接抓取等")

    message = relationship(Message, back_populates="message_extra")


def list_messages(db, id_: str | Collection[str]) -> List[Message]:
    ids = id_ if isinstance(id_, Collection) else [id_]
    return db.query(Message).filter(Message.id.in_(ids)).all()


def clear_messages(session_id: str) -> None:
    db = next(get_db())
    db.query(Message).filter(Message.session_id == session_id).update({
        "is_clear": True
    })


def list_previous_messages(session_id: str, create_at_gt: datetime) -> List[Message]:
    db = next(get_db())
    return db.query(Message).filter(Message.session_id == session_id, Message.is_clear == True, Message.created_at >= create_at_gt).all()