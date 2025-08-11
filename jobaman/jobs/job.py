import enum
import os
import signal
import threading
import time
from collections import defaultdict, deque

from jobaman.helpers import get_pids_by_ppid, synchronized
from jobaman.logger import get_logger

log = get_logger()


class JobState(enum.StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "finished"
    KILLED = "killed"


class Job:

    STREAM_MAX_LINES_DEFAULT = 10_000

    def __init__(self, process, state=JobState.IDLE):
        self.lock = threading.Lock()

        self.process = process
        self.state = state
        self.exit_code = None

        self.streams_limit = self.STREAM_MAX_LINES_DEFAULT
        self.streams = defaultdict(lambda: deque(maxlen=self.streams_limit))

        self.process_handlers = []
        self._start_process_handlers()

        self.ts_started = int(time.time())
        self.ts_completed = None

    def __repr__(self) -> str:
        return (
            f"Job(state={self.state}, "
            f"pid={self.process.pid}, exit_code={self.exit_code}, "
            f"ts_started={self.ts_started}, ts_completed={self.ts_completed})"
        )

    @property
    def stdout(self):
        with self.lock:
            return "".join(self.streams["stdout"])

    @property
    def stderr(self):
        with self.lock:
            return "".join(self.streams["stderr"])

    @property
    def runtime(self):
        if self.ts_completed is not None:
            return int(self.ts_completed - self.ts_started)
        return int(time.time()) - self.ts_started

    @synchronized
    def kill(self, wait=0.1):
        if self.state != JobState.RUNNING:
            return
        pids = get_pids_by_ppid(self.process.pid)
        pids.insert(0, self.process.pid)
        log.info("killing job: %s, pids: %s", self, pids)
        self.process.terminate()
        time.sleep(wait)
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:  # noqa
                continue
        if self.process.poll() is None:
            self.process.kill()
        self.exit_code = -1
        self.state = JobState.KILLED
        log.info("job killed: %s", self)
        self._close_handlers()

    @synchronized
    def wait_job_completion(self, timeout=None):
        if self.state == JobState.RUNNING:
            if self.process.poll() is None:
                try:
                    self.process.wait(timeout=timeout)
                except TimeoutError:
                    pass
            self.exit_code = self.process.returncode
            self.state = JobState.DONE
            self._close_handlers()
            self.ts_completed = int(time.time())
        log.info("job completed: %s", self)
        return self.exit_code

    def _close_handlers(self):
        ct = threading.current_thread()
        _ = list(map(lambda t: t is not ct and t.join(timeout=0.1), self.process_handlers))

    @synchronized
    def _start_process_handlers(self):

        def read_stream(stream, stream_name):
            if stream is None:
                return
            try:
                for line in iter(stream.readline, ""):
                    with self.lock:
                        self.streams[stream_name].append(line)
            except Exception as e:
                log.error("Error reading %s stream: %s", stream_name, e)
                self.streams[stream_name].append(str(e))
            finally:
                if not stream.closed:
                    try:
                        stream.close()
                    except Exception as _:
                        pass

        def poll_job_completion(wait=0.5):
            while self.state == JobState.RUNNING and self.process.poll() is None:
                threading.Event().wait(wait)
            self.wait_job_completion()

        self.process_handlers = [
            threading.Thread(target=read_stream, args=(self.process.stdout, "stdout"), daemon=True),
            threading.Thread(target=read_stream, args=(self.process.stderr, "stderr"), daemon=True),
            threading.Thread(target=poll_job_completion, daemon=True),
        ]

        _ = list(map(lambda t: t.start(), self.process_handlers))

    def __del__(self):
        self.kill()
