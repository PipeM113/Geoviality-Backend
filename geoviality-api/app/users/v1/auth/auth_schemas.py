from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

##################################################################################
# MODELOS PARA AUTENTICACIÓN
##################################################################################

# Modelo de Token
class Token(BaseModel):
    access_token : str
    token_type: str

# Modelo de TokenData (lo que lleva el token)
class TokenData(BaseModel):
    username: str | None = None


# Modelo de usuario para login
class UserLogin(BaseModel):
    username: str
    password: str
