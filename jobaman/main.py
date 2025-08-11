import argparse
import time

import jobaman.jobs
import jobaman.logger
from jobaman.config import config

log = jobaman.logger.get_logger()


def main():

    params = parse_cli_params()

    ini_path = params.pop("ini_path", None)
    ini_section = params.pop("ini_section", None)
    env_prefix = params.pop("env_prefix", "JOBAMAN")
    env_use = params.pop("env_use", True)

    config.configure(
        params=params,
        ini_path=ini_path,
        ini_section=ini_section,
        env_use=env_use,
        env_prefix=env_prefix,
    )

    jobaman.logger.configure(
        level=config.get("log-level", "INFO"),
        log_format=config.get("log-format"),
    )

    log.debug("jobaman config:")
    for key, value in config.as_dict().items():
        log.debug("%s=%s", key, value)

    run(config)


def run(cfg):

    man = jobaman.jobs.manager

    # FIXME # FIXME # FIXME
    command = ["/bin/bash", "-c", "echo 'hallo!'; sleep 2; ls /hallo; echo 'bye!'; exit ${RANDOM}"]
    for _i in range(3):
        job_id = man.run_task(command)
        job = man[job_id]
        print(f"{job_id=}, {job=} {len(man)=}")

    time.sleep(3.3)

    for job_id, job in man.jobs.items():
        print(f"{job_id=}, {job=}, \n{job.stdout=}\n{job.stderr=}")


def parse_cli_params():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ini-path", type=str)
    parser.add_argument("--ini-section", type=str)
    parser.add_argument("--env-use", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--env-prefix", type=str, default="JOBAMAN")
    parser.add_argument("--log-level", type=str)
    parser.add_argument("--debug", action=argparse.BooleanOptionalAction, default=None)
    params, _ = parser.parse_known_args()

    if params.debug is True:
        params.log_level = "DEBUG"

    return {k: v for k, v in vars(params).items() if v is not None}


if __name__ == "__main__":
    main()
