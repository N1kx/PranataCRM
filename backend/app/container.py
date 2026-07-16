"""
Dependency wiring — the ONLY place where concrete use_case classes are bound
to Protocols (ADR-007). Routers depend on these provider functions via
FastAPI's Depends(), never construct a service/repository themselves.
"""
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db as get_session
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.auth.use_case import AuthUseCase
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.service import CompanyService
from app.modules.companies.use_case import CompanyUseCase
from app.modules.contacts.repository import ContactRepository
from app.modules.contacts.service import ContactService
from app.modules.contacts.use_case import ContactUseCase
from app.modules.geo.cache import GeoCache
from app.modules.geo.repository import GeoRepository
from app.modules.geo.service import GeoService
from app.modules.geo.use_case import GeoUseCase
from app.shared.contracts.auth_contract import AuthContractProtocol
from app.shared.contracts.company_contract import CompanyContractProtocol
from app.shared.contracts.geo_contract import GeoContractProtocol
from app.shared.redis import get_redis


async def get_auth_usecase(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthUseCase:
    return AuthUseCase(AuthService(AuthRepository(session)))


async def get_geo_usecase(
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> GeoUseCase:
    return GeoUseCase(GeoService(GeoRepository(session), GeoCache(redis)))


async def get_company_usecase(
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContractProtocol, Depends(get_auth_usecase)],
    geo: Annotated[GeoContractProtocol, Depends(get_geo_usecase)],
) -> CompanyUseCase:
    return CompanyUseCase(CompanyService(CompanyRepository(session)), auth, geo)


async def get_contact_usecase(
    session: Annotated[AsyncSession, Depends(get_session)],
    companies: Annotated[CompanyContractProtocol, Depends(get_company_usecase)],
    auth: Annotated[AuthContractProtocol, Depends(get_auth_usecase)],
    geo: Annotated[GeoContractProtocol, Depends(get_geo_usecase)],
) -> ContactUseCase:
    return ContactUseCase(ContactService(ContactRepository(session)), companies, auth, geo)
