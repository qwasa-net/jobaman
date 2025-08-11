import os
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


def get_pids_by_ppid(ppid):
    pids = []
    ppid_index = 3
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/stat", "r") as f:
                stat = f.read().split()
                if len(stat) > ppid_index and int(stat[ppid_index]) == ppid:
                    pids.append(int(pid))
        except Exception:
            continue
    return pids


def human_time(seconds):
    minute = 60
    hour = minute * 60
    day = hour * 24
    if seconds < minute:
        return f"{seconds:.0f}s"
    if seconds < hour:
        return f"{seconds // minute:.0f}m{seconds % minute:.0f}s"
    if seconds < day:
        return f"{seconds // hour:.0f}h{(seconds % hour) // minute:.0f}m"
    return f"{seconds // day:.0f}d{(seconds % day) // hour:.0f}h:{(seconds % hour) // minute:.0f}m"
