import unittest
from cloudfoundry.cli import CloudFoundry
from cloudfoundry.config import CloudFoundryDeployerConfig, ServiceConfig, CloudFoundryConfig
import shell
from shell import Shell
import json_fix

json_fix.patch()


class TestCommands(unittest.TestCase):

    def test_basic_shell(self):
        shell = Shell()
        p = shell.exec("ls -l")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(['ls', '-l'], p.args)
        shell.log_stdout(p)

    def test_target(self):
        cf = CloudFoundry(deployer_config=self.config().deployer_config, shell=Shell(dry_run=True))
        p = cf.target(org='p-dataflow', space='dturanski')
        self.assertEqual(['cf', 'target', '-o', 'p-dataflow', '-s', 'dturanski'], p.args)

    def test_push(self):
        cf = CloudFoundry(deployer_config=self.config().deployer_config, shell=Shell(dry_run=True))
        p = cf.push("-f scdf-server.yml")
        self.assertEqual(['cf', 'push', '-f', 'scdf-server.yml'], p.args)

    def test_login(self):
        cf = CloudFoundry(deployer_config=self.config().deployer_config, shell=Shell(dry_run=True))
        p = cf.login()
        self.assertEqual(['cf', 'login', '-a', 'https://api.mycf.org', '-o', 'org', '-s', 'space',
                          '-u', 'user', '-p', 'password', '--skip-ssl-validation'], p.args)

    def test_delete_all(self):
        cf = CloudFoundry(deployer_config=self.config().deployer_config, shell=Shell(dry_run=True))
        apps = ['scdf-app-repo', 'skipper-server-1411', 'dataflow-server-19655', 'LKg7lBB-taphttp-log-v1',
                'LKg7lBB-taphttp-http-v1', 'LKg7lBB-tapstream-log-v1']

        apps.remove('scdf-app-repo')

        cf.delete_all(apps)

    def test_create_service(self):
        cf = CloudFoundry(deployer_config=self.config().deployer_config, shell=Shell(dry_run=True))
        p = cf.create_service(service_config=ServiceConfig(name="rabbit", service="p.rabbitmq", plan="single-node"))
        self.assertEqual(['cf', 'create-service', 'p.rabbitmq', 'single-node', 'rabbit'], p.args)

    def config(self):
        deployer_config = CloudFoundryDeployerConfig(api_endpoint="https://api.mycf.org",
                                                     org="org",
                                                     space="space",
                                                     app_domain="apps.mycf.org",
                                                     username="user",
                                                     password="password")
        return CloudFoundryConfig(deployer_config=deployer_config)
