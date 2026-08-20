from fastapi import APIRouter
comments_router = APIRouter()

@comments_router.get("/")
async def placeholder():
    return {"message": "comments_router placeholder endpoint"}
