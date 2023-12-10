"""Deterministic retry and dead-letter state transitions."""
import argparse
import json
import math

def clock(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Time must be finite and nonnegative')
    return value
