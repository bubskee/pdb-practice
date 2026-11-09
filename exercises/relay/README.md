# Exercise 02: Log Relay

Original debugging practice · Python standard library · 90-minute target.
For a two-hour block, use 15 minutes for pdb familiarity, up to
90 minutes for repairs, and 15 minutes for regression tests and a debrief.
The timer starts only when you choose. No solution is included.

## Scenario

A monitoring service receives UTF-8 log data in arbitrary byte chunks. One
chunk may contain several records, half a record, or part of a multibyte
character. `LogRelay` buffers input and queues completed records for consumers.
The implementation has several defects. Repair `log_relay.py`, keeping the
public API and basic class structure. Use tests and debugger observations to
guide targeted changes. The supplied tests are intentional contract checks;
add tests in `tests/basicTests.py` without weakening `tests/relayTests.py`.

## Input contract

- `feed` receives `bytes`, including possibly `b""`. Across calls the stream
  is valid UTF-8, but any individual chunk may end inside a UTF-8 character.
  Invalid encodings and wrong argument types are outside this exercise.
- Only the LF byte (`b"\n"`) terminates a line. Retain all bytes after the last
  LF for a later call. Do not process an unterminated final line.
- For each complete line, remove its LF and then at most one trailing CR
  (`"\r"`). Other line-separator characters are ordinary content.
- A line consisting entirely of whitespace, including an empty line, is
  ignored. It is neither accepted nor rejected.
- Otherwise, the format is `channel|message`. The first `|` separates fields;
  any further `|` characters belong to the message. Apply Python `str.strip()`
  to the channel only. Preserve the message exactly after the one-CR rule,
  including leading/trailing whitespace. An empty message is valid.
- A nonblank line with no `|`, or with an empty channel after stripping, is
  malformed. Consume it, increment the rejection counter, and continue with
  later lines. It does not receive a sequence number.

## API contract

- `LogRelay()` creates an empty, independent relay.
- `feed(chunk)` appends bytes to the pending stream, processes complete lines,
  and returns the integer number of valid records accepted **in that call**.
  Accepted records enter the queue in stream order. Sequence numbers start at
  1 and increase by 1 only for accepted records, even if older records are popped.
- Each record is a dictionary with exactly `seq` (integer), `channel` (string),
  and `message` (string).
- `pop(channel=None)` removes and returns the oldest queued record, or the
  oldest record whose normalized channel equals the supplied string exactly.
  Matching is case-sensitive; the filter itself is not stripped. Return `None`
  if no record matches, leaving the queue unchanged. Preserve all other order.
- `snapshot()` returns the queued records in order. Its list and dictionaries
  must be independent copies. Mutating it must not affect the relay; later
  operations on the relay must not affect an older snapshot.
- `stats()` returns a fresh dictionary with exactly `accepted` (total accepted
  since construction/reset, including popped records), `rejected` (total
  malformed complete lines since construction/reset), `queued` (current record
  count), and `pending_bytes` (number of bytes awaiting a line terminator).
- `reset()` discards all queued records and pending bytes, zeros counters,
  restarts sequence numbering at 1, and returns `None`.

Example: feeding `b"ops|ready\nops|par"` returns `1`, queues
`{"seq": 1, "channel": "ops", "message": "ready"}`, and retains seven bytes.
Feeding `b"tial\n"` next returns `1` and queues sequence 2 with message `"partial"`.

## Run and debug

From this directory:

```sh
python3 -m unittest discover -s tests -p '*Tests.py' -v
python3 -m pdb -m unittest discover -s tests -p '*Tests.py'
```

For a single supplied test, use its full name, for example:

```sh
python3 -m pdb -m unittest tests.relayTests.RelayTests.test_ascii_record
```

Set a breakpoint with `b log_relay.py:LINE`, then `c`. Use `n`, `s`,
`p expression`, `where`, `u`, and `d` to inspect execution. Alternatively insert
`breakpoint()` and run the ordinary unittest command in the terminal. Remove
temporary breakpoints before the final full run. Ask for hints when wanted.

Record the baseline, elapsed time, final test count, one useful debugger
observation, and help received. A partial independent attempt is useful data.
