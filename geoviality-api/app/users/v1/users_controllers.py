from typing import List
from fastapi import HTTPException, status
from app.users.v1.users_schemas import UserCreate, UserUpdate, UserResponse
from app.users.v1.users_queries import (
    create_user, read_user, update_user, delete_user, read_all_users
)
from app.auth.v1.auth_controllers import hash_password

def create_user_to_mongodb(payload: UserCreate) -> bool:
    if read_user(payload.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    doc = payload.model_dump()
    doc["password"] = hash_password(doc["password"])
    res = create_user(doc)
    return bool(res.inserted_id)

def read_user_from_mongodb(username: str) -> UserResponse | None:
    doc = read_user(username)
    return UserResponse(**doc) if doc else None

def update_user_to_mongodb(username: str, changes: UserUpdate) -> bool:
    doc = changes.model_dump(exclude_unset=True)
    if "password" in doc and doc["password"]:
        doc["password"] = hash_password(doc["password"])
    res = update_user(username, doc)
    return res.modified_count > 0

def delete_user_from_mongodb(username: str) -> bool:
    res = delete_user(username)
    return res.deleted_count > 0

def read_all_users_from_mongodb() -> List[UserResponse]:
    return [UserResponse(**d) for d in read_all_users()]
