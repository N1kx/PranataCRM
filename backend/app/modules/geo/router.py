import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.container import get_geo_usecase
from app.modules.geo.exceptions import GeoValidationError
from app.modules.geo.schemas import GeoCityResponse, GeoCountryResponse, GeoStateResponse
from app.modules.geo.use_case import GeoUseCase
from app.shared.contracts.auth_contract import CurrentUser, get_current_user

# Public lookup surface — any authenticated tenant user, feeds the cascading
# location autocompletes on the contact/company forms (issue #26).
router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/countries", response_model=list[GeoCountryResponse])
async def list_countries(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
) -> list[GeoCountryResponse]:
    return await geo.list_countries()


@router.get("/states", response_model=list[GeoStateResponse])
async def list_states(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
    country: str = Query(default=""),
) -> list[GeoStateResponse]:
    country = country.strip()
    if not country:
        raise GeoValidationError("country is required.")
    return await geo.list_states(country)


@router.get("/cities", response_model=list[GeoCityResponse])
async def list_cities(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    geo: Annotated[GeoUseCase, Depends(get_geo_usecase)],
    state: str = Query(default=""),
) -> list[GeoCityResponse]:
    state = state.strip()
    if not state:
        raise GeoValidationError("state is required.")
    try:
        state_id = uuid.UUID(state)
    except ValueError:
        raise GeoValidationError("state must be a valid UUID.")
    return await geo.list_cities(state_id)
