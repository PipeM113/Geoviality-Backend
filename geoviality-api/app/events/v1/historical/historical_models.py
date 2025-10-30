from mongoengine import Document, EmbeddedDocument, fields

class IrregularidadesPorTipo(EmbeddedDocument):
    hoyo = fields.IntField(default=0)
    grieta = fields.IntField(default=0)
    cocodrilo = fields.IntField(default=0)
    hoyo_con_agua = fields.IntField(default=0, db_field="hoyo con agua")
    longitudinal = fields.IntField(default=0)
    transversal = fields.IntField(default=0)
    lomo_de_toro = fields.IntField(default=0, db_field="lomo de toro")

class Coordenadas(EmbeddedDocument):
    lat = fields.FloatField(required=True)
    lng = fields.FloatField(required=True)

class DatosHistoricos(Document):
    anio = fields.IntField(required=True)
    mes = fields.StringField(required=True)
    irregularidadesTotales = fields.IntField(required=True)
    irregularidadesReparadas = fields.IntField(required=True)
    irregularidadesPorTipo = fields.EmbeddedDocumentField(IrregularidadesPorTipo)
    coordenadas = fields.ListField(fields.EmbeddedDocumentField(Coordenadas))

    meta = {
        'collection': 'processed_geojson',
        'allow_inheritance': True,
        'strict': False,
    }
