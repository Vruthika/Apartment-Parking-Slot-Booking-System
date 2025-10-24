
from fastapi import WebSocket, WebSocketDisconnect, Request, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import random

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")
clients = {} 
admin_socket = None

def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@router.get("/client", response_class=HTMLResponse)
async def client_page(request: Request, username: str):
    color = random_color()
    return templates.TemplateResponse("client.html", {"request": request, "username": username, "color": color})


@router.get("/admin-link")
async def get_admin_link(request: Request):
    base_url = str(request.base_url).rstrip("/")
    link = f"{base_url}/admin"
    return JSONResponse({"chat_url": link})

@router.get("/client-link")
async def get_client_link(request: Request, username: str):
    base_url = str(request.base_url).rstrip("/")
    color = random_color()
    link = f"{base_url}/client?username={username}&color={color}"
    return JSONResponse({"chat_url": link})


@router.websocket("/ws/{role}")
async def websocket_endpoint(websocket: WebSocket, role: str):
    global admin_socket
    await websocket.accept()

    if role.startswith("client_"):
        username = role.split("_", 1)[1]
        color = random_color()
        clients[username] = {"socket": websocket, "color": color}
        print(f"✅ Client {username} connected ({color})")
        if admin_socket:
            await admin_socket.send_text(f"📩 {username} connected.")
    elif role == "admin":
        admin_socket = websocket
        print("✅ Admin connected")
        await admin_socket.send_text("🟢 Admin connected.")

    try:
        while True:
            data = await websocket.receive_text()

            if role == "admin":
                if ":" in data:
                    target, message = data.split(":", 1)
                    target = target.strip()
                    if target in clients:
                        color = clients[target]["color"]
                        await clients[target]["socket"].send_text(f"Admin:{message.strip()}")
                    else:
                        await admin_socket.send_text(f"⚠️ User '{target}' not found.")
                else:
                    await admin_socket.send_text("⚠️ Use format: username: message")

            elif role.startswith("client_"):
                username = role.split("_", 1)[1]
                color = clients[username]["color"]
                if admin_socket:
                    await admin_socket.send_text(f"<b style='color:{color}'>{username}</b>: {data}")
                await websocket.send_text(f"You: {data}")

    except WebSocketDisconnect:
        if role.startswith("client_"):
            username = role.split("_", 1)[1]
            clients.pop(username, None)
            print(f"❌ {username} disconnected")
            if admin_socket:
                await admin_socket.send_text(f"⚠️ {username} disconnected.")
        elif role == "admin":
            admin_socket = None
            print("❌ Admin disconnected")

