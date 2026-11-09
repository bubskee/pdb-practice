# Third-party runtime dependencies

The source package does not vendor these libraries; the browser loads pinned
versions from jsDelivr:

- Monaco Editor 0.52.2: https://github.com/microsoft/monaco-editor — MIT.
- Pyodide 0.29.0: https://github.com/pyodide/pyodide — MPL-2.0; its distribution
  includes CPython and other components under their respective licenses.

The MIT license in this repository covers this project's own code and original
exercises. It does not replace the licenses of external dependencies. If you
vendor a dependency for offline hosting, retain its license and notices.

The isolation service worker in this repository adds COOP/COEP headers to network
responses and does not cache learner files. `serve.py` supplies these headers
directly for local use.
