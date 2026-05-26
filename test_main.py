import importlib.util
from pathlib import Path
import sys
import unittest
_spec = importlib.util.spec_from_file_location('lab_' + Path(__file__).parent.name.replace('-', '_'), Path(__file__).with_name('main.py'))
m = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = m
_spec.loader.exec_module(m)

class DeadLetterTests(unittest.TestCase):

    def test_ack_prevents_redelivery(self):
        q = m.Queue()
        q.enqueue('a', {})
        q.claim(0)
        q.ack('a')
        self.assertIsNone(q.claim(100))

    def test_delay_is_respected(self):
        q = m.Queue()
        q.enqueue('a', {})
        q.claim(0)
        q.fail('a', 'x', 0)
        self.assertIsNone(q.claim(0.9))
        self.assertEqual(q.claim(1)['attempt'], 2)

    def test_attempt_limit(self):
        q = m.Queue(max_attempts=1)
        q.enqueue('a', {})
        q.claim(0)
        q.fail('a', 'x', 0)
        self.assertEqual(q.jobs['a']['state'], 'dead')
        self.assertIsNone(q.claim(20))

    def test_redrive_starts_new_cycle(self):
        q = m.Queue(max_attempts=1)
        q.enqueue('a', {})
        q.claim(0)
        q.fail('a', 'x', 0)
        q.redrive('a', 2)
        self.assertEqual(q.claim(2)['attempt'], 1)

    def test_state_and_clock_guards(self):
        q = m.Queue()
        q.enqueue('a', {})
        with self.assertRaises(ValueError):
            q.ack('a')
        q.claim(5)
        with self.assertRaises(ValueError):
            q.claim(4)
        with self.assertRaises(ValueError):
            q.redrive('a', 6)

    def test_fifo_skips_delayed(self):
        q = m.Queue()
        q.enqueue('a', {})
        q.enqueue('b', {})
        q.claim(0)
        q.fail('a', 'x', 0)
        self.assertEqual(q.claim(0)['id'], 'b')
if __name__ == '__main__':
    unittest.main()
