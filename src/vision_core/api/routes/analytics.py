
from fastapi import APIRouter, Query, Request


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/performance")
def get_performance_history(
    request: Request,
    hours: int = Query(default=24, ge=1, le=720),
    limit: int = Query(default=1000, ge=1, le=10000),
):
    database = request.app.state.database

    snapshots = database.get_performance_snapshots(
        hours=hours,
        limit=limit,
    )

    return {
        "total": len(snapshots),
        "hours": hours,
        "snapshots": snapshots,
    }


@router.get("/drift")
def get_drift_history(
    request: Request,
    hours: int = Query(default=24, ge=1, le=720),
    camera_id: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=1000, ge=1, le=10000),
):
    database = request.app.state.database

    reports = database.get_drift_reports(
        hours=hours,
        camera_id=camera_id,
        limit=limit,
    )

    return {
        "total": len(reports),
        "hours": hours,
        "camera_id": camera_id,
        "reports": reports,
    }
