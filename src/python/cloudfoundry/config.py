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
import os

from cloudfoundry.domain import JSonEnabled

logger = logging.getLogger(__name__)


def env_vars(env, prefix):
    if not prefix:
        logger.warning("no environment variable prefix is set")
    if not prefix:
        return env
    prefixed_env = {}
    for (key, value) in env.items():
        if key.startswith(prefix):
            prefixed_env[key] = value
    return prefixed_env


class TestConfig(JSonEnabled):
    @classmethod
    def from_env_vars(cls, env=os.environ):
        dataflow_version =  env.get('DATAFLOW_VERSION')
        skipper_version = env.get('SKIPPER_VERSION')
        dataflow_jar_path = env.get('DATAFLOW_JAR_PATH')
        skipper_jar_path = env.get('SKIPPER_JAR_PATH')
        deploy_wait_sec = int(env.get('DEPLOY_WAIT_SEC')) if env.get('DEPLOY_WAIT_SEC') else None
        max_retries = int(env.get('MAX_RETRIES')) if env.get('MAX_RETRIES') else None
        buildpack = env.get('BUILDPACK') if env.get('BUILDPACK') else None
        jbp_jre_version = env.get('JBP_JRE_VERSION')
        maven_repos = json.loads(env.get('MAVEN_REPOS')) if env.get('MAVEN_REPOS') else None

        return TestConfig(
            dataflow_version=dataflow_version,
            skipper_version=skipper_version,
            dataflow_jar_path=dataflow_jar_path,
            skipper_jar_path=skipper_jar_path,
            deploy_wait_sec=deploy_wait_sec,
            max_retries=max_retries,
            buildpack=buildpack,
            maven_repos=maven_repos,
            jbp_jre_version=jbp_jre_version)

    def __init__(self,
                 dataflow_version=None,
                 skipper_version=None,
                 dataflow_jar_path=None,
                 skipper_jar_path=None,
                 deploy_wait_sec=None,
                 max_retries=None,
                 buildpack=None,
                 maven_repos=None,
                 jbp_jre_version=None):
        # TODO: All the not used for tile is a code smell. Maybe refactor for different TestConfig and options
        """
        These all named for corresponding environment variables.
        :param dataflow_version: Not used for Tile. the maven version for dataflow server
        :param skipper_version: Not used for Tile. the maven version for skipper server
        :param dataflow_jar_path: Not used for Tile. the dataflow jar path
        :param skipper_jar_path: Not used for Tile. the skipper jar path
        :param deploy_wait_sec: time to wait before polling the status of service and app create and delete operations
        :param max_retries: maximum number of polls
        :param buildpacks: Not used for Tile. Must be a java build pack for Spring Boot apps, typically no need to change this.
        unless you want to try something java with a custom build pack, or override the default version to investigate JRE issues
        :param maven_repos: Not used for Tile. Normally no need to change this.
        :param jbp_jre_version: Not used for Tile. If you need to test a different runtime JRE version for the container
        Note: Usedd conditional expressions instead of default arg values here b/c all are normally set even if None.
        """
        if not dataflow_version:
            raise ValueError("'dataflow_version' is required")
        if not skipper_version:
            raise ValueError("'We could assume the skipper version is, and will always be, the same major version and minor version-1 relative to dataflow."
                             "Would be a fun use of regex, but it's probably a bad idea. So you have to set it")
        self.dataflow_version = dataflow_version
        self.skipper_version = skipper_version
        self.deploy_wait_sec = deploy_wait_sec if deploy_wait_sec else 20
        self.max_retries = max_retries if max_retries else 30  # 10 min max wait time for a service or app to come up
        self.buildpack = buildpack if buildpack else 'java_buildpack_offline'
        self.maven_repos = maven_repos if maven_repos else {'repo1': 'https://repo.spring.io/libs-snapshot'}
        self.jbp_jre_version = jbp_jre_version if jbp_jre_version else '1.8 +'
        self.dataflow_jar_path = dataflow_jar_path
        self.skipper_jar_path = skipper_jar_path


