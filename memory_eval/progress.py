"""Small dependency-free progress display for long-running eval stages."""

from __future__ import annotations

import sys
import time
from threading import Event, Lock, Thread


_REWRITE_LINE = "\x1b[2K\x1b[1G"


def _duration(seconds: float | None) -> str:
    if seconds is None:
        return "--:--:--"
    value = max(0, int(seconds))
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class ProgressReporter:
    """Print one flushed progress line after every completed unit."""

    def __init__(self, stage: str, total: int, *, completed: int = 0) -> None:
        self.stage = stage
        self.total = max(0, total)
        self.completed = min(max(0, completed), self.total)
        self.resumed = self.completed
        self.succeeded = self.completed
        self.failed = 0
        self.started = time.perf_counter()
        self._last_width = 0
        self._closed = False
        self._lock = Lock()
        self._heartbeat_stop: Event | None = None
        self._heartbeat_thread: Thread | None = None
        self._print("resume" if completed else "start")

    def advance(self, *, item_id: str, status: str) -> None:
        with self._lock:
            self.completed = min(self.total, self.completed + 1)
            if status.upper().startswith("FAILED") or status.lower() == "error":
                self.failed += 1
            else:
                self.succeeded += 1
            self._print(status, item_id=item_id)

    def refresh(self, *, status: str = "running", item_id: str = "") -> None:
        """Refresh elapsed time without advancing the completed count."""

        with self._lock:
            if not self._closed:
                self._print(status, item_id=item_id)

    def start_heartbeat(self, *, interval: float = 1.0) -> None:
        """Keep an in-flight stage visibly alive on the same terminal line."""

        if self._heartbeat_thread is not None:
            return
        self._heartbeat_stop = Event()
        self.refresh()

        def heartbeat() -> None:
            assert self._heartbeat_stop is not None
            while not self._heartbeat_stop.wait(interval):
                self.refresh()

        self._heartbeat_thread = Thread(target=heartbeat, daemon=True)
        self._heartbeat_thread.start()

    def _print(self, status: str, *, item_id: str = "") -> None:
        elapsed = time.perf_counter() - self.started
        session_completed = self.completed - self.resumed
        rate = session_completed / elapsed if session_completed and elapsed > 0 else None
        remaining = self.total - self.completed
        eta = remaining / rate if rate else None
        fraction = self.completed / self.total if self.total else 1.0
        width = 20
        filled = min(width, int(fraction * width))
        bar = "#" * filled + "-" * (width - filled)
        suffix = f" item={item_id}" if item_id else ""
        line = (
            f"[{self.stage}] [{bar}] {self.completed}/{self.total} "
            f"({fraction * 100:5.1f}%) ok={self.succeeded} failed={self.failed} "
            f"elapsed={_duration(elapsed)} "
            f"eta={_duration(eta)} status={status}{suffix}"
        )
        finished = self.completed >= self.total
        padding = " " * max(0, self._last_width - len(line))
        sys.stdout.write(_REWRITE_LINE + line + padding + ("\n" if finished else ""))
        sys.stdout.flush()
        self._last_width = len(line)
        if finished:
            self._closed = True

    def close(self) -> None:
        """Finish an in-place line after interruption or an early stage exit."""

        if self._heartbeat_stop is not None:
            self._heartbeat_stop.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join()
        with self._lock:
            if not self._closed:
                sys.stdout.write("\n")
                sys.stdout.flush()
            self._closed = True
