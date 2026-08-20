from fastapi import APIRouter
search_router = APIRouter()

@search_router.get("/")
async def placeholder():
    return {"message": "search_router placeholder endpoint"}
