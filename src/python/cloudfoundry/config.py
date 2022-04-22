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


def set_by_name_if_present(key, env, obj, transform=None):
    val = None
    if env.get(key):
        val = transform(env.get(key)) if transform else env.get(key)
        setattr(obj, key.lower(), val)
    return val


class AcceptanceTestsConfig(JSonEnabled):
    """
    """

    @classmethod
    def from_env_vars(cls, env=os.environ):
        config = AcceptanceTestsConfig()
        set_by_name_if_present('PLATFORM', env, config)
        set_by_name_if_present('BINDER', env, config)
        set_by_name_if_present('DATAFLOW_VERSION', env, config)
        set_by_name_if_present('SKIPPER_VERSION', env, config)
        set_by_name_if_present('DATAFLOW_JAR_PATH', env, config)
        set_by_name_if_present('SKIPPER_JAR_PATH', env, config)
        set_by_name_if_present('DEPLOY_WAIT_SEC', env, config, lambda val: int(val))
        set_by_name_if_present('MAX_RETRIES', env, config, lambda val: int(val))
        set_by_name_if_present('BUILDPACK', env, config)
        set_by_name_if_present('MAVEN_REPOS', env, config, lambda val: json.loads(val))
        set_by_name_if_present('TRUST_CERT', env, config)
        set_by_name_if_present('SCHEDULER_ENABLED', env, config, lambda val: val.lower() in ['y', 'yes', 'true'])
        set_by_name_if_present('CONFIG_SERVER_ENABLED', env, config, lambda val: val.lower() in ['y', 'yes', 'true'])
        set_by_name_if_present('TASK_SERVICES', env, config, lambda val: val.split(','))
        set_by_name_if_present('STREAM_SERVICES', env, config, lambda val: val.split(','))
        return config

    def __init__(self):
        self.platform = 'tile'
        self.binder = 'rabbit'
        self.dataflow_version = None
        self.skipper_version = None
        self.dataflow_jar_path = './build/dataflow-server.jar'
        self.skipper_jar_path = './build/skipper-server.jar'
        self.deploy_wait_sec = 20
        self.max_retries = 60  # 10 min max wait time for a service or app to come up
        self.buildpack = 'java_buildpack_offline'
        self.maven_repos = {'repo1': 'https://repo.spring.io/libs-snapshot'}
        self.jbp_jre_version = '1.8 +'
        self.scheduler_enabled = False
        self.config_server_enabled = False
        self.task_services = ['sql']
        self.stream_services = ['rabbit']


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
    def assert_required_keys(cls, env):
        assert_required_keys(cls, env, [cls.url_key, cls.org_key, cls.space_key, cls.username_key, cls.password_key])

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        if not env.get(cls.url_key):
            cls.assert_required_keys(env)

        skip_ssl_validation = False
        if env.get(cls.skip_ssl_validation_key) and env.get(cls.skip_ssl_validation_key).lower() in ['true', 'y',
                                                                                                     'yes']:
            skip_ssl_validation = True

        return CloudFoundryDeployerConfig(api_endpoint=env.get(cls.url_key),
                                          org=env.get(cls.org_key),
                                          space=env.get(cls.space_key),
                                          app_domain=env.get(cls.app_domain_key),
                                          username=env.get(cls.username_key),
                                          password=env.get(cls.password_key),
                                          skip_ssl_validation=skip_ssl_validation,
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
    provider_key = prefix + 'PROVIDER'
    host_key = prefix + 'HOST'
    port_key = prefix + 'PORT'
    username_key = prefix + 'USERNAME'
    password_key = prefix + 'PASSWORD'
    index_key = prefix + 'INDEX'

    @classmethod
    def assert_required_keys(cls, env):
        assert_required_keys(cls, env, [cls.provider_key, cls.host_key, cls.port_key, cls.username_key, cls.password_key,
                                   cls.index_key])

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        if not env.get(cls.prefix + 'PROVIDER'):
            logger.warning("%s is not defined in the OS environment" % (cls.prefix + 'PROVIDER'))
            return None

        return DBConfig(host=env.get(cls.host_key),
                        port=env.get(cls.port_key),
                        username=env.get(cls.username_key),
                        password=env.get(cls.password_key),
                        provider=env.get(cls.provider_key),
                        index=env.get(cls.index_key))

    def __init__(self, host, port, username, password, provider, index='0'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.provider = provider
        self.index = index


# Doesn't map to env. Created on the fly in db.py
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
        self.validate()

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
    broker_address_key = prefix + 'BROKER_ADDRESS'
    username_key = prefix + 'USERNAME'
    password_key = prefix + 'PASSWORD'

    @classmethod
    def assert_required_keys(cls, env):
        assert_required_keys(cls, env, [cls.broker_address_key, cls.username_key, cls.password_key])

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        if not env.get(cls.broker_address_key):
            logger.debug(
                "%s is not defined in the environment. Skipping Kafka config" % (cls.broker_address_key))
            return None

        return KafkaConfig(broker_address=os.getenv(cls.broker_address_key),
                           username=os.getenv(cls.username_key),
                           password=os.getenv(cls.password_key))

    def __init__(self, broker_address, username, password):
        self.broker_address = broker_address
        self.username = username
        self.password = password
        self.validate()

    def validate(self):
        if not self.broker_address:
            raise ValueError("'broker_address' is required")
        if not self.username:
            raise ValueError("'username' is required")
        if not self.password:
            raise ValueError("'password' is required")

    def as_env(self):
        return {KafkaConfig.broker_address_key: '"%s"' % self.broker_address,
                KafkaConfig.username_key: self.username,
                KafkaConfig.password_key: self.password,
                }


class DataflowConfig(JSonEnabled):
    prefix = 'SPRING_CLOUD_DATAFLOW_'
    streams_enabled_key = prefix + 'FEATURES_STREAMS_ENABLED'
    tasks_enabled_key = prefix + 'FEATURES_TASKS_ENABLED'
    schedules_enabled_key = prefix + 'FEATURES_SCHEDULES_ENABLED'
    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        config = DataflowConfig(env)
        set_by_name_if_present(cls.streams_enabled_key, env, config)
        set_by_name_if_present(cls.tasks_enabled_key, env, config)
        set_by_name_if_present(cls.schedules_enabled_key, env, config)

        return config

    def __init__(self, env={}):
        self.streams_enabled = True
        self.tasks_enabled = True
        self.schedules_enabled = False
        self.env = env
        self.validate()

    def validate(self):
        if not self.streams_enabled and not self.tasks_enabled:
            raise ValueError("One 'streams_enabled' or 'tasks_enabled' must be true")
        if self.schedules_enabled and not self.tasks_enabled:
            raise ValueError("'schedules_enabled' requires 'tasks_enabled' to be true")

    def as_env(self):
        return self.env | {DataflowConfig.streams_enabled_key:  self.streams_enabled,
                DataflowConfig.tasks_enabled_key: self.tasks_enabled,
                DataflowConfig.schedules_enabled_key: self.schedules_enabled
                }

class SkipperConfig(JSonEnabled):
    prefix = 'SPRING_CLOUD_SKIPPER_'

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = env_vars(env, cls.prefix)
        return SkipperConfig(env)

    def __init__(self, env={}):
        self.env = env

    def as_env(self):
        return self.env

class CloudFoundryServicesConfig(JSonEnabled):
    """
    """
    prefix = 'CF_SERVICE_'

    @classmethod
    def from_env_vars(cls, env=os.environ):
        services = env_vars(env, cls.prefix)
        cf_services = {}
        for service in services:
            cf_services[service.name] = ServiceConfig.of_service(service)
        return cf_services if cf_services else cls.defaults()

    @classmethod
    def defaults(cls):
        return {'rabbit': ServiceConfig.rabbit_default(),
                'sql': ServiceConfig.sql_default(),
                'scheduler': ServiceConfig.scheduler_default(),
                'config': ServiceConfig.config_default(),
                'dataflow': ServiceConfig.dataflow_default()
                }


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

    @classmethod
    def dataflow_default(cls):
        return ServiceConfig(name="dataflow", service="p-dataflow", plan="standard")

    @classmethod
    def config_default(cls):
        return ServiceConfig(name="config-server", service="p.config-server", plan="standard")

    @classmethod
    def sql_default(cls):
        return ServiceConfig(name="mysql", service="p.mysql", plan="standard")

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


class CloudFoundryATConfig(JSonEnabled):
    @classmethod
    def from_env_vars(cls, env=os.environ):
        deployer_config = CloudFoundryDeployerConfig.from_env_vars(env)
        dataflow_config = DataflowConfig.from_env_vars(env)
        db_config = DBConfig.from_env_vars(env)
        test_config = AcceptanceTestsConfig.from_env_vars(env)
        kafka_config = KafkaConfig.from_env_vars(env)
        services_config = CloudFoundryServicesConfig.from_env_vars(env)
        skipper_config = SkipperConfig.from_env_vars(env)

        return CloudFoundryATConfig(deployer_config=deployer_config,
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
        Set during external db initialization, if db_config is present. Otherwise, configure default sql service.
        """
        self.datasources_config = {}
        self.sql_service = None
        self.validate()
        self.configure()
        self.env = env

    def validate(self):
        pass

    def configure(self):

        logger.info("Configuring CloudFoundry Acceptence Test Context for platform %s" % self.test_config.platform)
        if self.test_config.platform == 'cloudfoundry':
            self.configure_for_cloudfoundry()
        elif self.test_config.platform == 'tile':
            self.configure_for_tile()

    def configure_for_tile(self):
        if not self.services_config.get('dataflow'):
            raise ValueError("'dataflow' service is required for tile")
        if not self.deployer_config:
            CloudFoundryDeployerConfig.assert_required_keys(self.env)
            raise ValueError("'deployer_config' is required")

        self.services_config.pop('rabbit', None)
        self.services_config.pop('sql', None)
        if not self.test_config.scheduler_enabled:
            self.services_config.pop('scheduler', None)
        if not self.test_config.config_server_enabled:
            self.services_config.pop('config', None)

    def configure_for_cloudfoundry(self):
        if not self.test_config.dataflow_version:
            raise ValueError("'dataflow_version' is required")
        if not self.test_config.dataflow_jar_path:
            raise ValueError("'dataflow_jar_path' is required")

        if self.dataflow_config.streams_enabled:
            if not self.skipper_config:
                raise ValueError("Skipper config is required")
            if not self.test_config.skipper_version:
                raise ValueError("'skipper_version' is required")
            if not self.test_config.skipper_jar_path:
                raise ValueError("'skipper_jar_path' is required")

        if not self.services_config:
            raise ValueError("'services_config' is required")

        if not self.deployer_config:
            CloudFoundryDeployerConfig.assert_required_keys(self.env)

        if self.db_config:
            logger.debug("External DB config, removing configured SQL service")
            self.services_config.pop('sql', None)
        else:
            if not self.services_config.get('sql'):
                DBConfig.assert_required_keys(self.env)

        if not self.test_config.binder == 'rabbit':
            logger.debug('removing rabbit service for binder %s' % self.test_config.binder)
            self.services_config.pop('rabbit', None)

        if not self.test_config.scheduler_enabled:
            logger.debug('Scheduler is not enabled. Removing scheduler service')
            self.services_config.pop('scheduler', None)
        if not self.test_config.config_server_enabled:
            logger.debug('Config Server is not enabled. Removing config service')
            self.services_config.pop('config', None)
        if not self.kafka_config and self.test_config.binder == 'kafka':
            KafkaConfig.assert_required_keys(self.env)


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


def required_env_names(names):
    s = ''
    for i in range(0, len(names)):
        s += names[i]
        if i < len(names) - 1:
            s = s + '\n'
    return s


def assert_required_keys(cls, env, required_keys):
    for key in required_keys:
        if not env.get(key):
            raise ValueError(
                "A required environment variable is missing. The following required keys are bound to %s\n%s" % (
                    cls.__name__, required_env_names(required_keys)))
