from fastapi import APIRouter
user_router = APIRouter()

@user_router.get("/")
async def placeholder():
    return {"message": "user_router placeholder endpoint"}
