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
import unittest
import scdf_at
import yaml

scdf_at.enable_debug_logging()

from cloudfoundry.config import CloudFoundryDeployerConfig, CloudFoundryATConfig, DataflowConfig, AcceptanceTestsConfig, \
    DatasourceConfig, SkipperConfig, CloudFoundryServicesConfig
from cloudfoundry.manifest import create_for_scdf, create_for_skipper, spring_application_json

logger = logging.getLogger(__name__)


def indent(i):
    return ' ' * i


class TestManifest(unittest.TestCase):

    def test_spring_application_json(self):
        deployment = {'services': ['mysql']}
        platform_accounts_key = 'spring.cloud.dataflow.task.platform.cloudfoundry.accounts'
        saj = spring_application_json(cf_config=self.config(), app_deployment=deployment,
                                      platform_accounts_key=platform_accounts_key)
        self.assertEqual({"remoteRepositories": {"repo0": {"url": "https://repo.spring.io/libs-snapshot"}}},
                         saj['maven'])
        self.assertEqual({'url': 'https://api.mycf.org', 'org': 'org', 'space': 'space',
                          'domain': 'apps.mycf.org', 'username': 'user', 'password': 'password'},
                         saj[platform_accounts_key]['default']['connection'])
        self.assertEqual(
            saj['spring.cloud.dataflow.task.platform.cloudfoundry.accounts']['default']['deployment']['services'],
            ['mysql'])

    def test_basic_dataflow_manifest(self):
        params = {'skipper_uri': 'https://skipper-server.somehost.cf-app.com/api'}
        manifest = create_for_scdf(cf_at_config=self.config(),params=params)
        print(manifest)
        doc = yaml.safe_load(manifest)
        app = doc['applications'][0]
        self.assertEqual(app['name'], 'dataflow-server')
        self.assertEqual(app['buildpack'], 'java_buildpack_offline')
        self.assertEqual(app['path'], 'test/dataflow.jar')
        self.assertEqual(app['env']['SPRING_DATASOURCE_URL'], 'jdbc://oracle:thin:123.456.78:1234/xe/dataflow')
        self.assertEqual(app['env']['SPRING_CLOUD_SKIPPER_CLIENT_SERVER_URI'], params['skipper_uri'])
        self.assertEqual(app['services'], ['mysql'])
        saj = json.loads(app['env']['SPRING_APPLICATION_JSON'])
        self.assertEqual(
            saj['spring.cloud.dataflow.task.platform.cloudfoundry.accounts']['default']['deployment']['services'],
            ['mysql'])

    def test_basic_skipper_manifest(self):
        manifest = create_for_skipper(cf_at_config=self.config())
        doc = yaml.safe_load(manifest)
        app = doc['applications'][0]
        self.assertEqual(app['name'], 'skipper-server')
        self.assertEqual(app['buildpack'], 'java_buildpack_offline')
        self.assertEqual(app['path'], 'test/skipper.jar')
        self.assertEqual(app['env']['SPRING_DATASOURCE_URL'], 'jdbc://oracle:thin:123.456.78:1234/xe/skipper')
        self.assertEqual(app['services'], ['mysql'])
        saj = json.loads(app['env']['SPRING_APPLICATION_JSON'])
        self.assertEqual(
            saj['spring.cloud.skipper.server.platform.cloudfoundry.accounts']['default']['deployment']['services'],
            ['rabbit'])

    def config(self):
        deployer_config = CloudFoundryDeployerConfig(api_endpoint="https://api.mycf.org",
                                                     org="org",
                                                     space="space",
                                                     app_domain="apps.mycf.org",
                                                     username="user",
                                                     password="password")

        test_config = AcceptanceTestsConfig()
        test_config.dataflow_version = '2.10.0-SNAPSHOT'
        test_config.skipper_version = '2.9.0-SNAPSHOT'
        test_config.skipper_jar_path = 'test/skipper.jar'
        test_config.dataflow_jar_path = 'test/dataflow.jar'
        test_config.maven_repos = {'repo0': 'https://repo.spring.io/libs-snapshot'}
        test_config.platform = 'cloudfoundry'
        test_config.task_services = ['mysql']
        test_config.stream_services = ['rabbit']
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

        cf_at_config = CloudFoundryATConfig(deployer_config=deployer_config,
                                            dataflow_config=dataflow_config,
                                            skipper_config=SkipperConfig(),
                                            services_config=CloudFoundryServicesConfig.defaults(),
                                            test_config=test_config)
        cf_at_config.datasources_config = datasources_config
        return cf_at_config
