"""Editable scratch tests. Add focused regression cases here."""
import unittest
from log_relay import LogRelay


class BasicTests(unittest.TestCase):
    def test_smoke(self):
        relay = LogRelay()
        self.assertEqual(relay.feed(b"ops|hello\n"), 1)
        self.assertEqual(relay.pop()["message"], "hello")
