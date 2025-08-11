import argparse

import jobaman.jobs.manager
import jobaman.logger
from jobaman.api.server import run_server
from jobaman.config import Configuration
from jobaman.helpers import run_command

log = jobaman.logger.get_logger(__name__)


def main():

    config = read_configuration()

    jobaman.logger.configure(config)
    manager = jobaman.jobs.manager.Manager(config)
    config["manager"] = manager

    log.debug("jobaman config:")
    for key, value in config.as_dict().items():
        log.debug("%s=%s", key, value)

    run_command(config["startup_command"], "startup")

    try:
        run_server(config)
    except KeyboardInterrupt:
        log.info("shutting down on user interrupt")
    except Exception as e:
        log.error("fatal error: %s", e)
    finally:
        manager.shutdown()

    run_command(config["shutdown_command"], "shutdown")


def read_configuration():
    config = Configuration()

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

    return config


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
