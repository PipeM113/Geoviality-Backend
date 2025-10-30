from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

##################################################################################
# MODELOS PARA DATOS HISTORICOS
##################################################################################

# Modelo para los tipos de irregularidades
class IrregularidadesPorTipo(BaseModel):
    hoyo: Optional[int] = 0
    grieta: Optional[int] = 0
    cocodrilo: Optional[int] = 0
    hoyo_con_agua: Optional[int] = Field(0, alias="hoyo con agua")
    longitudinal: Optional[int] = 0
    transversal: Optional[int] = 0
    lomo_de_toro: Optional[int] = Field(0, alias="lomo de toro")

# Modelo para las coordenadas de los puntos
class Coordenadas(BaseModel):
    lat: float
    lng: float

# Modelo para los datos históricos
class DatosHistoricos(BaseModel):
    anio: int 
    mes: str 
    irregularidadesTotales: int
    irregularidadesReparadas: int
    irregularidadesPorTipo: IrregularidadesPorTipo
    coordenadas : list[Coordenadas]

# Modelo para la respuesta de los datos históricos
class DatosHistoricosResponse(BaseModel):
    info: list[DatosHistoricos]