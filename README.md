# pdb-practice

A local Python debugging practice range: a browser editor, original broken
exercises, `unittest` results, and a real interactive `pdb` terminal.

## Run locally

You need **Python 3.11+**, a current desktop browser, and internet access to load
the editor and browser Python runtime. No Node, pip packages, API keys, account,
or paid services are required.

```sh
git clone https://github.com/bubskee/pdb-practice.git
cd pdb-practice
python3 serve.py
```

Open **http://127.0.0.1:8000/**. On Windows, use `py -3 serve.py` if `python3`
is unavailable. Stop the server with Ctrl+C. If the port is occupied, use
`python3 serve.py --port 8001` and open the printed address.

The launcher builds the exercise catalog automatically, serves only `web/`,
and binds to your own computer. It does not execute learner Python on the host;
that code runs inside a browser worker. Don't open `index.html` directly with
`file://`: the runtime and debugger require an HTTP origin.

## Practice

1. Select an exercise and read its description and supplied tests.
2. Run the suite to establish a baseline. These starters are intentionally broken.
3. Choose one failure, form a hypothesis, inspect execution, and make a targeted repair.
4. Add regression cases in the editable `tests/basicTests.py`.
5. Run all tests and save a practice checkpoint. Start the timer only when ready.

**In Terminal** shows prints and accepts debugger commands. **Structured** shows
individual test results. Supplied tests and `main.sh` are read-only in the UI.
Use Terminal when your code contains `breakpoint()`.

```sh
python3 -m unittest discover -s tests -p '*Tests.py' -v
python3 -m pdb -m unittest discover -s tests -p '*Tests.py'
```

At `(Pdb)`, use `b filename.py:LINE`, `c`, `n`, `s`, `p expression`, `where`,
`u`, `d`, and `q`. You can also insert `breakpoint()` and run the ordinary test
command. After a program finishes, `python3 -m pdb` normally restarts it; use `q`
to return to the command prompt. The Information panel includes a command guide.

### Included exercises

| Exercise | Focus | Suggested time | Starter baseline |
| --- | --- | --- | --- |
| Dispatch Queue | Classes, ordering, state transitions, mutable data | 75 min | 10/16 passing |
| Log Relay | UTF-8 byte chunks, parsing, queues, state | 90 min | 11/24 passing |

All exercises are original. No solutions or actual assessment questions are
included. This project is independent of CodeSignal and any hiring program.
Use it for practice; follow the assistance rules of any real assessment.

## Saves and runtime limits

- Code, notes, timers, and checkpoints save in this browser's local storage,
  separately for each exercise. They are not uploaded or written into the clone.
- The origin matters: `localhost`, `127.0.0.1`, and different ports have separate
  saves. Use the same printed address each time. Download files/debriefs before
  clearing browser data or moving computers.
- Submit records a local checkpoint; it sends nothing to an assessor.
- The terminal uses real CPython 3.13.2 via Pyodide, not your installed Python.
  It provides a small command launcher, not a full operating-system shell.
  Supported commands include `python3`, `python`, `ls`, `cat`, `pwd`, `clear`,
  and `bash main.sh`. No subprocesses or package installation are provided.
- Every command uses the current editor files. Files changed by Python are
  temporary and do not update editor models; edit in the editor to keep changes.
- A run stops after 30 seconds without an input prompt. Waiting in pdb does not
  count toward that limit. **Interrupt (Ctrl+C)** signals Python; **Stop** restarts
  the worker and preserves editor files. Keyboard shortcuts can vary by browser.
- Pyodide 0.29.0 and Monaco 0.52.2 load from jsDelivr. This is local execution,
  **not a guaranteed offline bundle**. See [THIRD_PARTY.md](THIRD_PARTY.md).

## Use an ordinary terminal instead

The exercises also run directly with your installed Python:

```sh
cd exercises/relay
python3 -m unittest discover -s tests -p '*Tests.py' -v
python3 -m pdb -m unittest tests.relayTests.RelayTests.test_ascii_record
```

Edit the files in that exercise directory. Browser saves and these files are
independent. Failed tests on a fresh starter are expected.

## Build and extend

```sh
python3 build.py
python3 -m unittest discover -s tests -v
```

`build.py` assembles `web/exercises.json` from readable files in `exercises/`.
The top-level tests check packaging and server behavior; they do not require
the intentionally broken exercises to pass. Restart `serve.py` after changing
exercise files, then refresh the browser. Existing browser saves take precedence
over changed starter code; use Reset file (with backup) when appropriate.

See [AUTHORING.md](AUTHORING.md) to add your own scenario. The browser application
is plain HTML, CSS, and JavaScript under `web/`; there is no frontend build step.
The `web/` directory can also be served by a static host after running the build.
Interactive pdb requires cross-origin isolation; the local launcher supplies
the headers, and the included service worker provides a fallback for HTTPS hosts.
Third-party iframe hosts may still prevent interactive input.

## Troubleshooting

- **Runtime fails to load:** check connectivity to `cdn.jsdelivr.net`, browser
  console errors, and extensions blocking scripts or WebAssembly.
- **Interactive input unavailable:** open the localhost URL in a full browser
  tab. Use the provided launcher so the isolation headers are present.
- **My changes disappeared:** check the browser profile, host, and port. The repo
  does not sync local storage across addresses or devices.
- **A changed starter isn't appearing:** refresh after rebuilding; saved learner
  code is preserved until you explicitly reset that file.

MIT licensed. Contributions should contain only original practice material.
