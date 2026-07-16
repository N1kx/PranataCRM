import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import get_geo_usecase
from app.database import get_db as get_session
from app.modules.auth.exceptions import PermissionDenied
from app.modules.geo.schemas import (
    GeoCityCreate,
    GeoCityResponse,
    GeoCityUpdate,
    GeoCountryResponse,
    GeoCountryUpdate,
    GeoStateCreate,
    GeoStateResponse,
    GeoStateUpdate,
)
from app.modules.geo.use_case import GeoUseCase
from app.shared.contracts.auth_contract import CurrentUser, get_current_user
from app.shared.types import SuiteRole

# Admin maintenance surface for geo reference data (issue #26): states/cities
# are admin-editable because administrative regions change (e.g. Indonesian
# province splits); countries are ISO-fixed, so only rename/activate.
router = APIRouter(prefix="/admin/geo", tags=["geo-admin"])


def _require_admin(current_user: CurrentUser) -> None:
    # TODO(platform-admin): this codebase has no dedicated cross-tenant
    # platform-admin role yet — ADR-010's suite_role is per-tenant
    # (tenant_owner / tenant_admin / member), not a platform-wide identity.
    # Geo reference data is GLOBAL (shared by every tenant), so gating this
    # on a per-tenant role is an interim measure only: any tenant_owner in
    # ANY tenant can currently edit data every other tenant reads. Replace
    # this check with a real platform-admin role/claim before relying on it
    # for anything beyond a small set of trusted early operators.
    if current_user.suite_role != SuiteRole.TENANT_OWNER:
        raise PermissionDenied()


@router.patch("/countries/{code}", response_model=GeoCountryResponse)
async def update_country(
    code: str,
    payload: GeoCountryUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
) -> GeoCountryResponse:
    _require_admin(current_user)
    result = await geo.update_country(code, payload)
    await session.commit()
    return result


@router.post("/states", response_model=GeoStateResponse, status_code=201)
async def create_state(
    payload: GeoStateCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
) -> GeoStateResponse:
    _require_admin(current_user)
    result = await geo.create_state(payload)
    await session.commit()
    return result


@router.patch("/states/{state_id}", response_model=GeoStateResponse)
async def update_state(
    state_id: uuid.UUID,
    payload: GeoStateUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
) -> GeoStateResponse:
    _require_admin(current_user)
    result = await geo.update_state(state_id, payload)
    await session.commit()
    return result


@router.delete("/states/{state_id}", status_code=200)
async def delete_state(
    state_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
) -> dict:
    _require_admin(current_user)
    await geo.delete_state(state_id)
    await session.commit()
    return {"message": "State deleted successfully."}


@router.post("/cities", response_model=GeoCityResponse, status_code=201)
async def create_city(
    payload: GeoCityCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
) -> GeoCityResponse:
    _require_admin(current_user)
    result = await geo.create_city(payload)
    await session.commit()
    return result


@router.patch("/cities/{city_id}", response_model=GeoCityResponse)
async def update_city(
    city_id: uuid.UUID,
    payload: GeoCityUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
) -> GeoCityResponse:
    _require_admin(current_user)
    result = await geo.update_city(city_id, payload)
    await session.commit()
    return result


@router.delete("/cities/{city_id}", status_code=200)
async def delete_city(
    city_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
) -> dict:
    _require_admin(current_user)
    await geo.delete_city(city_id)
    await session.commit()
    return {"message": "City deleted successfully."}
