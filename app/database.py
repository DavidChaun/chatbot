import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv("DB_URL")
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 3600))
engine = create_engine(
    DB_URL,
    pool_recycle=DB_POOL_RECYCLE,
    pool_pre_ping=True,
    # 应该要比executor的数量稍微大一点
    max_overflow=36,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


PG_VDB_URL = os.getenv(
    "POSTGRES_SERVER_URL",
    "postgresql+psycopg2://postgres:123456@127.0.0.1:5432/docker",
)
vdb_engine = create_engine(PG_VDB_URL)
VdbSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=vdb_engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def vector_db_session():
    vdb = VdbSessionLocal()
    try:
        yield vdb
    finally:
        vdb.close()


def save_entity(entity: Base):
    db = next(get_db())
    db.add(entity)
    db.commit()
    db.refresh(entity)


def delete_entity(id_):
    db = next(get_db())
    db.delete(id_)
    db.commit()
