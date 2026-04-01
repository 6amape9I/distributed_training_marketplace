# Stage 3 Note

The Stage 3 caveat is now closed.

The repository includes a dedicated two-runtime smoke test in `trainer_agent/app/tests/test_multi_runtime_smoke.py`. This test proves that two independent trainer runtimes can register, heartbeat, claim distinct tasks, execute `local_fit`, and persist task outputs without double assignment.

Stage 3 acceptance therefore no longer depends only on architecture, compose layout, or manual reasoning.
