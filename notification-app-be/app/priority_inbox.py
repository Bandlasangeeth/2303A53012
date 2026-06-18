import heapq
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class AlertRecord(BaseModel):
    id: str
    category: str
    content: str
    created_at: str


WEIGHT_TABLE = {
    "Placement": 100,
    "Result": 80,
    "Exam Alert": 60,
    "Event": 40,
}


def convert_to_unix(time_value: str) -> float:
    try:
        parsed_time = datetime.strptime(
            time_value,
            "%Y-%m-%d %H:%M:%S"
        )
        return parsed_time.timestamp()
    except ValueError:
        return 0.0


def compute_rank(alert: AlertRecord) -> float:
    category_weight = WEIGHT_TABLE.get(alert.category, 0)
    time_weight = convert_to_unix(alert.created_at)

    return (category_weight * 10_000_000_000) + time_weight


class NotificationRanker:
    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.heap_storage = []

    def insert(self, alert: AlertRecord) -> None:
        rank_value = compute_rank(alert)

        entry = (
            rank_value,
            alert.id,
            alert
        )

        if len(self.heap_storage) < self.capacity:
            heapq.heappush(
                self.heap_storage,
                entry
            )
        else:
            lowest_rank = self.heap_storage[0][0]

            if rank_value > lowest_rank:
                heapq.heappushpop(
                    self.heap_storage,
                    entry
                )

    def get_ranked_items(self) -> List[AlertRecord]:
        ordered_entries = sorted(
            self.heap_storage,
            key=lambda record: record[0],
            reverse=True
        )

        return [record[2] for record in ordered_entries]


def select_top_notifications(
    records: List[Dict[str, Any]],
    limit: int = 10
) -> List[AlertRecord]:
    ranker = NotificationRanker(capacity=limit)

    for item in records:
        alert = AlertRecord(
            id=item.get("ID", ""),
            category=item.get("Type", ""),
            content=item.get("Message", ""),
            created_at=item.get("Timestamp", ""),
        )

        ranker.insert(alert)

    return ranker.get_ranked_items()
