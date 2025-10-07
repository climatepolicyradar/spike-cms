from datetime import datetime
from pydantic import BaseModel


class Label(BaseModel):
    id: str
    title: str
    type: str


class LabelRelationship(BaseModel):
    label: Label
    relationship: str
    timestamp: datetime


class LabelledDocument(BaseModel):
    id: str
    title: str
    labels: list[LabelRelationship]
    collections: list[LabelRelationship]