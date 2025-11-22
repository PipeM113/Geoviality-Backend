from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserPublic(BaseModel):
    model_config = ConfigDict(extra="allow")  # permite campos adicionales sin romper compat
    username: str
    # Puedes agregar aquí más campos públicos si en tu BD existen (email, roles, etc.)
