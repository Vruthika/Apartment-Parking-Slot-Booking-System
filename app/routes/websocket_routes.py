from fastapi import APIRouter, WebSocket

router = APIRouter()

# WebSocket routes will be implemented later
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Connected")
    await websocket.close()