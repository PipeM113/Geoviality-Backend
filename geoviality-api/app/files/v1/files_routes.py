import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.auth.v1.auth_controllers import get_current_active_user
from app.files.v1.files_controllers import receive_image_from_IA, send_to_queue
from app.files.v1.files_schemas import PhotoQueue, PhotoSave

router = APIRouter(
    prefix="/v1/files",
    tags=["files"],
)


@router.post("/upload/image")
async def upload_image(
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    date: str = Form(...),
    modo: str = Form(...),
    current_user=Depends(get_current_active_user),
):
    """Sube una imagen original y la envía a la cola para que la procese la IA."""
    _id = __import__("uuid").uuid4().hex
    data = PhotoQueue(
        id=_id,
        # Se mantiene el formato actual: bytes -> string 1:1 (latin1).
        # Si en el futuro migras a base64, cámbialo de forma consistente
        # con el consumidor de la cola.
        image=(await image.read()).decode("latin1"),
        latitude=latitude,
        longitude=longitude,
        date=datetime.fromisoformat(date),
        modo=modo,
        user=current_user.username,
    )
    ok = send_to_queue(data)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Queue unavailable"
        )
    return {"id": _id}


@router.post(
    "/from-ia",
    summary="Recibe imágenes procesadas desde la IA",
)
async def from_ia(photo: PhotoSave):
    """Endpoint llamado por el microservicio de IA para guardar la imagen procesada.

    - No requiere autenticación por ahora.
    - Recibe un JSON compatible con `PhotoSend` de la IA.
    """
    receive_image_from_IA(photo)
    return {"status": "ok", "id": photo.id}


@router.get("/download/get_image/{image_id}")
async def download_image(
    image_id: str, _=Depends(get_current_active_user)
) -> FileResponse:
    file_path = os.path.join(os.getcwd(), "services", "imgs", f"{image_id}.jpg")
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return FileResponse(file_path)


@router.get("/download/get_pre_image/{image_id}")
async def download_pre_image(image_id: str, _=Depends(get_current_active_user)):
    file_path = os.path.join(os.getcwd(), "services", "pre_pro", image_id)
    return FileResponse(file_path)
