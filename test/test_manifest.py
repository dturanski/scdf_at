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

import json
import logging
import optparse
import unittest
import scdf_at
import yaml

scdf_at.enable_debug_logging()

from cloudfoundry.config import CloudFoundryDeployerConfig, CloudFoundryATConfig, DataflowConfig, TestConfig, \
    DatasourceConfig
from cloudfoundry.manifest import create_for_scdf, create_for_skipper, spring_application_json

logger = logging.getLogger(__name__)


def indent(i):
    return ' ' * i


class TestManifest(unittest.TestCase):

    def test_spring_application_json(self):
        opts = self.options(['--taskServices', 'mysql'])
        saj = spring_application_json(cf_config=self.config(), options=opts, services=opts.task_services.split(','))
        self.assertEqual({"remoteRepositories": {"repo0": {"url": "https://repo.spring.io/libs-snapshot"}}},
                         saj['maven'])
        self.assertEqual({'url': 'https://api.mycf.org', 'org': 'org', 'space': 'space',
                          'domain': 'apps.mycf.org', 'username': 'user', 'password': 'password'},
                         saj['spring.cloud.dataflow.task.platform.cloudfoundry.accounts']['default']['connection'])

    def test_basic_dataflow_manifest(self):
        opts = self.options(['--taskServices', 'mysql', '--scdfServices', 'mysql'])
        manifest = create_for_scdf(cf_config=self.config(), options=opts)
        doc = yaml.safe_load(manifest)
        app = doc['applications'][0]
        self.assertEqual(app['name'], 'dataflow-server')
        self.assertEqual(app['buildpack'], 'java_buildpack_offline')
        self.assertEqual(app['path'], 'test/dataflow.jar')
        self.assertEqual(app['env']['SPRING_DATASOURCE_URL'], 'jdbc://oracle:thin:123.456.78:1234/xe/dataflow')
        self.assertEqual(app['services'], ['mysql'])
        saj = json.loads(app['env']['SPRING_APPLICATION_JSON'])
        self.assertEqual(
            saj['spring.cloud.dataflow.task.platform.cloudfoundry.accounts']['default']['deployment']['services'],
            ['mysql'])

    def test_basic_skipper_manifest(self):
        opts = self.options(['--streamServices', 'rabbit', '--skipperServices', 'mysql'])
        manifest = create_for_skipper(cf_config=self.config(), options=opts)
        doc = yaml.safe_load(manifest)
        app = doc['applications'][0]
        self.assertEqual(app['name'], 'skipper-server')
        self.assertEqual(app['buildpack'], 'java_buildpack_offline')
        self.assertEqual(app['path'], 'test/skipper.jar')
        self.assertEqual(app['env']['SPRING_DATASOURCE_URL'], 'jdbc://oracle:thin:123.456.78:1234/xe/skipper')
        self.assertEqual(app['services'],['mysql'])
        saj = json.loads(app['env']['SPRING_APPLICATION_JSON'])
        self.assertEqual(
            saj['spring.cloud.dataflow.task.platform.cloudfoundry.accounts']['default']['deployment']['services'],
            ['rabbit'])


    def config(self):
        deployer_config = CloudFoundryDeployerConfig(api_endpoint="https://api.mycf.org",
                                                     org="org",
                                                     space="space",
                                                     app_domain="apps.mycf.org",
                                                     username="user",
                                                     password="password")

        test_config = TestConfig(dataflow_version='2.10.0-SNAPSHOT',
                                 skipper_version='2.9.0-SNAPSHOT',
                                 skipper_jar_path="test/skipper.jar",
                                 dataflow_jar_path='test/dataflow.jar',
                                 maven_repos={'repo0': 'https://repo.spring.io/libs-snapshot'})
        dataflow_config = DataflowConfig()
        datasources_config = {
            'dataflow': DatasourceConfig(url="jdbc://oracle:thin:123.456.78:1234/xe/dataflow",
                                         username="test",
                                         password="password",
                                         driver_class_name="com.oracle.jdbc.OracleDriver"),
            'skipper': DatasourceConfig(url="jdbc://oracle:thin:123.456.78:1234/xe/skipper",
                                        username="test",
                                        password="password",
                                        driver_class_name="com.oracle.jdbc.OracleDriver")}

        return CloudFoundryATConfig(deployer_config=deployer_config,
                                    dataflow_config=dataflow_config,
                                    test_config=test_config,
                                    datasource_configs=datasources_config)

    def options(self, opts=[]):
        parser = optparse.OptionParser()

        parser.add_option('--taskServices',
                          help='services to bind to tasks',
                          dest='task_services', default=None)
        parser.add_option('--scdfServices',
                          help='services to bind to the dataflow app',
                          dest='scdf_services')
        parser.add_option('--ss', '--streamServices',
                          help='services to bind to streams',
                          dest='stream_services')
        parser.add_option('--se', '--schedulesEnabled',
                          help='cleans the scheduling infrastructure',
                          dest='schedules_enabled', action='store_true')
        parser.add_option('--skipperServices',
                          help='services to bind to the skipper app',
                          dest='skipper_services')

        options, arguments = parser.parse_args(opts)
        return options
