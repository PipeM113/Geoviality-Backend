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

class UserDocument(Document):
    meta = {"collection": "users"}
    username = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    nombre = StringField(required=True)
    apellido = StringField(required=True)
    date_register = DateTimeField(required=True)
    disabled = BooleanField(default=False)
    tipo = IntField(required=True)
    password = StringField(required=True)