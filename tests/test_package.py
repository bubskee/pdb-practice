import copy
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from build import ROOT, build, catalog
from serve import Handler


class CatalogTests(unittest.TestCase):
    def test_catalog_matches_source_and_contracts(self):
        items = build()
        self.assertTrue({'dispatch', 'relay'} <= {item['id'] for item in items})
        for item in items:
            source = ROOT / 'exercises' / item['id']
            self.assertEqual(item['spec'], (source / 'README.md').read_text(encoding='utf-8'))
            for name, content in item['files'].items():
                self.assertEqual(content, (source / name).read_text(encoding='utf-8'))
            self.assertNotIn(item['source'], item['readonly'])
            self.assertIn('tests/basicTests.py', item['files'])

    def fixture(self, root, **changes):
        item = copy.deepcopy(json.loads((ROOT / 'exercises/dispatch/exercise.json').read_text()))
        item.update(changes)
        target = root / 'sample'
        target.mkdir()
        (target / 'exercise.json').write_text(json.dumps(item))
        return target

    def test_escape_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, files=['../outside.py', 'tests/__init__.py'],
                         source='../outside.py', readonly=[])
            with self.assertRaisesRegex(ValueError, 'Invalid exercise path'):
                catalog(root)

    def test_missing_manifest_field_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self.fixture(root)
            manifest = target / 'exercise.json'
            item = json.loads(manifest.read_text())
            del item['source']
            manifest.write_text(json.dumps(item))
            with self.assertRaisesRegex(ValueError, 'missing fields'):
                catalog(root)

    def test_readonly_implementation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, readonly=['dispatch_queue.py'])
            with self.assertRaisesRegex(ValueError, 'must be editable'):
                catalog(root)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()
        class QuietHandler(Handler):
            def log_message(self, *args):
                pass
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0),
            partial(QuietHandler, directory=str(ROOT / 'web')))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_page_and_isolation_headers(self):
        with urlopen(self.url + '/', timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers['Cross-Origin-Opener-Policy'], 'same-origin')
            self.assertEqual(response.headers['Cross-Origin-Embedder-Policy'], 'require-corp')
            self.assertIn('Python Debugging Range', response.read().decode())

    def test_serves_generated_catalog_and_worker(self):
        with urlopen(self.url + '/exercises.json', timeout=5) as response:
            self.assertGreaterEqual(len(json.load(response)), 2)
        with urlopen(self.url + '/worker.js', timeout=5) as response:
            self.assertIn(b'loadPyodide', response.read())

    def test_repository_files_are_not_served(self):
        for path in ('/README.md', '/.git/config', '/%2e%2e/README.md'):
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                urlopen(self.url + path, timeout=5)
            self.assertEqual(error.exception.code, 404)
            error.exception.close()


if __name__ == '__main__':
    unittest.main()
