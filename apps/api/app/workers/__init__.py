"""Background workers.

Queue → Worker → Result → Events, in-memory/mocked today.

The real production queue (Redis/arq) swaps in behind the same interfaces in
M6 — the seam is the Queue protocol, and the worker/result/event machinery is
broker-agnostic. Current long-running work (research, call replay) still runs
on Starlette BackgroundTasks until that cutover.
"""
