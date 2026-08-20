from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

health_router = APIRouter()

@health_router.get("/health", status_code=status.HTTP_200_OK)
async def check_system_health() -> JSONResponse:
    return JSONResponse(
        content={
            "status": "healthy",
            "services": {"http_engine": "online", "socket_stream": "ready"},
        }
    )