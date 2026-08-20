from fastapi import APIRouter
reports_router = APIRouter()

@reports_router.get("/")
async def placeholder():
    return {"message": "reports_router placeholder endpoint"}
