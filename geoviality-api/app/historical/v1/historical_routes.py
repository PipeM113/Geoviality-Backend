from fastapi import APIRouter, Depends
from typing import Dict, Any, List

from app.auth.v1.auth_controllers import get_current_active_user
from app.historical.v1.historical_controllers import (
    get_historical_data, get_processed_info, get_point_by_id, get_processed_user
)

router = APIRouter(
    prefix="/v1/historical",
    tags=["historical"],
)

@router.get("/data")
async def historical_data(_=Depends(get_current_active_user)):
    return get_historical_data()

@router.get("/processed_info")
async def processed_info(_=Depends(get_current_active_user)):
    return get_processed_info()

@router.get("/processed_info/{type}")
async def processed_info_by_type(type: str, _=Depends(get_current_active_user)):
    return get_processed_info({"type": type})

@router.get("/processed_info/date/{year}/{month}")
async def processed_info_by_date(year: int, month: int, _=Depends(get_current_active_user)):
    return get_processed_info({"year": year, "month": month})

@router.get("/point/{id}")
async def get_point(id: str, _=Depends(get_current_active_user)):
    return get_point_by_id(id)

@router.get("/processed_user/{username}")
async def processed_user(username: str, _=Depends(get_current_active_user)):
    return get_processed_user(username)

@router.get("/processed_user/{username}/{type}")
async def processed_user_type(username: str, type: str, _=Depends(get_current_active_user)):
    return get_processed_user(username, type)
