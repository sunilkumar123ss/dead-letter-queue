"""Deterministic retry and dead-letter state transitions."""
import argparse
import json
import math

def clock(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Time must be finite and nonnegative')
    return value

class Queue:

    def __init__(self, max_attempts=3, base_delay=1):
        if type(max_attempts) is not int or not 1 <= max_attempts <= 20:
            raise ValueError('max_attempts must be 1..20')
        self.base_delay = clock(base_delay)
        self.max_attempts = max_attempts
        self.jobs = {}
        self.now = 0

    def advance(self, now):
        clock(now)
        if now < self.now:
            raise ValueError('Clock cannot move backward')
        self.now = now

    def enqueue(self, key, payload):
        if not isinstance(key, str) or not key or key in self.jobs:
            raise ValueError('Unique nonempty job ID required')
        self.jobs[key] = {'payload': payload, 'state': 'pending', 'attempts': 0, 'available': self.now, 'error': None}

    def claim(self, now):
        self.advance(now)
        for (key, job) in self.jobs.items():
            if job['state'] == 'pending' and job['available'] <= now:
                job['state'] = 'inflight'
                job['attempts'] += 1
                return {'id': key, 'payload': job['payload'], 'attempt': job['attempts']}
        return None

    def inflight(self, key):
        if key not in self.jobs or self.jobs[key]['state'] != 'inflight':
            raise ValueError('Job is not in-flight')
        return self.jobs[key]

    def ack(self, key):
        self.inflight(key)['state'] = 'complete'

    def fail(self, key, error, now):
        job = self.inflight(key)
        if not isinstance(error, str):
            raise ValueError('Error must be a string')
        self.advance(now)
        available = now + self.base_delay * 2 ** (job['attempts'] - 1)
        if not math.isfinite(available):
            raise ValueError('Delay overflow')
        job['error'] = error[:200]
        job['available'] = available
        job['state'] = 'dead' if job['attempts'] >= self.max_attempts else 'pending'

    def redrive(self, key, now):
        if key not in self.jobs or self.jobs[key]['state'] != 'dead':
            raise ValueError('Only dead-letter jobs can be redriven')
        self.advance(now)
        self.jobs[key].update(state='pending', attempts=0, available=now, error=None)
