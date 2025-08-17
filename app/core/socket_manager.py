from fastapi import WebSocket
from typing import Dict
from app.repositories import base_repository
from app.db.collections import Notification as NotificationCollection
from app.models.user import Notification

class UserNotificationManager:
    """
    UserNotificationManager handles the logic for connecting, disconnecting, and sending notifications.
    """
    
    def __init__(self):
        """
        Initializes the UserNotificationManager with a dictionary to keep track of active_connections.
        """
        self.active_connections: Dict[str, WebSocket] = {}

    async def manage_connection(self, user_id: str, websocket: WebSocket):
        """
        This method manages the websocket connection with user.

        Args:
            user_id (str): The unique identifier of the user.
            websocket (WebSocket): The WebSocket object used to communicate with the user in frontend.
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def manage_disconnection(self, user_id: str, websocket: WebSocket):
        """
        Handles the disconnection of a user connection. 

        Args:
            user_id (str): The unique identifier of the user.
        """
        self.active_connections.pop(user_id, None)

    async def send_notification(self, user_id: str, notification_obj: dict):
        """
        Sending notification to the user. 

        Args:
            user_id (str): The unique identifier of the user.
            notification_obj (dict): The dictionary which contains notification details
        """
        if user_id in self.active_connections:
            notification_id = await base_repository.store_document(NotificationCollection(), notification_obj)
            notification = await base_repository.get_document_data(NotificationCollection(), notification_id)
            notification_serialized_data = Notification(**notification).model_dump()

            await self.active_connections[user_id].send_json(notification_serialized_data)
