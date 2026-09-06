# Dead-letter queue

Bound retries and move repeatedly failed jobs into a reviewable dead-letter state.

Educational implementation with synthetic examples.

## Run

Python 3.9 or newer; standard library only. From this directory:

```sh
python3 main.py
python3 main.py --help
python3 -m unittest -v
```

The default example uses synthetic data and needs no credentials, installation, or network connection. The script also works by absolute path from another working directory.

## Behavior

Jobs move from pending to in-flight, then to complete, delayed retry, or dead-letter. A claim increments attempts; failures schedule exponential delay. Explicit redrive resets a dead-letter job for another bounded cycle.

## Use in Python

```python
from main import Queue

queue = Queue(max_attempts=3, base_delay=2)
queue.enqueue('example-job', {'task': 'index'})
job = queue.claim(now=0)
queue.fail(job['id'], 'synthetic retryable error', now=0)
assert queue.claim(now=1) is None
retry = queue.claim(now=2)
queue.ack(retry['id'])
```

## Design limits

An in-memory single-worker simulation. A worker crash while a job is in-flight requires recovery outside this component; there is no visibility timeout, persistence, authentication, or real queue service. Payloads should be JSON-compatible and are held by reference.

## Verification

The unit tests cover successful operations, failure paths, and invariants. These are local correctness checks, not production performance or security certification.

## Repository checks

```sh
python3 verify.py
```

This runs the isolated test suite, synthetic example, and CLI help. The included GitHub Actions workflow repeats these checks when the repository is published. No hosted CI result is claimed by the local verification report.
