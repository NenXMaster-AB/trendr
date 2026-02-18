from __future__ import annotations
from typing import Dict, Any

# Skeleton workflow runner.
# In production: validate DAG, support branching/conditions, retries, idempotency.
# Wire to Celery tasks or Temporal for robustness.

def validate_workflow(defn: Dict[str, Any]) -> None:
    if "nodes" not in defn or "edges" not in defn:
        raise ValueError("Invalid workflow definition")
