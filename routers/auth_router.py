from fastapi import APIRouter,Request

router = APIRouter()

@router.get("/users")
async def get_users():
    return {"message": "List of users"}



