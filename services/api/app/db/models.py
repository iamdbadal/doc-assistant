import os
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    tenant_id = Column(String, ForeignKey("tenants.id"))

    tenant = relationship("Tenant", back_populates="users")


# Production Async Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:@localhost:5432/doc_assistant",
)

# create_async_engine utilizes asyncpg
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True only for local debugging
    pool_pre_ping=True,  # Tests connections before using them (prevents stale connection drops)
    pool_size=5,  # Standard connection pool size
    max_overflow=10,
)

# AsyncSessionLocal manages the lifecycle of the connections
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Critical: prevents lazy-load errors after commits in async flows
)


# Dependency injection for FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
