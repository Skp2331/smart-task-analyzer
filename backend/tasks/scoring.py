from datetime import datetime, date
from typing import List, Dict, Tuple, Any

TODAY = date.today()


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def compute_urgency(due_date: date | None) -> float:
    """
    Returns urgency in [0, 1].
    - Past due -> 1.0
    - Due today -> 1.0
    - 1–30 days -> linearly decreasing to 0
    - Missing / far future -> 0
    """
    if not due_date:
        return 0.0

    delta = (due_date - TODAY).days
    if delta <= 0:
        return 1.0
    if delta >= 30:
        return 0.0
    return (30 - delta) / 30.0


def normalize_importance(importance: int | None) -> float:
    if importance is None:
        return 0.0
    return max(0.0, min(importance / 10.0, 1.0))


def normalize_effort(hours: float | int | None, max_hours: float = 12.0) -> float:
    """
    Normalize effort to [0, 1]. Higher = more effort.
    """
    if hours is None:
        return 0.5  # neutral if missing
    hours = float(hours)
    if hours <= 0:
        return 0.0
    return min(hours / max_hours, 1.0)


def build_dependency_graph(tasks: List[Dict[str, Any]]) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    """
    Returns:
      graph: task_id -> list of dependency task_ids
      dependents_count: task_id -> how many tasks depend on it
    """
    graph: Dict[str, List[str]] = {}
    dependents_count: Dict[str, int] = {}

    for idx, t in enumerate(tasks):
        tid = str(t.get("id", idx))
        deps = [str(d) for d in (t.get("dependencies") or [])]
        graph[tid] = deps
        dependents_count.setdefault(tid, 0)

    for tid, deps in graph.items():
        for d in deps:
            dependents_count[d] = dependents_count.get(d, 0) + 1

    return graph, dependents_count


def detect_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    """
    Return list of cycles (each cycle is list of node ids).
    Simple DFS-based cycle detection.
    """
    visited = set()
    stack = set()
    cycles: List[List[str]] = []

    def dfs(node: str, path: List[str]):
        if node in stack:
            # Found a cycle; capture from first occurrence in path
            if node in path:
                start_idx = path.index(node)
                cycles.append(path[start_idx:] + [node])
            return
        if node in visited:
            return

        visited.add(node)
        stack.add(node)
        for nei in graph.get(node, []):
            dfs(nei, path + [nei])
        stack.remove(node)

    for node in graph.keys():
        if node not in visited:
            dfs(node, [node])

    return cycles


def compute_base_score(
    urgency: float,
    importance: float,
    effort: float,
    dependents_norm: float,
    strategy: str,
) -> float:
    """
    strategy in {"fastest_wins", "high_impact", "deadline_driven", "smart_balance"}
    All components are in [0, 1]. effort is cost; (1 - effort) is "quick win".
    """
    quick_win = 1.0 - effort

    if strategy == "fastest_wins":
        # Low effort + some importance
        return 0.6 * quick_win + 0.3 * importance + 0.1 * urgency

    if strategy == "high_impact":
        # Importance dominates, with some urgency & dependency weight
        return 0.7 * importance + 0.2 * urgency + 0.1 * dependents_norm

    if strategy == "deadline_driven":
        # Deadline dominates
        return 0.7 * urgency + 0.2 * importance + 0.1 * dependents_norm

    # Default: smart_balance
    return (
        0.4 * importance
        + 0.3 * urgency
        + 0.2 * dependents_norm
        + 0.1 * quick_win
    )


def analyze_tasks(tasks: List[Dict[str, Any]], strategy: str = "smart_balance") -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Main entry point used by the views.
    Returns (analyzed_tasks, warnings)
    Each analyzed task will include:
      - score
      - strategy
      - explanation
      - has_cycle: bool
    """
    warnings: List[str] = []
    if not tasks:
        return [], ["No tasks provided."]

    # Build graph & dependents
    graph, dependents_count = build_dependency_graph(tasks)
    cycles = detect_cycles(graph)
    tasks_in_cycles = {node for cycle in cycles for node in cycle}

    if cycles:
        warnings.append(f"Detected {len(cycles)} circular dependency group(s). Tasks in cycles are de-prioritized.")

    max_dependents = max(dependents_count.values()) if dependents_count else 1

    analyzed: List[Dict[str, Any]] = []

    for idx, t in enumerate(tasks):
        tid = str(t.get("id", idx))
        title = t.get("title") or f"Task {idx + 1}"

        due_date = parse_date(t.get("due_date"))
        urgency = compute_urgency(due_date)

        importance_raw = t.get("importance")
        importance = normalize_importance(importance_raw)

        effort_raw = t.get("estimated_hours")
        effort = normalize_effort(effort_raw)

        dependents_norm = (
            dependents_count.get(tid, 0) / max_dependents if max_dependents > 0 else 0.0
        )

        base_score = compute_base_score(
            urgency=urgency,
            importance=importance,
            effort=effort,
            dependents_norm=dependents_norm,
            strategy=strategy,
        )

        has_cycle = tid in tasks_in_cycles
        if has_cycle:
            # Slightly penalize tasks that are part of circular dependency
            score = base_score * 0.7
        else:
            score = base_score

        explanation_parts = []
        if urgency >= 0.8:
            explanation_parts.append("Very urgent (due soon or overdue)")
        elif urgency >= 0.4:
            explanation_parts.append("Moderately urgent")

        if importance >= 0.7:
            explanation_parts.append("High importance")
        elif importance <= 0.3:
            explanation_parts.append("Low importance")

        if effort <= 0.3:
            explanation_parts.append("Quick win (low effort)")
        elif effort >= 0.8:
            explanation_parts.append("High effort")

        if dependents_norm >= 0.5:
            explanation_parts.append("Unblocks many other tasks")

        if has_cycle:
            explanation_parts.append("Involved in a circular dependency (penalized)")

        if not explanation_parts:
            explanation_parts.append("Balanced task with no extreme factors")

        explanation = "; ".join(explanation_parts)

        analyzed.append({
            **t,
            "id": tid,
            "score": round(score, 4),
            "strategy": strategy,
            "has_cycle": has_cycle,
            "explanation": explanation,
        })

    # Sort descending by score
    analyzed.sort(key=lambda x: x["score"], reverse=True)
    return analyzed, warnings


def suggest_top_tasks(tasks: List[Dict[str, Any]], strategy: str = "smart_balance", limit: int = 3) -> Tuple[List[Dict[str, Any]], List[str]]:
    analyzed, warnings = analyze_tasks(tasks, strategy=strategy)
    return analyzed[:limit], warnings
