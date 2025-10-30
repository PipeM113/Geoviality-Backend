from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from mongoengine.errors import MongoEngineException
from .event_model import PhotoDocument

class EventQueryError(Exception):
    """Clase base para errores de consulta de eventos."""
    pass

def find_processed_photo_by_id(photo_id: str) -> Optional[PhotoDocument]:
    try:
        return PhotoDocument.objects(id=photo_id).first()
    except MongoEngineException as e:
        raise EventQueryError(f"Error al buscar foto por ID: {e}")

def update_processed_photo(photo_id: str, update_fields: Dict[str, Any]) -> bool:
    if not update_fields:
        return True
    try:
        update_ops = {f"set__{field.replace('.', '__')}": value for field, value in update_fields.items()}
        result = PhotoDocument.objects(id=photo_id).update_one(**update_ops)
        return result > 0
    except MongoEngineException as e:
        raise EventQueryError(f"Error al actualizar la foto: {e}")

def delete_processed_photo(photo_id: str) -> bool:
    try:
        result = PhotoDocument.objects(id=photo_id).delete()
        return result > 0
    except MongoEngineException as e:
        raise EventQueryError(f"Error al eliminar la foto: {e}")

def list_processed_photos(filter_query: Optional[Dict[str, Any]] = None) -> List[PhotoDocument]:
    try:
        return list(PhotoDocument.objects(filter_query or {}))
    except MongoEngineException as e:
        raise EventQueryError(f"Error al listar las fotos: {e}")

def list_processed_photos_by_date(start_date: datetime, end_date: datetime) -> List[PhotoDocument]:
    try:
        return list(PhotoDocument.objects(properties__date__gte=start_date, properties__date__lt=end_date))
    except MongoEngineException as e:
        raise EventQueryError(f"Error al listar fotos por fecha: {e}")
