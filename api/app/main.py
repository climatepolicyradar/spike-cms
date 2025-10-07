from typing import Generic, TypeVar

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, create_engine, delete, select

from .document_models import Document, DocumentLabelLink, Label
from .models import LabelledDocument

APIDataType = TypeVar("APIDataType")


class APIListResponse(BaseModel, Generic[APIDataType]):
    data: list[APIDataType]
    total: int
    page: int
    page_size: int


class APIItemResponse(BaseModel, Generic[APIDataType]):
    data: APIDataType


documents_engine = create_engine(
    "postgresql://documents:documents@localhost:5433/documents"
)


def get_session():
    with Session(documents_engine) as session:
        yield session


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/documents", response_model=APIListResponse[Document])
def read_documents(*, session: Session = Depends(get_session)):
    documents = session.exec(select(Document).offset(0).limit(10)).all()

    return APIListResponse(
        data=list(documents),
        total=len(documents),
        page=1,
        page_size=len(documents),
    )


@app.get("/documents/{id}", response_model=APIItemResponse[Document])
def read_document(*, session: Session = Depends(get_session), id: str):
    document = session.exec(select(Document).where(Document.id == id)).one_or_none()

    return APIItemResponse(
        data=document,
    )


@app.put("/documents/{id}", response_model=APIItemResponse[Document])
def put_document(
    *, session: Session = Depends(get_session), document: LabelledDocument
):
    # clear the old label relationships
    session.exec(
        delete(DocumentLabelLink).where(DocumentLabelLink.document_id == document.id)
    )
    session.flush()

    # upsert the labels
    for label_relationship in document.labels:
        session.merge(
            Label(
                id=label_relationship.label.id,
                title=label_relationship.label.title,
                type=label_relationship.label.type,
            )
        )
    session.flush()

    # upsert the document (without relationships)
    upsert_document = Document(id=document.id, title=document.title)
    session.merge(upsert_document)
    session.flush()

    # add new relationships
    for label_relationship in document.labels:
        link = DocumentLabelLink(
            document_id=upsert_document.id,
            label_id=label_relationship.label.id,
            relationship=label_relationship.relationship,
            timestamp=label_relationship.timestamp,
        )
        session.merge(link)

    session.commit()
    return APIItemResponse(
        data=document,
    )
