from fastapi import FastAPI
from vehicle_scheduler_be.app.api import router

app = FastAPI(
    title="Vehicle Maintenance Scheduler Microservice",
    description="Campus Evaluation Backend Phase 1",
    version="1.0.0"
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
