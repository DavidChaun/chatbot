from app.database import Base, get_db
from sqlalchemy import Column, String, Text, JSON, Integer, BigInteger, Boolean


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    channel = Column(String(255), index=True, comment="从哪里来的用户")
    type_ = Column(String(255), index=True, comment="用户类型。AI | USER", name="type")
    eid = Column(String(255), index=True, comment="用户唯一标识")
    nickname = Column(String(255), index=True, comment="昵称")
    created_at = Column(BigInteger, unique=False, index=False)
