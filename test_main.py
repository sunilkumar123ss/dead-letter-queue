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




if __name__ == '__main__':
    unittest.main()