class CloudFoundryDeployerConfig(JSonEnabled):
    prefix = "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_"
    url_key = prefix + "URL"
    org_key = prefix + "ORG"
    space_key = prefix + "SPACE"
    app_domain_key = prefix + "DOMAIN"
    username_key = prefix + "USERNAME"
    password_key = prefix + "PASSWORD"
    skip_ssl_validation_key = prefix + "SKIP_SSL_VALIDATION"

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        if not env.get(cls.url_key):
            raise ValueError(cls.url_key + " is not configured in environment")

        return CloudFoundryDeployerConfig(api_endpoint=env.get(cls.url_key),
                                          org=env.get(cls.org_key),
                                          space=env.get(cls.space_key),
                                          app_domain=env.get(cls.app_domain_key),
                                          username=env.get(cls.username_key),
                                          password=env.get(cls.password_key),
                                          skip_ssl_validation=env.get(cls.skip_ssl_validation_key),
                                          env=env)

    def __init__(self, api_endpoint, org, space, app_domain, username, password, skip_ssl_validation=True,
                 env=None):
        # Besides the required props,we will put these in the scdf_server manifest
        self.env = env
        self.api_endpoint = api_endpoint
        self.org = org
        self.space = space
        self.app_domain = app_domain
        self.username = username
        self.password = password
        self.skip_ssl_validation = skip_ssl_validation
        self.env = env
        self.validate()

    def connection(self):
        return {'url': self.api_endpoint, 'org': self.org, 'space': self.space, 'domain': self.app_domain,
                'username': self.username, 'password': self.password}

    def validate(self):
        if not self.api_endpoint:
            raise ValueError("'api_endpoint' is required")
        if not self.org:
            raise ValueError("'org' is required")
        if not self.space:
            raise ValueError("'space' is required")
        if not self.app_domain:
            raise ValueError("'app_domain' is required")
        if not self.username:
            raise ValueError("'username' is required")
        if not self.password:
            raise ValueError("'password' is required")


