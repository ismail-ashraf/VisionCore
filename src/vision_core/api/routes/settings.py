
from fastapi import APIRouter, HTTPException, Request

from vision_core.api.settings_schema import RuntimeSettingsUpdate


router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)


@router.get("")
def get_settings(request: Request):
    runtime_settings = request.app.state.runtime_settings

    return runtime_settings.get_settings()


@router.patch("")
def update_settings(
    payload: RuntimeSettingsUpdate,
    request: Request,
):
    runtime_settings = request.app.state.runtime_settings

    updates = payload.model_dump(exclude_unset=True)

    # Ignore fields explicitly set to None.
    updates = {
        key: value
        for key, value in updates.items()
        if value is not None
    }

    try:
        return runtime_settings.update_settings(**updates)

    except (ValueError, TypeError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )
