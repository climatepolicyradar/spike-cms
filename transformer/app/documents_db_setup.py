from sqlmodel import SQLModel, create_engine, text
from document_models import Label, Document, DocumentLabelLink


documents_engine = create_engine(
    "postgresql://documents:documents@localhost:5433/documents",
    echo=True,
)

SQLModel.metadata.create_all(documents_engine)
