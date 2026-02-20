from typing import Optional

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_optional_current_user
from app.models.user import User
from app.schemas.environment import EnvironmentInformationResponse

router = APIRouter(prefix="/environment", tags=["Environment"])


@router.get("/information", response_model=EnvironmentInformationResponse)
def environment_information(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> EnvironmentInformationResponse:
    return EnvironmentInformationResponse(user=current_user)
