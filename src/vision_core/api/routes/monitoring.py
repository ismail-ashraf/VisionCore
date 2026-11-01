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

@router.get("/system")
def get_system_metrics(request: Request):

    stream_manager = request.app.state.stream_manager

    return stream_manager.get_inference_metrics()

@router.get("/cameras/health")
def get_camera_health(request: Request):
    stream_manager = request.app.state.stream_manager

    cameras = stream_manager.get_camera_health()

    return {
        "total_cameras": len(cameras),
        "cameras": cameras,
    }

@router.get("/errors")
def get_system_errors(request: Request):
    stream_manager = request.app.state.stream_manager

    metrics = stream_manager.get_inference_metrics()

    return metrics["errors"]