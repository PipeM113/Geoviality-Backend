from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any

class SidewalksDB(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
