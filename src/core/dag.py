from typing import Dict, List, Tuple, Set, Any, Iterable


class TaskNode:
    """Representation of a single task/node in a DAG.

    Attributes:
        id: unique identifier for the task
        type: executor/type string (e.g. "llm", "script", "tool")
        config: arbitrary executor configuration
        inputs: mapping from input name -> source task output key (optional)
    """

    def __init__(self, id: str, type: str, config: Dict[str, Any] | None = None, inputs: Dict[str, str] | None = None) -> None:
        self.id = id
        self.type = type
        self.config = config or {}
        self.inputs = inputs or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "config": self.config,
            "inputs": self.inputs,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        return cls(id=data["id"], type=data.get("type", ""), config=data.get("config"), inputs=data.get("inputs"))

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"TaskNode(id={self.id!r}, type={self.type!r})"


class DAG:
    """Directed Acyclic Graph for tasks.

    The DAG stores tasks and directed edges (source -> target). It provides
    validation and methods to compute a topological execution order and
    utility traversals.
    """

    def __init__(self, tasks: Iterable[TaskNode] | None = None, edges: Iterable[Tuple[str, str]] | None = None) -> None:
        self.tasks: Dict[str, TaskNode] = {}
        self.edges: List[Tuple[str, str]] = []
        if tasks:
            for t in tasks:
                self.add_task(t)
        if edges:
            for s, d in edges:
                self.add_edge(s, d)

    def add_task(self, task: TaskNode) -> None:
        if task.id in self.tasks:
            raise ValueError(f"Task with id '{task.id}' already exists")
        self.tasks[task.id] = task

    def add_edge(self, source: str, target: str) -> None:
        # store as (source -> target)
        if source == target:
            raise ValueError("Self-loop edges are not allowed")
        self.edges.append((source, target))

    def validate(self) -> None:
        """Validate the DAG structure.

        Ensures that every edge references known tasks and that there are no
        duplicate edges. Does not check for cycles (use `topological_sort`).
        """
        for s, d in self.edges:
            if s not in self.tasks:
                raise ValueError(f"Edge references unknown source task: {s}")
            if d not in self.tasks:
                raise ValueError(f"Edge references unknown destination task: {d}")

        seen: Set[Tuple[str, str]] = set()
        for e in self.edges:
            if e in seen:
                raise ValueError(f"Duplicate edge found: {e}")
            seen.add(e)

    def _build_adjacency(self) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        """Return adjacency list and indegree map used by topological sort."""
        adj: Dict[str, List[str]] = {tid: [] for tid in self.tasks}
        indeg: Dict[str, int] = {tid: 0 for tid in self.tasks}
        for s, d in self.edges:
            # Only include edges between known tasks (validate should be called first)
            if s in adj and d in adj:
                adj[s].append(d)
                indeg[d] += 1
        return adj, indeg

    def topological_sort(self) -> List[str]:
        """Return a topological ordering of task ids.

        Raises RuntimeError if a cycle is detected.
        """
        self.validate()
        adj, indeg = self._build_adjacency()

        # Kahn's algorithm
        queue: List[str] = [n for n, deg in indeg.items() if deg == 0]
        order: List[str] = []
        while queue:
            n = queue.pop(0)
            order.append(n)
            for m in adj.get(n, []):
                indeg[m] -= 1
                if indeg[m] == 0:
                    queue.append(m)

        if len(order) != len(self.tasks):
            # cycle detected
            raise RuntimeError("Cycle detected in DAG; topological sort not possible")
        return order

    def execution_groups(self) -> List[List[str]]:
        """Return execution groups (levels) where tasks in the same list can run in parallel.

        This is useful to schedule levels of independent tasks.
        """
        self.validate()
        adj, indeg = self._build_adjacency()

        groups: List[List[str]] = []
        zero = [n for n, deg in indeg.items() if deg == 0]
        seen: Set[str] = set()

        while zero:
            groups.append(list(zero))
            next_zero: List[str] = []
            for n in zero:
                seen.add(n)
                for m in adj.get(n, []):
                    indeg[m] -= 1
                    if indeg[m] == 0:
                        next_zero.append(m)
            zero = next_zero

        if len(seen) != len(self.tasks):
            raise RuntimeError("Cycle detected in DAG; execution groups not available")
        return groups

    def downstream(self, task_id: str) -> List[str]:
        """Return all downstream (descendant) task ids from `task_id` in BFS order."""
        if task_id not in self.tasks:
            raise KeyError(task_id)
        adj, _ = self._build_adjacency()
        visited: Set[str] = set()
        queue: List[str] = [task_id]
        result: List[str] = []
        while queue:
            cur = queue.pop(0)
            for nb in adj.get(cur, []):
                if nb not in visited and nb != task_id:
                    visited.add(nb)
                    result.append(nb)
                    queue.append(nb)
        return result

    def upstream(self, task_id: str) -> List[str]:
        """Return all upstream (ancestor) task ids for `task_id` in BFS order."""
        if task_id not in self.tasks:
            raise KeyError(task_id)
        adj, _ = self._build_adjacency()
        # build reverse adjacency
        rev: Dict[str, List[str]] = {tid: [] for tid in self.tasks}
        for s, targets in adj.items():
            for t in targets:
                rev[t].append(s)

        visited: Set[str] = set()
        queue: List[str] = [task_id]
        result: List[str] = []
        while queue:
            cur = queue.pop(0)
            for nb in rev.get(cur, []):
                if nb not in visited and nb != task_id:
                    visited.add(nb)
                    result.append(nb)
                    queue.append(nb)
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "edges": list(self.edges),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DAG":
        tasks = [TaskNode.from_dict(d) for d in data.get("tasks", [])]
        edges = [tuple(e) for e in data.get("edges", [])]
        return cls(tasks=tasks, edges=edges)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"DAG(tasks={list(self.tasks.keys())}, edges={self.edges})"
