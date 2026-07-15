"""
Dependency wiring — the ONLY place where concrete use_case classes are bound
to Protocols (ADR-007). Routers depend on these provider functions via
FastAPI's Depends(), never construct a service/repository themselves.
"""
from typing import Annotated

from fastapi import Depends
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
from app.shared.contracts.auth_contract import AuthContractProtocol
from app.shared.contracts.company_contract import CompanyContractProtocol


async def get_auth_usecase(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthUseCase:
    return AuthUseCase(AuthService(AuthRepository(session)))


async def get_company_usecase(
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContractProtocol, Depends(get_auth_usecase)],
) -> CompanyUseCase:
    return CompanyUseCase(CompanyService(CompanyRepository(session)), auth)


async def get_contact_usecase(
    session: Annotated[AsyncSession, Depends(get_session)],
    companies: Annotated[CompanyContractProtocol, Depends(get_company_usecase)],
) -> ContactUseCase:
    return ContactUseCase(ContactService(ContactRepository(session)), companies)
