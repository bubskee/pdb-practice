import unittest

from dispatch_queue import DispatchQueue


class DispatchQueueTests(unittest.TestCase):
    def setUp(self):
        self.queue = DispatchQueue()

    def test_empty_queue(self):
        self.assertEqual(self.queue.snapshot(), [])
        self.assertIsNone(self.queue.claim())
        self.assertEqual(self.queue.purge(), 0)

    def test_instances_are_independent(self):
        self.queue.add('a')
        self.assertEqual(DispatchQueue().snapshot(), [])

    def test_fifo_claims(self):
        for job_id in ('a', 'b', 'c'):
            self.queue.add(job_id)
        self.assertEqual(self.queue.claim(), 'a')
        self.assertEqual(self.queue.claim(), 'b')
        self.assertEqual(self.queue.claim(), 'c')
        self.assertIsNone(self.queue.claim())

    def test_add_copies_tags(self):
        tags = ['urgent']
        self.queue.add('a', tags)
        tags.append('external')
        self.assertEqual(self.queue.snapshot()[0]['tags'], ['urgent'])

    def test_duplicate_preserves_state(self):
        self.queue.add('a', ['first'])
        self.queue.cancel('a')
        before = self.queue.snapshot()
        with self.assertRaises(ValueError):
            self.queue.add('a', ['second'])
        self.assertEqual(self.queue.snapshot(), before)

    def test_snapshot_is_detached(self):
        self.queue.add('a', ['one'])
        snapshot = self.queue.snapshot()
        snapshot[0]['tags'].append('two')
        snapshot[0]['state'] = 'done'
        snapshot.append({'id': 'fake', 'tags': [], 'state': 'pending'})
        self.assertEqual(self.queue.snapshot(), [
            {'id': 'a', 'tags': ['one'], 'state': 'pending'},
        ])

    def test_old_snapshot_preserves_state(self):
        self.queue.add('a')
        before = self.queue.snapshot()
        self.queue.claim()
        self.assertEqual(before[0]['state'], 'pending')

    def test_complete_requires_running(self):
        self.queue.add('a')
        with self.assertRaises(ValueError):
            self.queue.complete('a')
        self.assertEqual(self.queue.snapshot()[0]['state'], 'pending')
        self.queue.claim()
        self.queue.complete('a')
        self.assertEqual(self.queue.snapshot()[0]['state'], 'done')
        with self.assertRaises(ValueError):
            self.queue.complete('a')

    def test_cancel_states(self):
        self.queue.add('a')
        self.assertTrue(self.queue.cancel('a'))
        self.assertFalse(self.queue.cancel('a'))
        self.assertIsNone(self.queue.claim())
        self.queue.add('b')
        self.assertEqual(self.queue.claim(), 'b')
        self.assertFalse(self.queue.cancel('b'))
        self.queue.complete('b')
        self.assertFalse(self.queue.cancel('b'))
        self.assertEqual([job['state'] for job in self.queue.snapshot()],
                         ['cancelled', 'done'])

    def test_retry_moves_to_end(self):
        self.queue.add('a')
        self.assertEqual(self.queue.claim(), 'a')
        self.queue.add('b')
        self.queue.add('c')
        self.queue.retry('a')
        self.assertEqual([job['id'] for job in self.queue.snapshot()],
                         ['b', 'c', 'a'])
        self.assertEqual(self.queue.claim(), 'b')

    def test_retry_invalid_states_are_unchanged(self):
        for state in ('pending', 'cancelled', 'done'):
            with self.subTest(state=state):
                queue = DispatchQueue()
                queue.add('a')
                if state == 'cancelled':
                    queue.cancel('a')
                elif state == 'done':
                    queue.claim()
                    queue.complete('a')
                before = queue.snapshot()
                with self.assertRaises(ValueError):
                    queue.retry('a')
                self.assertEqual(queue.snapshot(), before)

    def test_unknown_ids_raise_without_mutating(self):
        self.queue.add('a')
        before = self.queue.snapshot()
        for operation in (self.queue.complete, self.queue.cancel, self.queue.retry):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(KeyError):
                    operation('missing')
                self.assertEqual(self.queue.snapshot(), before)

    def test_purge_adjacent_terminal_jobs(self):
        for job_id in ('a', 'b', 'c', 'd'):
            self.queue.add(job_id)
        self.queue.cancel('a')
        self.queue.cancel('b')
        self.queue.cancel('c')
        self.assertEqual(self.queue.purge(), 3)
        self.assertEqual([job['id'] for job in self.queue.snapshot()], ['d'])
        self.assertEqual(self.queue.purge(), 0)

    def test_purge_done_and_reuse_id(self):
        self.queue.add('a')
        self.queue.claim()
        self.queue.complete('a')
        self.assertEqual(self.queue.purge(), 1)
        self.queue.add('a', ['new'])
        self.assertEqual(self.queue.claim(), 'a')

    def test_unicode_preserved(self):
        self.queue.add('配送-🦉', ['café', '東京'])
        self.assertEqual(self.queue.claim(), '配送-🦉')
        self.assertEqual(self.queue.snapshot()[0]['tags'], ['café', '東京'])

    def test_interleaved_lifecycle(self):
        self.queue.add('a')
        self.assertEqual(self.queue.claim(), 'a')
        self.queue.add('b')
        self.queue.add('c')
        self.queue.retry('a')
        self.assertTrue(self.queue.cancel('c'))
        self.assertEqual(self.queue.claim(), 'b')
        self.queue.complete('b')
        self.assertEqual(self.queue.purge(), 2)
        self.assertEqual(self.queue.snapshot(), [
            {'id': 'a', 'tags': [], 'state': 'pending'},
        ])
        self.assertEqual(self.queue.claim(), 'a')
        self.queue.complete('a')
        self.assertEqual(self.queue.purge(), 1)
        self.assertIsNone(self.queue.claim())


if __name__ == '__main__':
    unittest.main()
