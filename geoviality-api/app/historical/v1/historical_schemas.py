from pydantic import BaseModel, ConfigDict
from typing import List, Any

class DatosHistoricos(BaseModel):
    model_config = ConfigDict(extra="allow")

class DatosHistoricosResponse(BaseModel):
    data: List[DatosHistoricos]
