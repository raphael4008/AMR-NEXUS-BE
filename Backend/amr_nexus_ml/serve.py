import logging
import sys
from typing import Dict, Any, List
import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.app import app as fastapi_app
from src.utils.logger import logger
from src.database import SessionLocal
from src.services.prediction_service import AMRPredictionService
from src.utils.config import config

CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174"]
SERVER_HOST: str = "0.0.0.0"
SERVER_PORT: int = 8000

sio: socketio.AsyncServer = socketio.AsyncServer(
    async_mode="asgi", 
    cors_allowed_origins=CORS_ORIGINS
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

combined_app: socketio.ASGIApp = socketio.ASGIApp(
    socketio_server=sio, 
    other_asgi_app=fastapi_app
)
fastapi_app.sio = sio


@sio.event
async def connect(sid: str, environ: Dict[str, Any]) -> None:
    logger.info(f"SocketIO client connected securely. Session ID: {sid}")


@sio.event
async def disconnect(sid: str) -> None:
    logger.info(f"SocketIO client disconnected cleanly. Session ID: {sid}")


@sio.event
async def stream_isolate_data(sid: str, data: Dict[str, Any]) -> None:
    logger.info(f"Real-time pipeline payload received via socket channel from: {sid}")
    db_session = SessionLocal()
    try:
        service = AMRPredictionService(db_session)
        processed_records = service.process_and_persist(data)
        await sio.emit("prediction_complete", processed_records, to=sid)
    except Exception as e:
        logger.error(f"Failed to process streamed socket payload: {str(e)}")
        await sio.emit("prediction_failed", {"error": str(e)}, to=sid)
    finally:
        db_session.close()


if __name__ == "__main__":
    try:
        logger.info(f"Starting ASGI enterprise server deployment layer on {SERVER_HOST}:{SERVER_PORT}")
        uvicorn.run(
            "src.main:combined_app", 
            host=SERVER_HOST, 
            port=SERVER_PORT, 
            workers=1,
            log_level="info"
        )
    except Exception as e:
        logger.critical(f"Server deployment engine suffered unhandled boot crash: {str(e)}")
        sys.exit(1)
