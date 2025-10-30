from datetime import datetime
from typing import List, Optional

from mongoengine import (
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    DynamicField,
    FloatField,
    IntField,
    ListField,
    StringField,
    DateTimeField,
    BooleanField,
)

class PropertiesDocument(EmbeddedDocument):
    id = StringField(required=True)
    images = ListField(StringField(), default=list)
    date = DateTimeField(required=True)
    type_ = DynamicField(required=True, db_field="type")  # admite str o lista
    modo = StringField(required=True)
    user = StringField(required=True)
    repair_at = DateTimeField(default=None)
    estado = IntField(required=True)
    observaciones = StringField(required=True)
    last_update = DateTimeField(required=True)


class GeometryDocument(EmbeddedDocument):
    type_ = StringField(default="Point", db_field="type")
    coordinates = ListField(FloatField(), min_length=2, required=True)


class PhotoDocument(Document):
    meta = {"collection": "processed_geojson"}
    id = StringField(primary_key=True)
    type_ = StringField(default="Feature")
    geometry = EmbeddedDocumentField(GeometryDocument, required=True)
    properties = EmbeddedDocumentField(PropertiesDocument, required=True)

class SidewalkDocument(Document):
    meta = {"collection": "sidewalks"}
    id = StringField(primary_key=True)
    type_ = StringField(default="Feature")
    geometry = EmbeddedDocumentField(GeometryDocument, required=True)
    properties = EmbeddedDocumentField(PropertiesDocument, required=True)