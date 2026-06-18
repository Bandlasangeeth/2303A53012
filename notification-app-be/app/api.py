import httpx
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from notification_app_be.app.config import settings
from notification_app_be.app.priority_inbox import get_top_k_notifications, Notification

router = APIRouter()

async def fetch_notifications() -> List[dict]:
    """Fetch notifications from the evaluation service."""
    headers = {"Authorization": f"Bearer {settings.ACCESS_TOKEN}"} if settings.ACCESS_TOKEN else {}
    url = f"{settings.EVALUATION_API_BASE_URL}/evaluation-service/notifications"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch notifications: {response.text}")
        data = response.json()
        return data.get("notifications", [])

@router.get("/notifications/priority", response_model=List[Notification])
async def get_priority_inbox(n: int = 10):
    """
    Returns the top 'n' most important unread notifications.
    Priority is determined by Notification Type and Recency.
    Complexity: O(N log K)
    """
    raw_notifications = await fetch_notifications()
    top_notifications = get_top_k_notifications(raw_notifications, k=n)
    return top_notifications
