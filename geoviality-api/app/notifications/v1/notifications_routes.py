from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from app.notifications.v1.notifications_controllers import (
    event_generator1, event_generator2, active_connections
)

router = APIRouter(
    prefix="/v1/notifications",
    tags=["notifications"],
)

@router.get("/data/events/last_point/web")
async def sse_points():
    return StreamingResponse(event_generator1(), media_type="text/event-stream")

@router.get("/data/events/last_point/movil")
async def sse_movil():
    return StreamingResponse(event_generator2(), media_type="text/event-stream")

@router.websocket("/data/events/last_point")
async def websocket_points(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text() # Mantener la conexión abierta
    except WebSocketDisconnect:
        active_connections.remove(websocket)
