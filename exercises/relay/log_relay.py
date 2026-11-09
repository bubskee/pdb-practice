"""Incremental log relay. Repair this implementation against the specification."""


class LogRelay:
    def __init__(self):
        self._pending = b""
        self._records = []
        self._next_seq = 1
        self._rejected = 0

    def feed(self, chunk):
        text = (self._pending + chunk).decode("utf-8")
        lines = text.split("\n")
        self._pending = lines.pop().encode("utf-8")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "|" not in line:
                self._rejected += 1
                continue
            channel, message = line.split("|")
            channel = channel.strip()
            if not channel:
                self._rejected += 1
                continue
            self._records.append({
                "seq": self._next_seq,
                "channel": channel,
                "message": message,
            })
            self._next_seq += 1
        return len(lines)

    def pop(self, channel=None):
        for index, record in enumerate(self._records):
            if channel is None or record["channel"] == channel:
                return self._records.pop(index)
        return None

    def snapshot(self):
        return self._records.copy()

    def stats(self):
        return {
            "accepted": len(self._records),
            "rejected": self._rejected,
            "queued": len(self._records),
            "pending_bytes": len(self._pending),
        }

    def reset(self):
        self._records.clear()
        self._next_seq = 1
        self._rejected = 0
