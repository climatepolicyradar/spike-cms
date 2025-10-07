import os

from document_models import Document, DocumentLabelLink, Label
from models import PhysicalDocument
from navigator_transformer import NavigatorTransformer
from pydantic import BaseModel
from sqlmodel import Session, create_engine, delete, select

navigator_engine = create_engine(
    "postgresql://navigator_admin:navigator_admin@localhost:5432/navigator_admin"
)
documents_engine = create_engine(
    "postgresql://documents:documents@localhost:5433/documents"
)


class VespaPutDocument(BaseModel):
    put: str
    fields: dict


def main():
    out_dir = ".data"
    os.makedirs(out_dir, exist_ok=True)
    navigator_transformer = NavigatorTransformer()

    with Session(navigator_engine) as navigator_session:
        results = navigator_session.exec(
            select(PhysicalDocument).where(
                # GOTCHA: we have empty documents in the DB
                PhysicalDocument.source_url != ""
                # GOTCHA: we have documents that aren't part of a family
                # trunk-ignore(ruff/E711)
                and PhysicalDocument.family_document != None
            )
        ).all()

        feed_file = os.path.join(out_dir, "documents.jsonl")
        with Session(documents_engine) as documents_session:
            with open(feed_file, "w", encoding="utf-8") as f:
                for row in results:
                    documents_model = navigator_transformer.transform(row)
                    vespa_document = VespaPutDocument(
                        # GOTCHA: we can do better IDing than this
                        put=f"id:production:documents::{documents_model.id}",
                        fields=documents_model.model_dump(),
                    )
                    f.write(vespa_document.model_dump_json() + "\n")

                    if False:
                        # clear the old label relationships
                        documents_session.exec(
                            delete(DocumentLabelLink).where(
                                DocumentLabelLink.document_id == documents_model.id
                            )
                        )
                        documents_session.flush()

                        # upsert the labels
                        for label_relationship in documents_model.labels:
                            documents_session.merge(
                                Label(
                                    id=label_relationship.label.id,
                                    title=label_relationship.label.title,
                                    type=label_relationship.label.type,
                                )
                            )
                        documents_session.flush()

                        # upsert the document (without relationships)
                        document = Document(
                            id=documents_model.id, title=documents_model.title
                        )
                        documents_session.merge(document)
                        documents_session.flush()

                        # add new relationships
                        for label_relationship in documents_model.labels:
                            link = DocumentLabelLink(
                                document_id=documents_model.id,
                                label_id=label_relationship.label.id,
                                relationship=label_relationship.relationship,
                                timestamp=label_relationship.timestamp,
                            )
                            documents_session.merge(link)

                        documents_session.commit()

    print(f"Wrote docs to {feed_file}")


if __name__ == "__main__":
    main()
    print("done")  # quick visual
