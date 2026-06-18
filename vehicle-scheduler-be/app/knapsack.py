from typing import List, Tuple
from pydantic import BaseModel

class Task(BaseModel):
    task_id: str
    duration: int
    impact: int

def knapsack_optimize(tasks: List[Task], capacity: int) -> Tuple[List[Task], int, int]:
    """
    Solves the 0/1 Knapsack problem using Dynamic Programming.
    Weight = duration
    Value = impact
    Capacity = mechanic_hours (assuming integers)
    
    Returns:
        Tuple of (selected_tasks, total_impact, total_duration)
    """
    n = len(tasks)
    
    # dp[i][w] will store the maximum impact using the first i tasks with a capacity of w
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        task = tasks[i - 1]
        weight = task.duration
        value = task.impact
        
        for w in range(1, capacity + 1):
            if weight <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - weight] + value)
            else:
                dp[i][w] = dp[i - 1][w]
                
    # Backtrack to find the selected tasks
    selected_tasks = []
    res = dp[n][capacity]
    w = capacity
    total_duration = 0
    total_impact = res
    
    for i in range(n, 0, -1):
        if res <= 0:
            break
        # If the result comes from the top, the item was not included
        if res == dp[i - 1][w]:
            continue
        else:
            # Item was included
            task = tasks[i - 1]
            selected_tasks.append(task)
            res -= task.impact
            w -= task.duration
            total_duration += task.duration

    selected_tasks.reverse()
    return selected_tasks, total_impact, total_duration
