from fastapi import APIRouter, Request, Depends, status
from fastapi.exceptions import HTTPException
from typing import List

from controllers import (
    create_user_to_mongodb,
    read_user_from_mongodb,
    update_user_to_mongodb,
    delete_user_from_mongodb,
    get_current_active_user,
    read_all_users_from_mongodb,
)
from users_schemas import UserCreate, UserSol, User, UserResponse, UserUpdate

users_router = APIRouter(prefix="/v1/users", tags=["users"])
##################################################################################
# RUTAS CRUD
##################################################################################

# Create User
@users_router.post("/user/create", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    try:
        res = create_user_to_mongodb(user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear el usuario.") from exc
    if not res:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    return {"message": "User created successfully"}

# Read User
@users_router.get("/user/read/{username}")
async def read_user(request: Request, requester: User = Depends(get_current_active_user)) -> UserResponse:
    username = request.path_params['username']
    try:
        user = read_user_from_mongodb(username)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener el usuario.") from exc
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# Update User
@users_router.put("/user/update/{username}")
async def update_user(request: Request, user: UserSol, requester: User = Depends(get_current_active_user)):
    username = request.path_params['username']
    updatedUser = UserUpdate(**user.model_dump(), username=username)
    try:
        res = update_user_to_mongodb(updatedUser)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar el usuario.") from exc
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User updated successfully"}

# Delete User
@users_router.delete("/user/delete/{username}")
async def delete_user(request: Request, requester: User = Depends(get_current_active_user)):
    username = request.path_params['username']
    try:
        res = delete_user_from_mongodb(username)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al eliminar el usuario.") from exc
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User deleted successfully"}

# Read All Users
@users_router.get("/user/read_all")
async def read_users(requester: User = Depends(get_current_active_user)) -> List[UserResponse]:
    try:
        users = read_all_users_from_mongodb()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al listar usuarios.") from exc
    return users