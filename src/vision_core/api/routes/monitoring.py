from fastapi import APIRouter, Request, HTTPException

router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
)


@router.get("/drift")
def get_all_drift_insights(request: Request):

    stream_manager = request.app.state.stream_manager

    insights = stream_manager.get_drift_insights()

    return {
        "total_cameras": len(insights),
        "cameras": insights,
    }


@router.get("/drift/{camera_id}")
def get_camera_drift_insights(
    camera_id: str,
    request: Request,
):

    stream_manager = request.app.state.stream_manager

    try:
        insights = stream_manager.get_drift_insights(
            camera_id=camera_id
        )

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Camera {camera_id} not found",
        )

    return insights[0]