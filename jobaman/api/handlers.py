import time

from jobaman.logger import get_logger

from .query import Query

log = get_logger(__name__)


def handle(query, config):
    for route, handler in ROUTING_TABLE:
        if route.method is None or query.method == route.method:
            if route.path == "*" or str(query.path).startswith(route.path):
                return handler(query, config)
    return 404, {}


def handle_ping(query, config=None):
    rsp = {"message": "pong", "ts": int(time.time())}
    return 200, rsp


def handle_run_job(query, config):
    cmd = query.params_to_args()
    job_id = query.get_param("__job_id", None)
    try:
        real_job_id = config.manager.run_task(cmd, job_id=job_id)
    except ValueError as e:
        return 400, {"error": str(e)}
    return 200, {
        "job_id": real_job_id,
        "running": config.manager.running_jobs_count,
    }


def handle_list_jobs(query, config):
    rsp = {
        "jobs": {
            job_id: {
                "state": job.state,
                "pid": job.process.pid,
                "exit_code": job.exit_code,
                "ts_started": job.ts_started,
                "ts_completed": job.ts_completed,
                "kill-link": f"{config.server_base_url}/jobs/kill?__job_id={job_id}",
                "output-link": f"{config.server_base_url}/jobs/output?__job_id={job_id}",
            }
            for job_id, job in config.manager.running_jobs.items()
        }
    }
    rsp["count"] = len(rsp["jobs"])
    return 200, rsp


def handle_kill_job(query, config):
    job_id = query.get_param("__job_id", None)
    try:
        config.manager[job_id].kill()
    except KeyError:
        return 404, {"error": f"job_id {job_id} not found"}
    except Exception as e:
        return 400, {"error": str(e)}
    return 200, {"message": f"job_id {job_id} killed"}


def handle_output_job(query, config):
    job_id = query.get_param("__job_id", None)
    try:
        job = config.manager[job_id]
        stdout = job.stdout
        stderr = job.stderr
    except KeyError:
        return 404, {"error": f"job_id {job_id} not found"}
    except Exception as e:
        return 400, {"error": str(e)}
    return 200, {
        "job_id": job_id,
        "job": str(job),
        "stdout": stdout,
        "stderr": stderr,
    }


ROUTING_TABLE = [
    (Query(method="GET", path="/jobs/run"), handle_run_job),
    (Query(method="GET", path="/jobs/kill"), handle_kill_job),
    (Query(method="GET", path="/jobs/output"), handle_output_job),
    (Query(method="GET", path="/jobs/"), handle_list_jobs),
    (Query(method=None, path="/ping"), handle_ping),
]
