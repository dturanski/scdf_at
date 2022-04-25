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

import logging
import os
import re

from cloudfoundry.platform.config.environment import EnvironmentAware
from cloudfoundry.platform.config.db import DBConfig
from cloudfoundry.platform.config.at_config import AcceptanceTestsConfig
from cloudfoundry.platform.config.deployer import CloudFoundryDeployerConfig
from cloudfoundry.platform.config.service import CloudFoundryServicesConfig
from cloudfoundry.platform.config.dataflow import DataflowConfig
from cloudfoundry.platform.config.skipper import SkipperConfig
from cloudfoundry.platform.config.kafka import KafkaConfig

logger = logging.getLogger(__name__)


class CloudFoundryPlatformConfig(EnvironmentAware):
    @classmethod
    def from_env_vars(cls, env=os.environ):
        deployer_config = CloudFoundryDeployerConfig.from_env_vars(env)
        dataflow_config = DataflowConfig.from_env_vars(env)
        db_config = DBConfig.from_env_vars(env)
        test_config = AcceptanceTestsConfig.from_env_vars(env)
        kafka_config = KafkaConfig.from_env_vars(env)
        services_config = CloudFoundryServicesConfig.from_env_vars(env)
        skipper_config = SkipperConfig.from_env_vars(env)

        return CloudFoundryPlatformConfig(deployer_config=deployer_config,
                                          dataflow_config=dataflow_config,
                                          skipper_config=skipper_config,
                                          db_config=db_config,
                                          kafka_config=kafka_config,
                                          test_config=test_config,
                                          services_config=services_config,
                                          env=env
                                          )

    def __init__(self, deployer_config, test_config, dataflow_config=None, skipper_config=None, db_config=None,
                 services_config=None, kafka_config=None, env={}):
        self.deployer_config = deployer_config
        self.dataflow_config = dataflow_config
        self.skipper_config = skipper_config
        self.services_config = services_config
        self.test_config = test_config
        self.db_config = db_config
        self.kafka_config = kafka_config
        """
        Set during external db initialization, if db_config is present. Otherwise must configure default sql service.
        """
        self.datasources_config = {}
        self.validate()
        self.configure(env)

    def validate(self):
        pass

    def configure(self, env):
        logger.info("Configuring CloudFoundry Acceptance Test Context for platform %s" % self.test_config.platform)
        if not self.deployer_config:
            CloudFoundryDeployerConfig.assert_required_keys(env)
            raise ValueError("'deployer_config' is required")

        # TODO: create a function to encapsulate dataflow config
        if self.dataflow_config.streams_enabled and self.kafka_config:
            logger.debug("configuring dataflow instance for Kafka")
            self.dataflow_config.add_kafka_application_properties(self.kafka_config)
            self.remove_required_service('rabbit')
            if 'rabbit' in self.test_config.stream_services:
                logger.warning('removing rabbit from stream services for Kafka binder')
                self.test_config.stream_services.remove('rabbit')
        if self.dataflow_config.tasks_enabled and self.db_config and self.db_config.provider == 'oracle':
            self.dataflow_config.add_oracle_application_properties()

        self.dataflow_config.add_trust_certs_application_properties(self.deployer_config.uaa_host())
        ###

        if not self.dataflow_config.schedules_enabled:
            logger.debug('Scheduler is not enabled. Removing scheduler service')
            self.remove_required_service('scheduler')

        if not self.test_config.cert_host:
            self.test_config.cert_host = self.deployer_config.uaa_host()
        logger.debug('cert_host=%s' % self.test_config.cert_host)

        if self.test_config.platform == 'cloudfoundry':
            self.configure_for_cloudfoundry(env)
        elif self.test_config.platform == 'tile':
            self.configure_for_tile(env)

    def configure_for_tile(self, env):
        if not self.services_config or not self.services_config.get('dataflow'):
            raise ValueError("'dataflow' service is required for tile")
        self.remove_required_service('rabbit')
        self.remove_required_service('sql')
        if not self.test_config.config_server_enabled:
            self.remove_required_service('config')

    def configure_for_cloudfoundry(self, env):
        self.remove_required_service('dataflow')
        if not self.test_config.dataflow_version:
            raise ValueError("'dataflow_version' is required")
        if not self.test_config.dataflow_jar_path:
            raise ValueError("'dataflow_jar_path' is required")

        if self.dataflow_config and self.dataflow_config.streams_enabled:
            if not self.test_config.skipper_version:
                raise ValueError("'skipper_version' is required")
            if not self.test_config.skipper_jar_path:
                raise ValueError("'skipper_jar_path' is required")

        if not self.services_config:
            raise ValueError("'services_config' is required")

        if not self.deployer_config:
            CloudFoundryDeployerConfig.assert_required_keys(env)

        if self.db_config:
            logger.debug("External DB config, removing configured SQL service")
            self.remove_required_service('sql')
            self.test_config.task_services = []
        else:
            if not self.services_config.get('sql'):
                logger.error("No external DB or SQL service is configured")
                DBConfig.assert_required_keys(env)

        if not self.test_config.binder == 'rabbit':
            logger.debug('removing rabbit service for binder %s' % self.test_config.binder)
            self.remove_required_service('rabbit')

        if not self.test_config.config_server_enabled:
            logger.debug('Config Server is not enabled. Removing config service')
            self.remove_required_service('config')
        if self.test_config.binder == 'kafka':
            if not self.kafka_config:
                KafkaConfig.assert_required_keys(env)

    def remove_required_service(self, service_key):
        # Safe if key doesn't exist
        logger.debug("removing %s from required services" % service_key)
        if self.services_config:
            self.services_config.pop(service_key, None)
        else:
            logger.warning("No services are configured.")
