import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthCheck(BaseModel):
    status: str
    timestamp: str
    version: str
    checks: dict[str, str]


@router.get("/health", response_model=HealthCheck)
async def health():
    checks = await _run_checks()
    all_healthy = all(v == "ok" for v in checks.values())
    return HealthCheck(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
        checks=checks,
    )


@router.get("/health/ready")
async def readiness():
    checks = await _run_checks()
    if all(v == "ok" for v in checks.values()):
        return {"ready": True}
    return {"ready": False, "checks": checks}


@router.get("/health/live")
async def liveness():
    return {"alive": True}


async def _run_checks() -> dict[str, str]:
    results = {}
    results["api"] = "ok"
    # Database and Redis checks will be added when those services are connected
    return results
