import os
import sys

# Ensure `src` is on sys.path so imports work when running the script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.dag import TaskNode, DAG
from core.state_machine import StateMachine


def main():
    # Create tasks
    a = TaskNode(id="A", type="script")
    b = TaskNode(id="B", type="script")
    c = TaskNode(id="C", type="script")

    # Edges: A -> B, A -> C (B and C depend on A)
    dag = DAG(tasks=[a, b, c], edges=[("A", "B"), ("A", "C")])

    print("Topological order:", dag.topological_sort())
    print("Execution groups:", dag.execution_groups())

    sm = StateMachine(dag=dag)
    print("Initial runnable:", sm.next_runnable())

    # Run A
    sm.mark_running("A")
    sm.mark_succeeded("A", result={"value": 1})
    print("After A succeeded, runnable:", sm.next_runnable())

    # Run B and C
    runnable = sm.next_runnable()
    for t in runnable:
        sm.mark_running(t)
        # pretend B succeeds and C fails
        if t == "B":
            sm.mark_succeeded(t, result={"value": 2})
        else:
            sm.mark_failed(t, error="simulated error")

    print("States:", sm.states)
    print("Results:", sm.results)
    print("Errors:", sm.errors)
    print("All done?", sm.all_done())


if __name__ == "__main__":
    main()
