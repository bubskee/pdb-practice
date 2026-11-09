"""Supplied contract tests. Do not weaken these assertions."""
import unittest
from log_relay import LogRelay


def record(seq, channel, message):
    return {"seq": seq, "channel": channel, "message": message}


class RelayTests(unittest.TestCase):
    def setUp(self):
        self.relay = LogRelay()

    def test_initial_state(self):
        self.assertEqual(self.relay.snapshot(), [])
        self.assertIsNone(self.relay.pop())
        self.assertEqual(self.relay.stats(), {
            "accepted": 0, "rejected": 0, "queued": 0, "pending_bytes": 0})

    def test_ascii_record(self):
        self.assertEqual(self.relay.feed(b"build|ready\n"), 1)
        self.assertEqual(self.relay.snapshot(), [record(1, "build", "ready")])

    def test_multiple_records_fifo(self):
        self.assertEqual(self.relay.feed(b"a|one\nb|two\n"), 2)
        self.assertEqual(self.relay.pop(), record(1, "a", "one"))
        self.assertEqual(self.relay.pop(), record(2, "b", "two"))
        self.assertIsNone(self.relay.pop())

    def test_ascii_record_across_chunks(self):
        self.assertEqual(self.relay.feed(b"build|rea"), 0)
        self.assertEqual(self.relay.snapshot(), [])
        self.assertEqual(self.relay.stats()["pending_bytes"], 9)
        self.assertEqual(self.relay.feed(b"dy\n"), 1)
        self.assertEqual(self.relay.pop(), record(1, "build", "ready"))

    def test_complete_unicode_record(self):
        self.assertEqual(self.relay.feed("café|你好 🌱\n".encode("utf-8")), 1)
        self.assertEqual(self.relay.pop(), record(1, "café", "你好 🌱"))

    def test_split_utf8_character(self):
        self.assertEqual(self.relay.feed(b"a|caf\xc3"), 0)
        self.assertEqual(self.relay.stats()["pending_bytes"], 6)
        self.assertEqual(self.relay.feed(b"\xa9\n"), 1)
        self.assertEqual(self.relay.pop(), record(1, "a", "café"))

    def test_complete_line_before_partial_character(self):
        self.assertEqual(self.relay.feed(b"a|ok\nb|\xf0\x9f"), 1)
        self.assertEqual(self.relay.snapshot(), [record(1, "a", "ok")])
        self.assertEqual(self.relay.stats()["pending_bytes"], 4)
        self.assertEqual(self.relay.feed(b"\x8c\xb1\n"), 1)
        self.assertEqual(self.relay.snapshot()[1], record(2, "b", "🌱"))

    def test_every_two_chunk_boundary(self):
        data = "工具|café🌱\nops|done\n".encode("utf-8")
        expected = [record(1, "工具", "café🌱"), record(2, "ops", "done")]
        for cut in range(len(data) + 1):
            with self.subTest(cut=cut):
                relay = LogRelay()
                total = relay.feed(data[:cut]) + relay.feed(data[cut:])
                self.assertEqual(total, 2)
                self.assertEqual(relay.snapshot(), expected)

    def test_one_byte_at_a_time(self):
        total = 0
        for byte in "a|é🌱\n".encode("utf-8"):
            total += self.relay.feed(bytes([byte]))
        self.assertEqual(total, 1)
        self.assertEqual(self.relay.pop(), record(1, "a", "é🌱"))

    def test_channel_trim_message_preserved(self):
        self.relay.feed(b"  ops \t|  done \t \n")
        self.assertEqual(self.relay.pop(), record(1, "ops", "  done \t "))

    def test_message_can_contain_pipes(self):
        self.assertEqual(self.relay.feed(b"ops|a|b||c\n"), 1)
        self.assertEqual(self.relay.pop(), record(1, "ops", "a|b||c"))

    def test_empty_message_is_valid(self):
        self.assertEqual(self.relay.feed(b"ops|\n"), 1)
        self.assertEqual(self.relay.pop(), record(1, "ops", ""))

    def test_blank_lines_are_ignored(self):
        self.assertEqual(self.relay.feed(b"\n \t\n\r\n"), 0)
        self.assertEqual(self.relay.stats()["rejected"], 0)
        self.assertEqual(self.relay.snapshot(), [])

    def test_malformed_lines_are_consumed(self):
        self.assertEqual(self.relay.feed(b"missing separator\n  |bad\na|ok\n"), 1)
        self.assertEqual(self.relay.stats()["rejected"], 2)
        self.assertEqual(self.relay.snapshot(), [record(1, "a", "ok")])
        self.assertEqual(self.relay.feed(b""), 0)
        self.assertEqual(self.relay.stats()["rejected"], 2)

    def test_crlf_removes_only_one_carriage_return(self):
        self.relay.feed(b"a|first\r\nb|second\r\r\n")
        self.assertEqual(self.relay.snapshot(), [
            record(1, "a", "first"), record(2, "b", "second\r")])

    def test_other_line_separators_are_message_content(self):
        self.relay.feed("a|left\u2028right\n".encode("utf-8"))
        self.assertEqual(self.relay.pop(), record(1, "a", "left\u2028right"))

    def test_pop_channel_keeps_other_records_in_order(self):
        self.relay.feed(b"a|one\nb|two\na|three\n")
        self.assertEqual(self.relay.pop("b"), record(2, "b", "two"))
        self.assertIsNone(self.relay.pop("B"))
        self.assertEqual(self.relay.snapshot(), [
            record(1, "a", "one"), record(3, "a", "three")])

    def test_accepted_count_survives_pop(self):
        self.relay.feed(b"a|one\na|two\n")
        self.relay.pop()
        self.assertEqual(self.relay.stats(), {
            "accepted": 2, "rejected": 0, "queued": 1, "pending_bytes": 0})

    def test_snapshot_is_independent(self):
        self.relay.feed(b"a|one\n")
        snapshot = self.relay.snapshot()
        snapshot[0]["message"] = "changed"
        snapshot.append(record(99, "x", "extra"))
        self.assertEqual(self.relay.snapshot(), [record(1, "a", "one")])
        self.relay.feed(b"b|two\n")
        self.assertEqual(len(snapshot), 2)
        self.assertEqual(snapshot[1], record(99, "x", "extra"))

    def test_reset_clears_partial_input_and_counters(self):
        self.relay.feed(b"a|old\nbad\nunfinished|")
        self.relay.reset()
        self.assertEqual(self.relay.stats(), {
            "accepted": 0, "rejected": 0, "queued": 0, "pending_bytes": 0})
        self.assertEqual(self.relay.feed(b"b|new\n"), 1)
        self.assertEqual(self.relay.pop(), record(1, "b", "new"))

    def test_instances_are_independent(self):
        other = LogRelay()
        self.relay.feed(b"a|one\npartial")
        self.assertEqual(other.feed(b"b|two\n"), 1)
        self.assertEqual(other.pop(), record(1, "b", "two"))
        other.reset()
        self.assertEqual(self.relay.snapshot(), [record(1, "a", "one")])

    def test_partial_byte_count_and_empty_feed(self):
        self.assertEqual(self.relay.feed("a|é".encode("utf-8")), 0)
        self.assertEqual(self.relay.feed(b""), 0)
        self.assertEqual(self.relay.stats()["pending_bytes"], 4)
        self.assertEqual(self.relay.feed(b"\n"), 1)

    def test_interleaved_processing(self):
        self.assertEqual(self.relay.feed(b"a|one\nb|two\na|par"), 2)
        self.assertEqual(self.relay.pop("b"), record(2, "b", "two"))
        self.assertEqual(self.relay.feed(b"tial\ninvalid\n\na|four\n"), 2)
        self.assertEqual(self.relay.snapshot(), [record(1, "a", "one"),
            record(3, "a", "partial"), record(4, "a", "four")])
        self.assertEqual(self.relay.stats(), {
            "accepted": 4, "rejected": 1, "queued": 3, "pending_bytes": 0})
