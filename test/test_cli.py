import unittest
from cloudfoundry.cli import CloudFoundry
from cloudfoundry.config import CloudFoundryConfig
from shell.core import Shell, Utils


class TestCommands(unittest.TestCase):

    def test_basic_shell(self):
        shell = Shell()
        proc = shell.exec("ls -l")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(['ls', '-l'], proc.args)
        Utils.log_stdout(proc)

    def test_target(self):
        cf = CloudFoundry(self.config(), Shell(dry_run=True))
        proc = cf.target(org='p-dataflow', space='dturanski')
        self.assertEqual(proc.args, ['cf', 'target', '-o', 'p-dataflow', '-s', 'dturanski'])

    def test_current_target(self):
        cf = CloudFoundry(self.config())
        print(cf.current_target())

    def test_push(self):
        cf = CloudFoundry(self.config(), Shell(dry_run=True))
        proc = cf.push("-f scdf-server.yml")
        self.assertEqual(proc.args, ['cf', 'push', '-f', 'scdf-server.yml'])

    def test_login(self):
        cf = CloudFoundry(self.config(), Shell(dry_run=True))
        proc = cf.login()
        self.assertEqual(proc.args, ['cf', 'login', '-a', 'https://api.mycf.org', '-o', 'org', '-s', 'space',
                                     '-u', 'user', '-p', 'password', '--skip-ssl-validation'])

    def test_delete_all(self):
        cf = CloudFoundry(self.config(), Shell(dry_run=True))
        apps = ['scdf-app-repo', 'skipper-server-1411', 'dataflow-server-19655', 'LKg7lBB-taphttp-log-v1',
         'LKg7lBB-taphttp-http-v1', 'LKg7lBB-tapstream-log-v1']

        apps.remove('scdf-app-repo')

        cf.delete_all(apps)

    def config(self):
        return CloudFoundryConfig(api_endpoint="https://api.mycf.org",
                                  org="org",
                                  space="space",
                                  app_domain="apps.mycf.org",
                                  username="user",
                                  password="password")
