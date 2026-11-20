from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

CREATE_NO_WINDOW = 0x08000000


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    output: str
    duration_ms: int
    cancelled: bool = False
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.cancelled and self.returncode == 0 and not self.error

    @property
    def display(self) -> str:
        return subprocess.list2cmdline(self.args)


class CommandRunner:
    """Runs platform-tools commands without a shell and streams output safely."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._active: dict[int, subprocess.Popen] = {}
        self._next_id = 1

    def run(
        self,
        args: list[str],
        on_line: Callable[[str], None] | None = None,
        cancel_event: threading.Event | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        args = [str(arg) for arg in args if arg is not None]
        started = time.monotonic()
        with self._lock:
            run_id = self._next_id
            self._next_id += 1

        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception as exc:
            return CommandResult(
                args=args,
                returncode=-1,
                output="",
                duration_ms=int((time.monotonic() - started) * 1000),
                error=str(exc),
            )

        with self._lock:
            self._active[run_id] = process

        chunks: list[str] = []
        buffer = ""

        def emit(line: str) -> None:
            cleaned = line.replace("\x00", "").rstrip()
            if not cleaned.strip():
                return
            chunks.append(cleaned)
            if on_line:
                try:
                    on_line(cleaned)
                except Exception:
                    pass

        cancelled = False
        try:
            assert process.stdout is not None
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    cancelled = True
                    process.terminate()
                    break
                char = process.stdout.read(1)
                if char == "":
                    break
                if char in ("\r", "\n"):
                    emit(buffer)
                    buffer = ""
                else:
                    buffer += char
                    if len(buffer) >= 16384:
                        emit(buffer)
                        buffer = ""
            if buffer:
                emit(buffer)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        finally:
            with self._lock:
                self._active.pop(run_id, None)

        return CommandResult(
            args=args,
            returncode=process.returncode if process.returncode is not None else -1,
            output="\n".join(chunks),
            duration_ms=int((time.monotonic() - started) * 1000),
            cancelled=cancelled,
        )

    def capture_binary(self, args: list[str]) -> bytes:
        completed = subprocess.run(
            [str(arg) for arg in args if arg is not None],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
            timeout=120,
            check=False,
        )
        return completed.stdout

    def cancel_all(self) -> None:
        with self._lock:
            processes = list(self._active.values())
        for process in processes:
            try:
                process.terminate()
            except Exception:
                pass


runner = CommandRunner()
