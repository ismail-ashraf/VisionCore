from fastapi import APIRouter, Request, HTTPException

from vision_core.api.schema import CameraCreate

router = APIRouter()


@router.post("/cameras", status_code=201)
def add_camera(camera: CameraCreate,request: Request):
    stream_manager = request.app.state.stream_manager

    try:
        stream_manager.add_camera(
            camera_id=camera.camera_id,
            source_url=camera.source_url,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message": "Camera added successfully",
        "camera_id": camera.camera_id,
    }


@router.delete("/cameras/{camera_id}")
def delete_camera(
    camera_id: str,
    request: Request,
):
    stream_manager = request.app.state.stream_manager

    try:
        stream_manager.stop_camera(camera_id)

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Camera {camera_id} not found",
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    return {
        "message": "Camera stopped successfully",
        "camera_id": camera_id,
    }

@router.get("/cameras")
def get_cameras(request: Request):
    stream_manager = request.app.state.stream_manager

    cameras = stream_manager.list_cameras()

    return {
        "total": len(cameras),
        "cameras": cameras,
    }