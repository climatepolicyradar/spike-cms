from datetime import datetime
from functools import wraps
from typing import Callable, Protocol, TypeVar

from models import PhysicalDocument
from pydantic import BaseModel


def rule(mermaid: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Store metadata on the function
        wrapper.mermaid = mermaid

        return wrapper

    return decorator


TransformerIn = TypeVar("TransformerIn")


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


Rule = Callable[[TransformerIn], list[LabelRelationship]]


class LabelledDocumentTransformer(Protocol[TransformerIn]):
    @rule(mermaid="")
    def transform(self, data_in: TransformerIn) -> LabelledDocument: ...

    rules: list[Rule]


class NavigatorTransformer:
    corporate_finance_projects = ["AF", "CIF", "GCF", "GEF"]
    corporate_finance_project_names = {
        "AF": "Adaptation Fund",
        "CIF": "Climate Investment Fund",
        "GCF": "Green Climate Fund",
        "GEF": "Global Environment Facility",
    }

    @rule(
        mermaid="PhysicalDocument --> FamilyDocument --> Family --> .name --> CollectionTypeLabel.title"
    )
    def event(self, data_in: PhysicalDocument) -> list[LabelRelationship]:
        return []

    @rule(
        mermaid="PhysicalDocument --> FamilyDocument --> Family --> .name --> CollectionTypeLabel.title"
    )
    def family(self, data_in: PhysicalDocument) -> list[LabelRelationship]:
        corpus_type_name = data_in.family_document.family.corpus.corpus_type.name
        labels = []
        if corpus_type_name in self.corporate_finance_projects:
            labels.append(
                LabelRelationship(
                    label=Label(
                        id=f"Project/{data_in.family_document.family.import_id}",
                        title=data_in.family_document.family.title,
                        type="Project",
                    ),
                    relationship="part_of",
                    timestamp=datetime.now().isoformat(),
                )
            )

        if corpus_type_name == "Litigation":
            labels.append(
                LabelRelationship(
                    label=Label(
                        id=f"Case/{data_in.family_document.family.import_id}",
                        title=data_in.family_document.family.title,
                        type="Case",
                    ),
                    relationship="part_of",
                    timestamp=datetime.now().isoformat(),
                )
            )

        labels.append(
            LabelRelationship(
                label=Label(
                    id=f"Family/{data_in.family_document.family.import_id}",
                    title=data_in.family_document.family.name,
                    type="Family",
                ),
                relationship="part_of",
                timestamp=datetime.now().isoformat(),
            )
        )

        return labels

    @rule(
        mermaid="PhysicalDocument --> FamilyDocument --> Family --> Corpus --> CorpusType -- .name --> GenreLabel.title"
    )
    def genre(self, data_in: PhysicalDocument) -> list[LabelRelationship]:
        corpus_type_name = data_in.family_document.family.corpus.corpus_type.name

        if corpus_type_name in self.corporate_finance_projects:
            return [
                LabelRelationship(
                    label=Label(
                        id="Genre/Corporate Finance Project",
                        title="Corporate Finance Project",
                        type="Genre",
                    ),
                    relationship="is",
                    timestamp=datetime.now().isoformat(),
                ),
                LabelRelationship(
                    label=Label(
                        id=f"MultilateralClimateFund/{self.corporate_finance_project_names[corpus_type_name]}",
                        title=self.corporate_finance_project_names[corpus_type_name],
                        type="MultilateralClimateFund",
                    ),
                    relationship="part_of",
                    timestamp=datetime.now().isoformat(),
                ),
            ]

        return [
            LabelRelationship(
                label=Label(
                    id=f"Genre/{corpus_type_name}",
                    title=corpus_type_name,
                    type="Genre",
                ),
                relationship="is",
                timestamp=datetime.now().isoformat(),
            )
        ]

    @rule(
        mermaid="PhysicalDocument --> FamilyDocument -- .valid_metadata.type --> DocumentTypeLabel.title"
    )
    def document_type(self, data_in: PhysicalDocument) -> list[LabelRelationship]:
        valid_metadata_document_types = data_in.family_document.valid_metadata.get(
            "type", []
        )

        document_types = []
        for valid_metadata_document_type in valid_metadata_document_types:
            """
            Most values are singular, but we have used CSVs as singular values to immitate
            multi values previously. This unwinds that hack.
            e.g.
                Nationally Determined Contribution,National Communication
                Pre-Session Document,Synthesis Report
                National Communication,Biennial Report
                Nationally Determined Contribution,National Communication
                National Adaptation Plan,Adaptation Communication
                Publication,Report
            """
            doc_types = valid_metadata_document_type.split(",")
            for doc_type in doc_types:
                document_types.append(
                    LabelRelationship(
                        label=Label(
                            id=f"DocumentType/{doc_type}",
                            title=doc_type,
                            type="DocumentType",
                        ),
                        relationship="is",
                        timestamp=datetime.now().isoformat(),
                    )
                )

        return document_types

    @rule(
        mermaid="PhysicalDocument --> FamilyDocument --> Family --> Geography -- .value --> GeographyLabel.title"
    )
    def geography(self, data_in: PhysicalDocument) -> list[LabelRelationship]:
        geographies = []
        for geography in data_in.family_document.family.unparsed_geographies:
            geographies.append(
                LabelRelationship(
                    label=Label(
                        id=f"Geography/{geography.value}",
                        title=geography.value,
                        type="Geography",
                    ),
                    relationship="is",
                    timestamp=datetime.now().isoformat(),
                )
            )

        return geographies

    @rule(
        mermaid="PhysicalDocument --> FamilyDocument --> Family --> FamilyMetadata -- .author --> AuthorLabel.title"
    )
    def author(self, data_in: PhysicalDocument) -> list[LabelRelationship]:
        authors = []
        for author in data_in.family_document.family.unparsed_metadata.value.get(
            "author", []
        ):
            authors.append(
                LabelRelationship(
                    label=Label(
                        id=f"Agent/{author}",
                        title=author,
                        type="Agent",
                    ),
                    relationship="author",
                    timestamp=datetime.now().isoformat(),
                )
            )

        return authors

    rules = [genre, document_type, geography, author]

    def transform(self, data_in: PhysicalDocument) -> LabelledDocument:
        labels = []
        for rule in self.rules:
            labels.extend(rule(self, data_in))

        return LabelledDocument(id=str(data_in.id), title=data_in.title, labels=labels)


def generate_mermaid_diagram(transformer: LabelledDocumentTransformer) -> str:
    mermaid_rules = [getattr(rule, "mermaid", "") for rule in transformer.rules]
    mermaid_rules_with_tabs = [f"    {rule}" for rule in mermaid_rules if rule]

    initialise_mermaid = [
        "flowchart LR",
        "    PhysicalDocument",
        "    FamilyDocument",
        "    Family",
        "    Corpus",
        "    CorpusType",
    ]
    chart = "\n".join(initialise_mermaid) + "\n" + "\n".join(mermaid_rules_with_tabs)
    return chart


print(generate_mermaid_diagram(transformer=NavigatorTransformer()))
