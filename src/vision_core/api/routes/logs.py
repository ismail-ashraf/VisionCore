
from fastapi import APIRouter, Query, Request
from typing import Optional

router = APIRouter(
    prefix="/logs",
    tags=["System Logs"],
)


@router.get("")
def get_system_logs(
    request: Request,
    hours: int = Query(default=24, ge=1, le=720),
    level: Optional[str] = Query(default=None),
    camera_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=10000),
):
    database = request.app.state.database

    logs = database.get_system_logs(
        hours=hours,
        level=level,
        camera_id=camera_id,
        search=search,
        limit=limit,
    )

    return {
        "total": len(logs),
        "filters": {
            "hours": hours,
            "level": level,
            "camera_id": camera_id,
            "search": search,
        },
        "logs": logs,
    }
