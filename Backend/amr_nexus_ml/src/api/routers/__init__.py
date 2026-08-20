# src/api/routers/__init__.py
from src.api.routers.health_router import health_router
from src.api.routers.predictions import router as prediction_router
from src.api.routers.analytics import analytics_router
from src.api.routers.alerts import alerts_router
from src.api.routers.reports import reports_router
from src.api.routers.comments import comments_router
from src.api.routers.guidance import guidance_router
from src.api.routers.search import search_router
from src.api.routers.user import user_router
from src.api.routers.ews import ews_router
from .user_router import user_router
