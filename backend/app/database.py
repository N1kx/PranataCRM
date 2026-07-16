from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.shared.base import Base  # noqa: F401 — re-exported for Alembic

# Import all models so SQLAlchemy and Alembic can discover them via Base.metadata.
import app.modules.auth.models  # noqa: F401
import app.modules.licensing.models  # noqa: F401
import app.modules.contacts.models  # noqa: F401
import app.modules.companies.models  # noqa: F401
import app.modules.deals.models  # noqa: F401
import app.modules.ai.models  # noqa: F401
import app.modules.billing.models  # noqa: F401
import app.modules.reporting.models  # noqa: F401
import app.modules.geo.models  # noqa: F401

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
