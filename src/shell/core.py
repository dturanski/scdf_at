import subprocess
import shlex
import logging

logger = logging.getLogger(__name__)

class Shell:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def exec(self, cmd):
        args = shlex.split(cmd)
        if self.dry_run:
            proc = subprocess.CompletedProcess(args, 0)
            return proc
        else:
            return subprocess.run(args, capture_output=True)


class Utils:

    @classmethod
    def log_stdout(cls, completed_proc):
        print(cls.stdout_to_s(completed_proc))

    @classmethod
    def stdout_to_s(cls, completed_proc):
        return completed_proc.stdout.decode() if completed_proc.stdout else ""

    @classmethod
    def log_stderr(cls, completed_proc):
        logger.info(completed_proc.stderr.decode() if completed_proc.stdout else "")

    @classmethod
    def log_command(cls, completed_proc, msg=""):
        logger.info(msg + ": " + shlex.join(completed_proc.args))
