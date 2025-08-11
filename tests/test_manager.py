import time
import unittest

from jobaman.jobs.manager import JobState, Manager
from tests.base import BaseTestCase


class TestManager(BaseTestCase, unittest.TestCase):

    def test_10_run_date_task(self):
        manager = Manager(config={"max_jobs": 2, "entrypoint": None})
        job_id = manager.run_task(["date", "--utc", "--iso-8601=seconds"])

        time.sleep(1)
        job = manager[job_id]
        self.assertEqual(job.exit_code, 0)
        self.assertIsNotNone(job.ts_started)
        self.assertIsNotNone(job.ts_completed)
        self.assertEqual(job.state, JobState.DONE)

        output = job.stdout.strip()
        isodt_re = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\+\d{2}:\d{2})?\n?$"
        self.assertRegex(output, isodt_re)

        manager.purge()
        self.assertNotIn(job_id, manager.jobs)
        self.assertEqual(manager.running_jobs_count, 0)
        manager.shutdown()

    def test_20_max_jobs_limit(self, n=25):
        manager = Manager(config={"max_jobs": n, "entrypoint": None})
        job_ids = []
        for _ in range(n):
            job_id = manager.run_task(["sleep", "5"])
            job_ids.append(job_id)
            self.assertEqual(manager.running_jobs_count, len(job_ids))
        with self.assertRaises(ValueError):
            manager.run_task(["date"])
        manager.shutdown()

    def test_30_shutdown_kills_running_jobs(self, n=3):
        manager = Manager(config={"max_jobs": n, "entrypoint": None})
        job_id = manager.run_task(["sleep", "5"])
        job = manager[job_id]
        manager.shutdown()
        self.assertEqual(job.state, JobState.KILLED)
