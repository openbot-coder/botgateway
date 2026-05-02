import time
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from ..api.auth import verify_management_token

router = APIRouter()


def get_memory_info():
    if not PSUTIL_AVAILABLE:
        raise RuntimeError("psutil not available")
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "percent": memory.percent,
    }


def get_cpu_info():
    if not PSUTIL_AVAILABLE:
        raise RuntimeError("psutil not available")
    return {
        "percent": psutil.cpu_percent(interval=0.1),
        "count": psutil.cpu_count(logical=True),
        "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
    }


def get_disk_info():
    if not PSUTIL_AVAILABLE:
        raise RuntimeError("psutil not available")
    disk = psutil.disk_usage("/")
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent,
    }


def get_process_info():
    if not PSUTIL_AVAILABLE:
        raise RuntimeError("psutil not available")
    process = psutil.Process()
    return {
        "pid": process.pid,
        "name": process.name(),
        "memory_percent": process.memory_percent(),
        "cpu_percent": process.cpu_percent(),
    }


def get_network_info():
    if not PSUTIL_AVAILABLE:
        raise RuntimeError("psutil not available")
    return {"connections": len(psutil.net_connections())}


def get_uptime():
    if not PSUTIL_AVAILABLE:
        raise RuntimeError("psutil not available")
    return time.time() - psutil.boot_time()


@router.get("/health")
async def health_check(request: Request):
    auth_result = verify_management_token(request)
    if isinstance(auth_result, JSONResponse):
        return auth_result

    try:
        memory = get_memory_info()
        cpu = get_cpu_info()
        disk = get_disk_info()
        network = get_network_info()
        process = get_process_info()
        uptime = get_uptime()
    except RuntimeError:
        raise HTTPException(
            status_code=500,
            detail="Internal server error: required dependencies not available"
        )

    routes: list[dict[str, str]] = []
    for route in request.app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
            })

    return {
        "status": "healthy",
        "server_time": datetime.utcnow().isoformat() + "Z",
        "memory": memory,
        "cpu": cpu,
        "disk": disk,
        "network": network,
        "process": process,
        "uptime": uptime,
        "endpoints": routes,
    }
