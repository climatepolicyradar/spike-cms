from unittest import result

from fastapi import FastAPI, Query
from vespa.application import Vespa

vespa = Vespa(url="http://localhost:8081")


app = FastAPI()


def group_query(group_name: str):
    return f"all(group({group_name}) max(10000) order(-count()) each(output(count())))"


@app.get("/")
def read_root(
    labels: list[str] = Query(default=[]),
    relationships: list[str] = Query(default=[]),
):
    # region: labels
    parsed_labels: list[tuple[str, str]] = []
    for label in labels:
        match label.split(":", 1):
            case [op, title] if op in {"and", "or"}:
                parsed_labels.append((op, title))
            case _:
                parsed_labels.append(("and", label))

    labels_where = ""
    if len(parsed_labels) == 0:
        labels_where = "true"
    elif len(parsed_labels) == 1:
        labels_where = f"label_ids contains '{parsed_labels[0][1]}'"
    elif len(parsed_labels) > 1:
        conditions = [
            (op, f"(label_ids contains '{label}')") for op, label in parsed_labels
        ]

        # The operator doesn't matter on the first
        labels_where = conditions[0][1]
        for op, condition in conditions[1:]:
            labels_where = f"{labels_where} {op} {condition}"
    # endregion

    # region: relationships
    parsed_relationships: list[tuple[str, str]] = []
    for relationship in relationships:
        match relationship.split(":", 1):
            case [op, title] if op in {"and", "or"}:
                parsed_relationships.append((op, title))
            case _:
                parsed_relationships.append(("and", relationship))

    relationships_where = ""
    if len(parsed_relationships) == 0:
        relationships_where = "true"
    elif len(parsed_relationships) == 1:
        relationships_where = (
            f"label_relationships contains '{parsed_relationships[0][1]}'"
        )
    elif len(parsed_relationships) > 1:
        conditions = [
            (op, f"(label_relationships contains '{relationship}')")
            for op, relationship in parsed_relationships
        ]

        # The operator doesn't matter on the first
        relationships_where = conditions[0][1]
        for op, condition in conditions[1:]:
            relationships_where = f"{relationships_where} {op} {condition}"
    # endregion

    
    documents_yql = f"select * from sources * where ({labels_where}) and ({relationships_where}) limit 100;"
    print(f"documents_yql: {documents_yql}")
    documents_result = vespa.query(body={"yql": documents_yql})

    # TODO: this should be controlled via query params
    exclude_groups = ["Case", "Family", "Project"]
    exclude_groups_yql = f"!({" or ".join([f"label_types contains '{group}'" for group in exclude_groups])})"
    groups_yql = f"select * from sources * where ({labels_where}) and {exclude_groups_yql} and ({relationships_where}) limit 100 | {group_query('label_types')} | {group_query('label_titles')} | {group_query('label_ids')} | {group_query('label_relationships')};"
    print(f"groups_yql: {groups_yql}")
    groups_result = vespa.query(body={"yql": groups_yql})

    return {"documents": documents_result, "groups": groups_result}
