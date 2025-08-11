import subprocess
import threading
import uuid

from jobaman.helpers import synchronized
from jobaman.jobs.job import Job, JobState
from jobaman.logger import get_logger

log = get_logger()


class Manager:

    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    @synchronized
    def run_task(self, command):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            shell=False,
            bufsize=0,
        )
        job_id = str(process.pid) or str(uuid.uuid4())
        info = Job(process, state=JobState.RUNNING)
        self.jobs[job_id] = info
        log.info("job #`%s`: %.100s", job_id, command)
        return job_id

    @synchronized
    def __getitem__(self, job_id):
        return self.jobs[job_id]

    @synchronized
    def __len__(self):
        return len(self.jobs)

    @synchronized
    def list_running_jobs(self):
        return {job_id: job for job_id, job in self.jobs.items() if job.state == JobState.RUNNING}

    @synchronized
    def purge(self):
        self.jobs = {
            job_id: job for job_id, job in self.jobs.items() if job.state not in (JobState.DONE, JobState.KILLED)
        }
        return len(self.jobs)
