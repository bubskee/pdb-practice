# Exercise 01: Dispatch Queue

Original Python debugging practice. Budget: **75 minutes**, starting when you begin. Python standard library only. The starter implementation is intentionally broken; no solution is included.

## Task

Repair `dispatch_queue.py` so it follows this specification and passes the tests. Keep the public API and the basic implementation structure. Add regression tests when useful; do not weaken the supplied assertions. Inputs are valid unless a case below explicitly specifies an exception.

`DispatchQueue` manages jobs for one worker:

- Each new queue is empty and independent of every other queue.
- `add(job_id, tags=None)` accepts a string ID and an optional list of strings. It adds a pending job at the end of the queue and copies the supplied tags. IDs must be unique among jobs currently present, including cancelled and completed jobs. Duplicate IDs raise `ValueError` without changing state.
- `claim()` returns the ID of the earliest pending job and marks it running. Running, cancelled, and completed jobs are skipped. If nothing is pending, return `None`. Only one job changes state per call.
- `complete(job_id)` changes a running job to done. A known job in any other state raises `ValueError`; an unknown ID raises `KeyError`. Errors leave state unchanged.
- `cancel(job_id)` changes a pending job to cancelled and returns `True`. For a known job in any other state, return `False` without changing it. An unknown ID raises `KeyError`.
- `retry(job_id)` changes a running job back to pending and moves it behind **all other jobs**, so pending work already waiting is claimed first. Other known states raise `ValueError`; an unknown ID raises `KeyError`. Errors leave state unchanged.
- `snapshot()` returns a list of job dictionaries in current queue order, each with exactly `id`, `tags`, and `state`. Its list, dictionaries, and tag lists are independent copies: changing a snapshot must not change queue state, and later queue changes must not change old snapshots.
- `purge()` removes all done and cancelled jobs, retains the relative order of remaining jobs, and returns the number removed. Removed IDs can be used again.

No persistence, concurrency, I/O, or external packages are required. Unicode IDs and tags are ordinary Python strings and must be preserved exactly.

## Run

From this exercise directory:

```sh
python3 -m unittest discover -s tests -p '*Tests.py' -v
```

To debug a single test, substitute its name from the test output:

```sh
python3 -m pdb -m unittest tests.dispatchTests.DispatchQueueTests.test_fifo_claims
```

Useful pdb commands: `b` (breakpoint), `n` (next), `s` (step), `p expression` (inspect), `c` (continue), `where` (stack), `q` (quit). An IDE debugger is equally suitable.

## Session structure

1. First 10 minutes: read the contract and tests, run the suite, record the baseline.
2. Next 50 minutes: pick a failing behavior, write a hypothesis, inspect execution in the debugger, make a targeted repair, rerun the focused test and suite. Repeat.
3. Final 15 minutes: run the full suite, add a regression case, and record what you learned.

Passing tests are the immediate goal; the full written contract still applies. Stop at 75 minutes and report partial progress if needed. Ask for a nudge, a stronger hint, or an explanation when you want help; the coach will not volunteer fixes.

For your debrief, report minutes spent, final test results, where you got stuck, and one debugger observation that helped.
