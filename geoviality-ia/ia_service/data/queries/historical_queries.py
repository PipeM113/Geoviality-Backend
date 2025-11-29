# ia_service/data/queries/historical_queries.py
from ia_service.data.database import db
from ia_service.domain.models import GeoJson
from typing import Dict


def procesar_dato_hist(punto: GeoJson) -> None:
    """
    Cementerio reactivable:
    Procesa un punto y actualiza la colección de datos históricos 'historical_data'.
    """
    fecha = punto.properties.date.isoformat()
    tipos = punto.properties.type

    anio = int(fecha[:4])
    mes = fecha[5:7]
    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    nombre_mes = meses[int(mes) - 1]

    incrementos: Dict[str, int] = {
        f"irregularidadesPorTipo.{tipo}": 1 for tipo in tipos
    }
    incrementos["irregularidadesTotales"] = len(tipos)

    db.historical_data.update_one(
        {"anio": anio, "mes": nombre_mes},
        {
            "$inc": incrementos,
        },
    )
