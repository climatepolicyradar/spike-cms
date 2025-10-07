from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime


class Label(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    title: str
    type: str
    document_links: list["DocumentLabelLink"] = Relationship(back_populates="label")


class DocumentLabelLink(SQLModel, table=True):
    document_id: str = Field(foreign_key="document.id", primary_key=True)
    label_id: str = Field(foreign_key="label.id", primary_key=True)
    relationship: str
    timestamp: datetime = Field(default_factory=datetime.now)

    document: "Document" = Relationship(back_populates="label_links")
    label: "Label" = Relationship(back_populates="document_links")


class Document(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    title: str
    label_links: list["DocumentLabelLink"] = Relationship(back_populates="document")
