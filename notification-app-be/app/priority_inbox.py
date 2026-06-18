import heapq
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class Notification(BaseModel):
    id: str
    type: str
    message: str
    timestamp: str

# Base priority scores
PRIORITY_MAP = {
    "Placement": 100,
    "Result": 80,
    "Exam Alert": 60,
    "Event": 40
}

def parse_timestamp(ts: str) -> float:
    """Parses timestamp string to unix time."""
    try:
        # Example format: "2026-04-22 17:51:30"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return dt.timestamp()
    except ValueError:
        return 0.0

def calculate_score(notification: Notification) -> float:
    """
    Calculates the final score based on priority and recency.
    To ensure priority takes precedence but recency acts as a strong tie-breaker,
    we scale the priority score significantly.
    final_score = (priority_score * 10^10) + recency_score
    """
    priority_score = PRIORITY_MAP.get(notification.type, 0)
    recency_score = parse_timestamp(notification.timestamp)
    return (priority_score * 10_000_000_000) + recency_score

class PriorityInboxTracker:
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.min_heap = []
        
    def add_notification(self, notification: Notification):
        """
        Maintains the top K elements efficiently in O(log K) time per insertion.
        """
        score = calculate_score(notification)
        
        # We push a tuple of (score, notification_id, notification) into the min-heap.
        # Since it's a min-heap, the notification with the LOWEST score is at the root `self.min_heap[0]`.
        if len(self.min_heap) < self.max_size:
            heapq.heappush(self.min_heap, (score, notification.id, notification))
        else:
            # If the new notification's score is greater than the lowest score in the heap
            if score > self.min_heap[0][0]:
                heapq.heappushpop(self.min_heap, (score, notification.id, notification))

    def get_top_notifications(self) -> List[Notification]:
        """
        Returns the top notifications sorted in descending order of their scores.
        Time complexity: O(K log K) where K is max_size.
        """
        # Sort descending (highest score first)
        sorted_items = sorted(self.min_heap, key=lambda x: x[0], reverse=True)
        return [item[2] for item in sorted_items]

def get_top_k_notifications(notifications_data: List[Dict[str, Any]], k: int = 10) -> List[Notification]:
    """
    Processes a batch of notifications and returns the top K.
    Overall Time Complexity: O(N log K)
    """
    tracker = PriorityInboxTracker(max_size=k)
    for data in notifications_data:
        notif = Notification(
            id=data.get("ID", ""),
            type=data.get("Type", ""),
            message=data.get("Message", ""),
            timestamp=data.get("Timestamp", "")
        )
        tracker.add_notification(notif)
        
    return tracker.get_top_notifications()
