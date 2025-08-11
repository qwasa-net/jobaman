import subprocess
import threading

from jobaman.helpers import synchronized
from jobaman.jobs.job import Job, JobState
from jobaman.logger import get_logger

log = get_logger()


class Manager:

    CMD_ENCODING = "utf-8"
    ENTRYPOINT_DEFAULT = None

    def __init__(self, config=None):
        self.jobs = {}
        self.lock = threading.Lock()
        if config:
            self.configure(config)

    def configure(self, config):
        self.entrypoint = config.get("entrypoint", self.ENTRYPOINT_DEFAULT)

    def _build_command(self, command):
        if not command and not self.entrypoint:
            raise ValueError("no command or entrypoint")
        if not command:
            command = []
        if isinstance(command, str):
            command = [command]
        if self.entrypoint:
            return [self.entrypoint] + command
        return command

    @synchronized
    def run_task(self, command, job_id=None):
        if job_id and job_id in self.jobs and self.jobs[job_id].state == JobState.RUNNING:
            raise ValueError(f"job_id {job_id} already exists and is running")
        command_run = self._build_command(command)
        log.debug("command=%s", command_run)
        process = subprocess.Popen(
            command_run,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding=self.CMD_ENCODING,
            errors="ignore",
            shell=False,
            bufsize=1,
            start_new_session=True,
        )
        job_id = job_id or str(process.pid)
        job = Job(process, state=JobState.RUNNING)
        self.jobs[job_id] = job
        log.info("job started: %s=%s", job_id, job)
        return job_id

    @synchronized
    def __getitem__(self, job_id):
        return self.jobs[job_id]

    @synchronized
    def __len__(self):
        return len(self.jobs)

    @property
    @synchronized
    def running_jobs(self):
        return {job_id: job for job_id, job in self.jobs.items() if job.state == JobState.RUNNING}

    @property
    @synchronized
    def running_jobs_count(self):
        return sum((1 for job in self.jobs.values() if job.state == JobState.RUNNING))

    @synchronized
    def purge(self):
        jobs = {}
        for job_id, job in self.jobs.items():
            if job.state not in (JobState.DONE, JobState.KILLED):
                jobs[job_id] = job
        self.jobs = jobs
        return len(self.jobs)

    def shutdown(self):
        """Terminate all running jobs."""
        for job_id, job in self.running_jobs.items():
            try:
                job.kill()
                log.info("job terminated: %s:%s", job_id, job)
            except Exception as e:
                log.error("error terminating job %s: %s", job_id, e)

    def __del__(self):
        self.shutdown()
