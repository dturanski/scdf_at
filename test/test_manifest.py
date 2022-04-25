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

import yaml

import scdf_at
from cloudfoundry.cli import CloudFoundry
from cloudfoundry.platform.config.db import DatasourceConfig
from cloudfoundry.platform.config.kafka import KafkaConfig
from cloudfoundry.platform.config.skipper import SkipperConfig
from cloudfoundry.platform.config.dataflow import DataflowConfig
from cloudfoundry.platform.config.at_config import AcceptanceTestsConfig
from cloudfoundry.platform.config.deployer import CloudFoundryDeployerConfig
from cloudfoundry.platform.config.service import CloudFoundryServicesConfig
from cloudfoundry.platform.config.at import CloudFoundryPlatformConfig

import cloudfoundry.platform.manifest.skipper as skipper_manifest
import cloudfoundry.platform.manifest.dataflow as dataflow_manifest
from cloudfoundry.platform.manifest.util import spring_application_json
from cloudfoundry.platform.standalone import deploy
from scdf_at.shell import Shell

scdf_at.enable_debug_logging()

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
        manifest = dataflow_manifest.create_manifest(cf_at_config=self.config(), params=params)
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

    def test_dataflow_manifest_with_kafka(self):
        params = {'skipper_uri': 'https://skipper-server.somehost.cf-app.com/api'}
        config = self.config()
        config.test_config.platform = 'kafka'
        cf_at_config = cf_at_config = CloudFoundryPlatformConfig(deployer_config=config.deployer_config,
                                                                 dataflow_config=config.dataflow_config,
                                                                 skipper_config=config.skipper_config,
                                                                 services_config=config.services_config,
                                                                 kafka_config=KafkaConfig(broker_address="12.345.678.89:9092",
                                                                                    username='user',
                                                                                    password='password'),
                                                                 test_config=config.test_config)


        manifest = dataflow_manifest.create_manifest(cf_at_config=config, params=params)
        print(manifest)
        cf = CloudFoundry(test_config=config.test_config, deployer_config=config.deployer_config, shell=Shell(dry_run=True))
        deploy(cf=cf, cf_config=config, create_manifest=dataflow_manifest.create_manifest, application_name='dataflow-server',
               manifest_path='test.yml')

        doc = yaml.safe_load(manifest)
        app = doc['applications'][0]


    def test_basic_skipper_manifest(self):
        manifest = skipper_manifest.create_manifest(cf_at_config=self.config())
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
        deployer_env = {
            CloudFoundryDeployerConfig.scheduler_url_key:
                "'https://scheduler.sys.somehost.cf-app.com'",
            'SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_AUTO_DELETE_MAVEN_ARTIFACTS': 'false'
        }
        deployer_config = CloudFoundryDeployerConfig(api_endpoint="https://api.mycf.org",
                                                     org="org",
                                                     space="space",
                                                     app_domain="apps.mycf.org",
                                                     username="user",
                                                     password="password",
                                                     env=deployer_env
                                                     )
        test_config = AcceptanceTestsConfig()
        test_config.dataflow_version = '2.10.0-SNAPSHOT'
        test_config.skipper_version = '2.9.0-SNAPSHOT'
        test_config.skipper_jar_path = 'test/skipper.jar'
        test_config.dataflow_jar_path = 'test/dataflow.jar'
        test_config.maven_repos = {'repo0': 'https://repo.spring.io/libs-snapshot'}
        test_config.platform = 'cloudfoundry'
        test_config.task_services = ['mysql']
        test_config.stream_services = ['rabbit']
        test_config.scheduler_enabled = True
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

        cf_at_config = CloudFoundryPlatformConfig(deployer_config=deployer_config,
                                                  dataflow_config=dataflow_config,
                                                  skipper_config=SkipperConfig(),
                                                  services_config=CloudFoundryServicesConfig.defaults(),
                                                  test_config=test_config)
        cf_at_config.datasources_config = datasources_config
        return cf_at_config
