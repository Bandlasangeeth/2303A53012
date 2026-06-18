from fastapi import FastAPI
from notification_app_be.app.api import router

app = FastAPI(
    title="Priority Inbox Microservice",
    description="Campus Evaluation Backend Phase 3",
    version="1.0.0"
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
