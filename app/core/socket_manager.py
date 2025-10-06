from fastapi import WebSocket
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Notification
from app.repositories.base_repository import create_record
from app.core.logging import setup_logger

logger = setup_logger()

class UserNotificationManager:
    """
    UserNotificationManager handles the logic for connecting, disconnecting, and sending notifications.
    """
    
    def __init__(self) -> None:
        """
        Initializes the UserNotificationManager with a dictionary to keep track of active_connections.
        """
        self.active_connections: Dict[str, WebSocket] = {}

    async def manage_connection(self, user_id: str, websocket: WebSocket) -> None:
        """
        This method manages the websocket connection with user.

        Args:
            user_id (str): The unique identifier of the user.
            websocket (WebSocket): The WebSocket object used to communicate with the user in frontend.
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def manage_disconnection(self, user_id: str, websocket: WebSocket) -> None:
        """
        Handles the disconnection of a user connection. 

        Args:
            user_id (str): The unique identifier of the user.
        """
        self.active_connections.pop(user_id, None)

    async def send_notification(self, session: AsyncSession, user_id: str, notification_obj: Dict[str, Any]) -> None:
        """
        Sending notification to the user. 

        Args:
            session (AsyncSession): SQLAlchemy async session
            user_id (str): The unique identifier of the user.
            notification_obj (dict): The dictionary which contains notification details
        """
        if user_id in self.active_connections:
            try:
                # Create notification in database
                notification = await create_record(session, Notification, notification_obj)
                if notification:
                    # Convert to API response format
                    notification_data = {
                        "id": notification.id,
                        "user_id": notification.user_id,
                        "organization_id": notification.organization_id,
                        "type": notification.type,
                        "message": notification.message,
                        "is_seen": notification.is_seen,
                        "created_at": notification.created_at,
                        "updated_at": notification.updated_at
                    }
                    
                    # Send to WebSocket client
                    await self.active_connections[user_id].send_json(notification_data)
                else:
                    logger.error(f"Failed to create notification for user {user_id}")
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}")
