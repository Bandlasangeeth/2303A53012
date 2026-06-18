import httpx
import os
from typing import Literal

LayerKind = Literal["backend", "frontend"]
SeverityKind = Literal["debug", "info", "warn", "error", "fatal"]
ModuleKind = Literal[
    "cache", "controller", "cron_job", "db", "domain",
    "handler", "repository", "route", "service",
    "api", "component", "hook", "page", "state", "style",
    "auth", "config", "middleware", "utils"
]

def RecordEvent(
    layer: LayerKind,
    severity: SeverityKind,
    module: ModuleKind,
    text: str
) -> None:

    host = os.getenv("EVALUATION_API_BASE_URL", "http://4.224.186.213")
    auth_token = os.getenv("ACCESS_TOKEN", "")

    endpoint = f"{host}/evaluation-service/logs"
    request_headers = {
        "Content-Type": "application/json"
    }

    if auth_token:
        request_headers["Authorization"] = f"Bearer {auth_token}"

    body = {
        "stack": layer,
        "level": severity,
        "package": module,
        "message": text
    }

    try:
        result = httpx.post(
            endpoint,
            json=body,
            headers=request_headers,
            timeout=5.0
        )
        result.raise_for_status()
    except Exception as exc:
        print(f"Logging failed: {exc}")


async def async_RecordEvent(
    layer: LayerKind,
    severity: SeverityKind,
    module: ModuleKind,
    text: str
) -> None:
    """
    Asynchronous version of the reusable logging function.
    """

    host = os.getenv("EVALUATION_API_BASE_URL", "http://4.224.186.213")
    auth_token = os.getenv("ACCESS_TOKEN", "")

    endpoint = f"{host}/evaluation-service/logs"
    request_headers = {
        "Content-Type": "application/json"
    }

    if auth_token:
        request_headers["Authorization"] = f"Bearer {auth_token}"

    body = {
        "stack": layer,
        "level": severity,
        "package": module,
        "message": text
    }

    try:
        async with httpx.AsyncClient() as client:
            result = await client.post(
                endpoint,
                json=body,
                headers=request_headers,
                timeout=5.0
            )
            result.raise_for_status()
    except Exception as exc:
        print(f"Async logging failed: {exc}")
