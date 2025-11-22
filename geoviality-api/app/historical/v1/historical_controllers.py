from typing import Dict, Any, List
from fastapi import HTTPException, status

from app.historical.v1.historical_schemas import DatosHistoricos, DatosHistoricosResponse
from app.historical.v1.historical_queries import (
    find_historical, find_historical_by_id, find_processed_info, find_processed_user
)


def get_historical_data() -> List[Dict[str, Any]]:
    return find_historical()

def get_processed_info(filter: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    return find_processed_info(filter)

def get_point_by_id(_id: str) -> Dict[str, Any]:
    doc = find_historical_by_id(_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point not found")
    return doc

def get_processed_user(username: str, type_: str | None = None) -> List[Dict[str, Any]]:
    return find_processed_user(username, type_)
