from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.auth import router as auth_router
from src.api.backbone import router as backbone_router
from src.api.intelligence import router as intelligence_router
from src.api.users import router as users_router
from src.api.reports import router as reports_router
from src.api.decision_support import router as decision_support_router

app = FastAPI(title=settings.PROJECT_NAME, version="2.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes prefixed by API_V1_STR (e.g., /api/v1)
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(backbone_router, prefix=settings.API_V1_STR)
app.include_router(intelligence_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(decision_support_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AMR-Nexus API", "version": "2.2.0"}

@app.on_event("startup")
def print_routes():
    print("--- REGISTERED ROUTES ---")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"Path: {route.path} | Methods: {route.methods}")
    print("-------------------------")