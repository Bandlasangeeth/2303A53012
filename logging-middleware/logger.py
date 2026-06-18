import httpx
import os
from typing import Literal

StackType = Literal["backend", "frontend"]
LevelType = Literal["debug", "info", "warn", "error", "fatal"]
PackageType = Literal[
    "cache", "controller", "cron_job", "db", "domain", 
    "handler", "repository", "route", "service",  
    "api", "component", "hook", "page", "state", "style",  
    "auth", "config", "middleware", "utils"  
]

def Log(stack: StackType, level: LevelType, package: PackageType, message: str) -> None:
    
    base_url = os.getenv("EVALUATION_API_BASE_URL", "http://4.224.186.213")
    token = os.getenv("ACCESS_TOKEN", "")
    
    url = f"{base_url}/evaluation-service/logs"
    headers = {
        "Content-Type": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }
    
    try:
        
        response = httpx.post(url, json=payload, headers=headers, timeout=5.0)
        response.raise_for_status()
    except Exception as e:
        print(f"Logging failed: {e}")

async def async_Log(stack: StackType, level: LevelType, package: PackageType, message: str) -> None:
    """
    Asynchronous version of the reusable logging function.
    """
    base_url = os.getenv("EVALUATION_API_BASE_URL", "http://4.224.186.213")
    token = os.getenv("ACCESS_TOKEN", "")
    
    url = f"{base_url}/evaluation-service/logs"
    headers = {
        "Content-Type": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=5.0)
            response.raise_for_status()
    except Exception as e:
        print(f"Async logging failed: {e}")
