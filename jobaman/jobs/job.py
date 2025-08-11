import enum
import os
import signal
import threading
import time
from collections import defaultdict

from jobaman.helpers import synchronized
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

        self.streams = defaultdict(list)
        self.streams_limit = self.STREAM_MAX_LINES_DEFAULT

        self.process_handlers = []
        self._start_process_handlers()

        self.ts_started = int(time.time())
        self.ts_completed = None

    def __repr__(self) -> str:
        return (
            f"JobInfo(state={self.state}, "
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

    @synchronized
    def kill(self, wait=0.1):
        if self.state != JobState.RUNNING:
            return
        self.process.terminate()
        threading.Event().wait(wait)
        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
        threading.Event().wait(wait)
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
                        if len(self.streams[stream_name]) > self.streams_limit:
                            self.streams[stream_name] = self.streams[stream_name][-(self.streams_limit * 0.8) :]
            except Exception as e:
                log.error("Error reading %s stream: %s", stream_name, e)
                self.streams[stream_name].append(str(e))
            finally:
                if not stream.closed:
                    stream.close()

        def poll_job_completion():
            while self.state == JobState.RUNNING and self.process.poll() is None:
                threading.Event().wait(0.5)
            self.wait_job_completion()

        self.process_handlers = [
            threading.Thread(target=read_stream, args=(self.process.stdout, "stdout"), daemon=True),
            threading.Thread(target=read_stream, args=(self.process.stderr, "stderr"), daemon=True),
            threading.Thread(target=poll_job_completion, daemon=True),
        ]

        _ = list(map(lambda t: t.start(), self.process_handlers))
