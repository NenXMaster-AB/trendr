from __future__ import annotations
from collections import deque
from typing import Any


def _get_nodes(defn: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = defn.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("Workflow must define a non-empty 'nodes' list")
    return nodes


def _get_edges(defn: dict[str, Any]) -> list[dict[str, Any]]:
    edges = defn.get("edges")
    if edges is None:
        return []
    if not isinstance(edges, list):
        raise ValueError("Workflow 'edges' must be a list")
    return edges


def validate_workflow(
    defn: dict[str, Any],
    *,
    supported_tasks: set[str] | None = None,
) -> None:
    nodes = _get_nodes(defn)
    edges = _get_edges(defn)

    node_ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("Each workflow node must be an object")
        node_id = node.get("id")
        node_type = node.get("type")
        task_name = node.get("task")
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("Each workflow node requires a non-empty string 'id'")
        if node_id in node_ids:
            raise ValueError(f"Duplicate workflow node id '{node_id}'")
        if node_type != "task":
            raise ValueError(f"Unsupported node type '{node_type}' for node '{node_id}'")
        if not isinstance(task_name, str) or not task_name.strip():
            raise ValueError(f"Node '{node_id}' requires a non-empty string 'task'")
        if supported_tasks is not None and task_name not in supported_tasks:
            raise ValueError(
                f"Node '{node_id}' uses unsupported task '{task_name}'. "
                f"Supported tasks: {sorted(supported_tasks)}"
            )
        node_ids.add(node_id)

    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("Each workflow edge must be an object")
        source = edge.get("from")
        target = edge.get("to")
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError("Workflow edges require string 'from' and 'to'")
        if source not in node_ids or target not in node_ids:
            raise ValueError(
                f"Workflow edge references unknown node '{source}' -> '{target}'"
            )

    # Also validates there are no dependency cycles.
    topological_order(defn)


def topological_order(defn: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = _get_nodes(defn)
    edges = _get_edges(defn)

    node_map = {str(node["id"]): node for node in nodes}
    indegree = {node_id: 0 for node_id in node_map}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_map}

    for edge in edges:
        source = str(edge["from"])
        target = str(edge["to"])
        outgoing[source].append(target)
        indegree[target] += 1

    queue = deque(
        node_id for node_id in (str(node["id"]) for node in nodes) if indegree[node_id] == 0
    )
    ordered_ids: list[str] = []
    while queue:
        node_id = queue.popleft()
        ordered_ids.append(node_id)
        for child in outgoing[node_id]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    if len(ordered_ids) != len(nodes):
        raise ValueError("Workflow contains a dependency cycle")

    return [node_map[node_id] for node_id in ordered_ids]
