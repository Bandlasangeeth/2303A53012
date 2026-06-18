import httpx
from typing import List
from fastapi import APIRouter, HTTPException

from notification_app_be.app.config import settings
from notification_app_be.app.priority_inbox import (
    get_top_k_notifications,
    Notification,
)

notification_router = APIRouter()


async def load_notifications() -> List[dict]:
    """Retrieve notification data from the evaluation endpoint."""

    auth_headers = (
        {"Authorization": f"Bearer {settings.ACCESS_TOKEN}"}
        if settings.ACCESS_TOKEN
        else {}
    )

    endpoint_url = (
        f"{settings.EVALUATION_API_BASE_URL}/evaluation-service/notifications"
    )

    async with httpx.AsyncClient() as session:
        result = await session.get(endpoint_url, headers=auth_headers)

        if result.status_code != 200:
            raise HTTPException(
                status_code=result.status_code,
                detail=f"Failed to fetch notifications: {result.text}",
            )

        payload = result.json()
        return payload.get("notifications", [])


@notification_router.get(
    "/notifications/priority",
    response_model=List[Notification]
)
async def fetch_priority_notifications(limit: int = 10):
    """
    Retrieve the highest-priority unread notifications.

    Ranking considers notification category and recency.
    Complexity: O(N log K)
    """

    notifications = await load_notifications()
    prioritized_items = get_top_k_notifications(
        notifications,
        k=limit
    )

    return prioritized_items
