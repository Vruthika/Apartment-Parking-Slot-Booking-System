from app.websocket.manager import manager
import json

async def send_notification_to_resident(user_id: int, title: str, message: str, type: str):
    notification_data = {
        "type": "notification",
        "title": title,
        "message": message,
        "notification_type": type
    }
    await manager.send_personal_message(json.dumps(notification_data), user_id)

async def send_visitor_approval_request(user_id: int, visitor_data: dict):
    approval_request = {
        "type": "visitor_approval_request",
        "visitor_data": visitor_data
    }
    await manager.send_personal_message(json.dumps(approval_request), user_id)