from __future__ import annotations

import pytest

from trendr_api.workflows.engine import topological_order, validate_workflow


def test_validate_workflow_and_topological_order():
    definition = {
        "nodes": [
            {"id": "n1", "type": "task", "task": "ingest_youtube"},
            {"id": "n2", "type": "task", "task": "generate_posts"},
        ],
        "edges": [{"from": "n1", "to": "n2"}],
    }

    validate_workflow(definition, supported_tasks={"ingest_youtube", "generate_posts"})
    ordered = topological_order(definition)
    assert [node["id"] for node in ordered] == ["n1", "n2"]


def test_validate_workflow_rejects_cycle():
    definition = {
        "nodes": [
            {"id": "a", "type": "task", "task": "ingest_youtube"},
            {"id": "b", "type": "task", "task": "generate_posts"},
        ],
        "edges": [
            {"from": "a", "to": "b"},
            {"from": "b", "to": "a"},
        ],
    }

    with pytest.raises(ValueError, match="cycle"):
        validate_workflow(definition, supported_tasks={"ingest_youtube", "generate_posts"})


def test_validate_workflow_rejects_unsupported_task():
    definition = {
        "nodes": [
            {"id": "n1", "type": "task", "task": "generate_thumbnail"},
        ],
        "edges": [],
    }

    with pytest.raises(ValueError, match="unsupported task"):
        validate_workflow(definition, supported_tasks={"ingest_youtube", "generate_posts"})
