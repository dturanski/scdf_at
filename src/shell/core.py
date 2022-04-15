import subprocess
import shlex


class Shell:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def exec(self, cmd):
        args = shlex.split(cmd)
        if self.dry_run:
            return subprocess.CompletedProcess(args, 0)
        else:
            return subprocess.run(shlex.split(cmd), capture_output=True)


class Utils:

    @classmethod
    def log_stdout(cls, completed_proc):
        print(cls.stdout_to_s(completed_proc))

    @classmethod
    def stdout_to_s(cls, completed_proc):
        return completed_proc.stdout.decode()

    @classmethod
    def log_stderr(cls, completed_proc):
        print(completed_proc.stdout.decode())

    @classmethod
    def log_command(cls, completed_proc, msg=""):
        print(msg + ": " + shlex.join(completed_proc.args))
