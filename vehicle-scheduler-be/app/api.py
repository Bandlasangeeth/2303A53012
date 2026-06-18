import httpx
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from vehicle_scheduler_be.app.config import settings
from vehicle_scheduler_be.app.knapsack import knapsack_optimize, Task

router = APIRouter()

class OptimizedTaskResponse(BaseModel):
    task_id: str
    duration: int
    impact: int

class SchedulerOptimizationResult(BaseModel):
    selected_tasks: List[OptimizedTaskResponse]
    total_impact: int
    total_duration: int
    optimization_type: str

class SchedulerOptimizationResponse(BaseModel):
    results: List[SchedulerOptimizationResult]

async def fetch_depots() -> int:
    """Fetch depots and return total mechanic hours"""
    headers = {"Authorization": f"Bearer {settings.ACCESS_TOKEN}"} if settings.ACCESS_TOKEN else {}
    url = f"{settings.EVALUATION_API_BASE_URL}/evaluation-service/depots"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            # For testing without real API access, let's gracefully fail or return a default
            raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch depots: {response.text}")
        data = response.json()
        total_capacity = sum(d.get("MechanicHours", 0) for d in data.get("depots", []))
        return total_capacity

async def fetch_vehicles() -> List[Task]:
    """Fetch vehicles and return list of tasks"""
    headers = {"Authorization": f"Bearer {settings.ACCESS_TOKEN}"} if settings.ACCESS_TOKEN else {}
    url = f"{settings.EVALUATION_API_BASE_URL}/evaluation-service/vehicles"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch vehicles: {response.text}")
        data = response.json()
        tasks = []
        for v in data.get("vehicles", []):
            tasks.append(Task(
                task_id=v.get("TaskID"),
                duration=v.get("Duration"),
                impact=v.get("Impact")
            ))
        return tasks

@router.post("/scheduler/optimize", response_model=SchedulerOptimizationResponse)
async def optimize_schedule():
    """
    Optimize vehicle maintenance scheduling based on available mechanic hours.
    Uses Dynamic Programming (0/1 Knapsack) to maximize impact.
    """
    total_capacity = await fetch_depots()
    tasks = await fetch_vehicles()
    
    selected, total_imp, total_dur = knapsack_optimize(tasks, total_capacity)
    
    res = SchedulerOptimizationResult(
        selected_tasks=[OptimizedTaskResponse(task_id=t.task_id, duration=t.duration, impact=t.impact) for t in selected],
        total_impact=total_imp,
        total_duration=total_dur,
        optimization_type="global"
    )
    
    return SchedulerOptimizationResponse(results=[res])
