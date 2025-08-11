import subprocess

import jobaman.logger

log = jobaman.logger.get_logger(__name__)


def synchronized(method):
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)

    return wrapper


def run_command(command, name):
    if not command:
        return
    log.info("running `%s` command: `%.512s`", name, command)
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        log.error("`%s` command error: %s", name, e)
