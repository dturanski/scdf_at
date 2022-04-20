__copyright__ = '''
Copyright 2022 the original author or authors.
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
      http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
'''

__author__ = 'David Turanski'

import unittest
from cloudfoundry.cli import CloudFoundry
from cloudfoundry.config import CloudFoundryDeployerConfig, ServiceConfig, CloudFoundryATConfig, TestConfig
from scdf_at.shell import Shell


class TestCommands(unittest.TestCase):

    def test_basic_shell(self):
        shell = Shell()
        p = shell.exec("ls -l")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(['ls', '-l'], p.args)
        shell.log_stdout(p)

    def test_target(self):
        cf = self.cloudfoundry()
        p = cf.target(org='p-dataflow', space='dturanski')
        self.assertEqual(['cf', 'target', '-o', 'p-dataflow', '-s', 'dturanski'], p.args)

    def test_push(self):
        cf = self.cloudfoundry()
        p = cf.push("-f scdf-server.yml")
        self.assertEqual(['cf', 'push', '-f', 'scdf-server.yml'], p.args)

    def test_login(self):
        cf = self.cloudfoundry()
        p = cf.login()
        self.assertEqual(['cf', 'login', '-a', 'https://api.mycf.org', '-o', 'org', '-s', 'space',
                          '-u', 'user', '-p', 'password', '--skip-ssl-validation'], p.args)

    def test_delete_all(self):
        cf = self.cloudfoundry()
        apps = ['scdf-app-repo', 'skipper-server-1411', 'dataflow-server-19655', 'LKg7lBB-taphttp-log-v1',
                'LKg7lBB-taphttp-http-v1', 'LKg7lBB-tapstream-log-v1']

        apps.remove('scdf-app-repo')

        cf.delete_all(apps)

    def test_create_service(self):
        cf = self.cloudfoundry()
        p = cf.create_service(service_config=ServiceConfig(name="rabbit", service="p.rabbitmq", plan="single-node"))
        self.assertEqual(['cf', 'create-service', 'p.rabbitmq', 'single-node', 'rabbit'], p.args)

    def cloudfoundry(self):
        config = self.config()
        return CloudFoundry(deployer_config=config.deployer_config, test_config=config.test_config,
                          shell=Shell(dry_run=True))


    def config(self):
        deployer_config = CloudFoundryDeployerConfig(api_endpoint="https://api.mycf.org",
                                                     org="org",
                                                     space="space",
                                                     app_domain="apps.mycf.org",
                                                     username="user",
                                                     password="password")
        return CloudFoundryATConfig(deployer_config=deployer_config,
                                    test_config=TestConfig(dataflow_version='2.1.0-SNAPSHOT',
                                                           skipper_version='2.9.0-SNAPSHOT'))
