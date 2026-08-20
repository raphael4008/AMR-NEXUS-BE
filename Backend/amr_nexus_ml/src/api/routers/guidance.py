from fastapi import APIRouter
guidance_router = APIRouter()

@guidance_router.get("/")
async def placeholder():
    return {"message": "guidance_router placeholder endpoint"}
