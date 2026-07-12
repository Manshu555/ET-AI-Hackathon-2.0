"""
Critical Path Analysis — forward/backward pass over task dependencies.
Identifies which tasks lie on the critical path and would impact the project finish date if delayed.
"""
import json
from datetime import date, timedelta
from typing import Dict, List, Optional, Set


def build_dependency_graph(tasks: List[dict]) -> Dict[str, List[str]]:
    """Build adjacency list: task_id -> list of successor task IDs."""
    # Forward: task A depends on B means B -> A (B is predecessor of A)
    predecessors: Dict[str, List[str]] = {}
    successors: Dict[str, List[str]] = {}

    for task in tasks:
        tid = task["id"]
        predecessors[tid] = []
        successors.setdefault(tid, [])
        deps = task.get("dependencies")
        if deps:
            try:
                dep_ids = json.loads(deps)
                for dep_id in dep_ids:
                    predecessors[tid].append(dep_id)
                    successors.setdefault(dep_id, []).append(tid)
            except (json.JSONDecodeError, TypeError):
                pass
    return predecessors, successors


def compute_critical_path(tasks: List[dict]) -> Set[str]:
    """
    Simplified critical-path method:
    - Forward pass: compute earliest start/finish
    - Backward pass: compute latest start/finish
    - Tasks with zero float are on the critical path
    """
    if not tasks:
        return set()

    task_map = {t["id"]: t for t in tasks}
    predecessors, successors = build_dependency_graph(tasks)

    # Duration in days for each task
    durations = {}
    for t in tasks:
        if t.get("planned_start") and t.get("planned_end"):
            d = (t["planned_end"] - t["planned_start"]).days
            durations[t["id"]] = max(d, 1)
        elif t.get("duration_days"):
            durations[t["id"]] = t["duration_days"]
        else:
            durations[t["id"]] = 1

    # ── Forward pass ──
    earliest_start = {}
    earliest_finish = {}

    # Topological order via Kahn's algorithm
    in_degree = {tid: len(predecessors.get(tid, [])) for tid in task_map}
    queue = [tid for tid, deg in in_degree.items() if deg == 0]
    topo_order = []

    while queue:
        tid = queue.pop(0)
        topo_order.append(tid)
        for succ in successors.get(tid, []):
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)

    # Handle cycles gracefully (add remaining tasks)
    for tid in task_map:
        if tid not in topo_order:
            topo_order.append(tid)

    for tid in topo_order:
        preds = predecessors.get(tid, [])
        if preds:
            es = max(earliest_finish.get(p, 0) for p in preds if p in earliest_finish) if any(p in earliest_finish for p in preds) else 0
        else:
            es = 0
        earliest_start[tid] = es
        earliest_finish[tid] = es + durations.get(tid, 1)

    # ── Backward pass ──
    project_end = max(earliest_finish.values()) if earliest_finish else 0
    latest_finish = {}
    latest_start = {}

    for tid in reversed(topo_order):
        succs = successors.get(tid, [])
        if succs:
            lf = min(latest_start.get(s, project_end) for s in succs if s in latest_start) if any(s in latest_start for s in succs) else project_end
        else:
            lf = project_end
        latest_finish[tid] = lf
        latest_start[tid] = lf - durations.get(tid, 1)

    # ── Identify critical path (zero total float) ──
    critical = set()
    for tid in task_map:
        total_float = latest_start.get(tid, 0) - earliest_start.get(tid, 0)
        if total_float <= 0:
            critical.add(tid)

    return critical


def get_downstream_tasks(task_id: str, tasks: List[dict]) -> List[str]:
    """Return names of tasks that depend on the given task (direct successors)."""
    _, successors = build_dependency_graph(tasks)
    task_map = {t["id"]: t for t in tasks}

    succ_ids = successors.get(task_id, [])
    return [task_map[sid]["task_name"] for sid in succ_ids if sid in task_map]
