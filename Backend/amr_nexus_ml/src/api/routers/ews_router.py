from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from src.api.deps import get_db
from src.utils.logger import logger

print("✅ ews_router is being imported!")

ews_router = APIRouter()

# Only a ping route for debugging
@ews_router.get("/ping")
async def ping():
    return {"status": "ews_router is alive"}