class DBConfig(JSonEnabled):
    prefix = "SQL_"

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        if not env.get(cls.prefix + 'HOST'):
            logger.warning("%s is not defined in the OS environment" % (cls.prefix + 'HOST'))
            return None

        return DBConfig(host=env.get(cls.prefix + 'HOST'),
                        port=env.get(cls.prefix + 'PORT'),
                        username=env.get(cls.prefix + 'USERNAME'),
                        password=env.get(cls.prefix + 'PASSWORD'),
                        provider=env.get(cls.prefix + 'PROVIDER'),
                        index=env.get(cls.prefix + 'INDEX'))

    def __init__(self, host, port, username, password, provider, index='0'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.provider = provider
        self.index = index


class DatasourceConfig(JSonEnabled):
    prefix = "SPRING_DATASOURCE_"
    url_key = prefix + "URL"
    username_key = prefix + "USERNAME"
    password_key = prefix + "PASSWORD"
    driver_class_name_key = prefix + 'DRIVER_CLASS_NAME'

    def __init__(self, url, username, password, driver_class_name):
        self.url = url
        self.username = username
        self.password = password
        self.driver_class_name = driver_class_name

    def validate(self):
        if not self.url:
            raise ValueError("'url' is required")
        if not self.username:
            raise ValueError("'username' is required")
        if not self.password:
            raise ValueError("'password' is required")
        if not self.driver_class_name:
            raise ValueError("'driver_class_name' is required")

    def as_env(self):
        return {DatasourceConfig.url_key: '"%s"' % self.url,
                DatasourceConfig.username_key: self.username,
                DatasourceConfig.password_key: self.password,
                DatasourceConfig.driver_class_name_key: self.driver_class_name}


class KafkaConfig(JSonEnabled):
    prefix = "KAFKA_"

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        if not env.get(cls.prefix + 'BROKER_ADDRESS'):
            logger.debug(
                "%s is not defined in the environment. Skipping Kafka config" % (cls.prefix + 'BROKER_ADDRESS'))
            return None

        return KafkaConfig(broker_address=os.getenv(cls.prefix + 'BROKER_ADDRESS'),
                           username=os.getenv(cls.prefix + 'USERNAME'),
                           password=os.getenv(cls.prefix + 'PASSWORD'))

    def __init__(self, broker_address, username, password):
        self.broker_address = broker_address
        self.username = username
        self.password = password

    def validate(self):
        if not self.broker_address:
            raise ValueError("'broker_address' is required")
        if not self.username:
            raise ValueError("'username' is required")
        if not self.password:
            raise ValueError("'password' is required")


class ServiceConfig(JSonEnabled):
    def __init__(self, name, service, plan, config=None):
        self.name = name
        self.service = service
        self.plan = plan
        self.config = config
        self.validate()

    def __eq__(self, other):
        if isinstance(other, ServiceConfig):
            return self.name == other.name and self.service and other.service and \
                   self.plan == other.plan and self.config == other.config

    @classmethod
    def of_service(cls, service):
        return ServiceConfig(name=service.name, service=service.service, plan=service.plan)

    @classmethod
    def rabbit_default(cls):
        return ServiceConfig(name="rabbit", service="p.rabbitmq", plan="single-node")

    @classmethod
    def scheduler_default(cls):
        return ServiceConfig(name="ci-scheduler", service="scheduler-for-pcf", plan="standard")

    def validate(self):
        if not self.name:
            raise ValueError("'name' is required")
        if not self.service:
            raise ValueError("'service' is required")
        if not self.plan:
            raise ValueError("'plan' is required")

        if self.config:
            try:
                json.loads(self.config)
            except BaseException:
                raise ValueError("config is not valid json:" + self.config)


class DataflowConfig(JSonEnabled):
    prefix = 'SPRING_CLOUD_DATAFLOW_'

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        streams_enabled = env.get(cls.prefix + "FEATURES_STREAMS_ENABLED", True)
        tasks_enabled = env.get(cls.prefix + "FEATURES_TASKS_ENABLED", True)
        schedules_enabled = env.get(cls.prefix + "FEATURES_SCHEDULES_ENABLED", False)

        return DataflowConfig(streams_enabled, tasks_enabled, schedules_enabled, env)

    def __init__(self, streams_enabled=True, tasks_enabled=True, schedules_enabled=True, env={}):
        self.streams_enabled = streams_enabled
        self.tasks_enabled = tasks_enabled
        self.schedules_enabled = schedules_enabled
        self.env = env

    def validate(self):
        if not self.streams_enabled and not self.tasks_enabled:
            raise ValueError("One 'streams_enabled' or 'tasks_enabled' must be true")
        if self.schedules_enabled and not self.tasks_enabled:
            raise ValueError("'schedules_enabled' requires 'tasks_enabled' to be true")


class SkipperConfig(JSonEnabled):
    prefix = 'SPRING_CLOUD_SKIPPER_'

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        return SkipperConfig(env)

    def __init__(self, env={}):
        self.env = env
        if not env.get('SPRING_PROFILES_ACTIVE'):
            env['SPRING_PROFILES_ACTIVE'] = 'cloud'
        if not env.get('JBP_CONFIG_SPRING_AUTO_RECONFIGURATION'):
            env['JBP_CONFIG_SPRING_AUTO_RECONFIGURATION'] = '{enabled: false}'
        if not env.get('SPRING_APPLICATION_NAME'):
            env['SPRING_APPLICATION_NAME'] = 'skipper-server'


class CloudFoundryATConfig(JSonEnabled):
    @classmethod
    def from_env_vars(cls, env=os.environ):
        deployer_config = CloudFoundryDeployerConfig.from_env_vars(env)
        dataflow_config = DataflowConfig.from_env_vars(env)
        db_config = DBConfig.from_env_vars(env)
        test_config = TestConfig.from_env_vars(env)
        kafka_config = KafkaConfig.from_env_vars()

        return CloudFoundryATConfig(deployer_config=deployer_config, dataflow_config=dataflow_config,
                                    db_config=db_config, kafka_config=kafka_config, test_config=test_config,
                                    datasource_configs=None)

    def __init__(self, deployer_config, test_config, dataflow_config=None, skipper_config=None, db_config=None,
                 service_configs=[ServiceConfig.rabbit_default()], kafka_config=None, datasource_configs={}):
        self.deployer_config = deployer_config
        self.dataflow_config = dataflow_config
        self.skipper_config = skipper_config
        self.service_configs = service_configs
        self.test_config = test_config
        self.db_config = db_config
        self.kafka_config = kafka_config
        # Set later. 1 for dataflow and one for skipper
        self.datasource_configs = datasource_configs
        self.validate()

    def validate(self):
        if not self.deployer_config:
            raise ValueError("'deployer_config' is required")
        if not self.dataflow_config:
            logger.error("Really? No Dataflow config properties? What's the point")
        if not self.skipper_config and self.dataflow_config and not self.dataflow_config.streams_enabled:
            logger.error("Skipper config is required if streams are enabled")
