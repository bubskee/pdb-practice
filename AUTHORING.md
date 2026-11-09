# Add an original exercise

Create a directory under `exercises/` containing an `exercise.json` manifest,
`README.md` contract, intentionally broken source, and `unittest` tests.
Use an existing exercise as a structural template; write a new scenario.

```text
exercises/my_exercise/
  exercise.json
  README.md
  processor.py
  main.sh
  tests/
    __init__.py
    basicTests.py
    processorTests.py
```

Example manifest:

```json
{
  "id": "my_exercise",
  "number": "03",
  "title": "My original scenario",
  "summary": "One sentence describing the system to debug.",
  "target": "75 min target",
  "duration": 75,
  "source": "processor.py",
  "readonly": ["tests/processorTests.py", "tests/__init__.py", "main.sh"],
  "files": ["processor.py", "tests/basicTests.py", "tests/processorTests.py", "tests/__init__.py", "main.sh"]
}
```

- Give each exercise a unique, stable `id`; it keys the browser saves. Use a new
  ID for an incompatible revision. Two-digit `number` values determine ordering.
- `duration` must be 60, 75, 90, or 120 minutes. Timers start paused.
- List every runtime file explicitly. Paths must stay inside the exercise directory.
  `README.md` is loaded separately as the Description; do not put private notes,
  author solutions, or unrelated files in the manifest.
- Use `tests/*Tests.py` names for automatic discovery. Keep `tests/__init__.py`.
  The UI's focused-test picker recognizes ordinary `unittest.TestCase` classes
  and `test_...` methods; dynamic/metaprogrammed tests may not appear in that picker.
- `main.sh` should contain the ordinary unittest discovery command from the README.
  The browser's `bash main.sh` is a shortcut for that fixed command, not a shell
  interpreter for arbitrary script contents.
- Keep a small editable `basicTests.py` for learner regressions. Mark supplied
  tests read-only and ensure the learner's implementation remains editable.
- The Description renderer supports headings, paragraphs, bullets, fenced code,
  inline code, and bold text. Use simple Markdown; raw HTML is escaped.

Write exact contracts: argument and return types, ordering, ownership/copying,
state transitions, exceptions, and whether error paths may mutate state. Explain
what is outside scope. Avoid tests that demand behavior absent from the spec.
Validate expectations using a separate author implementation, without distributing
that solution. Record the initial failing baseline and check that each defect is
reachable with a meaningful test. Avoid disclosing bug locations in comments.

Run `python3 build.py`, then restart `python3 serve.py` and refresh the browser.
If testing a starter revision, use `?qa=1` for separate browser saves. This is
still a normal learner workspace, not an automated test mode.

Do not import real assessment material. If using a coach, request hints in
stages and keep the learner responsible for diagnosis and repairs.
