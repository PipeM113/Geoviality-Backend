from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.auth.v1.auth_controllers import get_current_active_user
from app.users.v1.users_schemas import UserCreate, UserUpdate, UserResponse
from app.users.v1.users_controllers import (
    create_user_to_mongodb, read_user_from_mongodb, update_user_to_mongodb,
    delete_user_from_mongodb, read_all_users_from_mongodb
)

router = APIRouter(
    prefix="/v1/users",
    tags=["users"],
)

@router.post("/create")
async def create_user(u: UserCreate) -> dict:
    ok = create_user_to_mongodb(u)
    return {"created": ok}

@router.get("/read/{username}", response_model=UserResponse | None)
async def read_user(username: str, _=Depends(get_current_active_user)):
    return read_user_from_mongodb(username)

@router.put("/update/{username}")
async def update_user(username: str, u: UserUpdate, _=Depends(get_current_active_user)) -> dict:
    ok = update_user_to_mongodb(username, u)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or unchanged")
    return {"updated": True}

@router.delete("/delete/{username}")
async def delete_user(username: str, _=Depends(get_current_active_user)) -> dict:
    ok = delete_user_from_mongodb(username)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"deleted": True}

@router.get("/read_all", response_model=List[UserResponse])
async def read_all(_=Depends(get_current_active_user)):
    return read_all_users_from_mongodb()
