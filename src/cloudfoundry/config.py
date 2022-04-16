import json, os
import logging

logger = logging.getLogger(__name__)


class Environment:
    def __init__(self, env={}):
        self.env = env

    def add_all(self, env):
        self.env = {**self.env, **env}
        return self.env

    def get(self, key):
        return self.env[key]

    def put(self, key, value):
        self.env[key] = value
        return self.env


class CloudFoundryDeployerConfig(json.JSONEncoder):

    @classmethod
    def from_spring_env_vars(self):
        url_key = "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_URL"
        org_key = "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_ORG"
        space_key = "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_SPACE"
        domain_key = "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_DOMAIN"
        username_key = "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_USERNAME"
        password_key = "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_PASSWORD"
        skip_ssl_validation_key = "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_SKIP_SSL_VALIDATION"

        # Besides the required props,we will put these in the scdf_server manifest
        deployer_props = {}
        for (key, value) in os.environ.items():
            if key.startswith("SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY") and key not in \
                    [url_key, org_key, space_key, domain_key, username_key, password_key, skip_ssl_validation_key]:
                deployer_props[key] = value

        return CloudFoundryDeployerConfig(api_endpoint=os.getenv(url_key),
                                          org=os.getenv(org_key),
                                          space=os.getenv(space_key),
                                          app_domain=os.getenv(domain_key),
                                          username=os.getenv(username_key),
                                          password=os.getenv(password_key),
                                          skipSslValidation=os.getenv(skip_ssl_validation_key),
                                          props=deployer_props)

    def __init__(self, api_endpoint, org, space, app_domain, username, password,
                 skipSslValidation=True, props={}):
        self.api_endpoint = api_endpoint
        self.org = org
        self.space = space
        self.skip_ssl_validation = skipSslValidation
        self.app_domain = app_domain
        self.username = username
        self.password = password
        self.props = props
        # Task services are optional if using an external DB.
        task_services_key = "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_TASK_SERVICES"
        self.task_services = props[task_services_key].split(",") if props.get(task_services_key) else []
        self.validate()

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

    def log_masked(self):
        logger.info("Using configuration:\n" + json.dumps(self, indent=4, sort_keys=True))

    def __json__(self):
        dict = self.__dict__
        dict['password'] = "*******" if dict['password'] else "null"
        return dict


class DatasourceConfig(json.JSONEncoder):
    @classmethod
    def from_spring_env_vars(cls):

        url_key = 'SPRING_DATASOURCE_URL'
        username_key = 'SPRING_DATASOURCE_USERNAME'
        password_key = 'SPRING_DATASOURCE_PASSWORD'
        driver_class_name_key = 'SPRING_DATASOURCE_DRIVER_CLASS_NAME'

        if not os.getenv(url_key):
            logger.warning(url_key + " is not set in the OS environment.")
            return None
        return DatasourceConfig(os.getenv(url_key),
                                os.getenv(username_key),
                                os.getenv(password_key),
                                os.getenv(driver_class_name_key))

    def __init__(self, url, username, password, driver_class_name):
        self.url = url
        self.username = username
        self.password = password
        self.driver_class_name = driver_class_name

    def as_env(self):
        return {DatasourceConfig.URL_KEY: self.url,
                DatasourceConfig.USERNAME_KEY: self.username,
                DatasourceConfig.PASSWORD_KEY: self.password,
                DatasourceConfig.DRIVER_CLASS_NAME_KEY: self.DRIVER_CLASS_NAME_KEY
                }

    def __json__(self):
        dict = self.__dict__
        dict['password'] = "*******" if dict['password'] else "null"
        return dict

    def validate(self):
        if not self.url:
            raise ValueError("'url' is required")
        if not self.username:
            raise ValueError("'username' is required")
        if not self.password:
            raise ValueError("'password' is required")
        if not self.driver_class_name:
            raise ValueError("'driver_class_name' is required")


class ServiceConfig(json.JSONEncoder):
    def __init__(self, name, service, plan, config=None):
        self.name = name
        self.service = service
        self.plan = plan
        self.config = config
        self.validate()

    def __json__(self):
        return self.__dict__

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

    def __json__(self):
        return self.__dict__


class DataflowConfig:
    TASK_SERVICES_KEY = 'TASK_SERVICES'
    APPLICATION_NAME_KEY = 'SPRING_APPLICATION_NAME'
    PROFILES_ACTIVE_KEY = 'SPRING_PROFILES_ACTIVE'
    SCHEDULER_URL_KEY = "scheduler-url"
    STREAMS_ENABLED_KEY = "SPRING_CLOUD_DATAFLOW_FEATURES_STREAMS_ENABLED"

    def __init__(self, task_services=None, application_name="dataflow_server", profiles_active="cloud",
                 scheduler_url=None,
                 streams_enabled=True, schedules_enabled=False, spring_application_json=None):
        self.task_services = task_services
        self.application_name = application_name
        self.profiles_active = profiles_active
        self.scheduler_url = scheduler_url
        self.streams_enabled = streams_enabled
        self.schedules_enabled = schedules_enabled
        self.spring_application_json = spring_application_json


class SkipperConfig(CloudFoundryDeployerConfig):
    STREAM_SERVICES_KEY = 'STREAM_SERVICES'
    PROFILES_ACTIVE_KEY = 'SPRING_PROFILES_ACTIVE'


class CloudFoundryConfig(json.JSONEncoder):
    def __init__(self, deployer_config, db_config=None, dataflow_config=None, skipper_config=None,
                 services_config=[ServiceConfig.rabbit_default()], deploy_wait_sec=10, max_retries=150):
        self.deployer_config = deployer_config
        self.db_config = db_config
        self.dataflow_config = dataflow_config
        self.skipper_config = skipper_config
        self.services_config = services_config
        self.deploy_wait_sec = deploy_wait_sec
        self.max_retries = max_retries
        self.validate()
        if self.dataflow_config and self.dataflow_config.schedules_enabled and self.services_config:
            if not [service for service in self.services_config if service.plan == "scheduler-for-pcf"]:
                scheduler_service = ServiceConfig.scheduler_default()
                logger.info("Adding default scheduler service:" + json.dumps(scheduler_service))
                self.services_config = services_config.append(scheduler_service)
        if not len(self.deployer_config.task_services) and not self.db_config:
            logger.error("We have a problem:Neither task Services nor an external DB are configured.")

    def __json__(self):
        return self.__dict__

    def validate(self):
        if not self.deployer_config:
            raise ValueError("'deployer_config' is required")
        if not self.db_config and not len(self.services_config):
            logger.error("Either external database or CF service must be configured")
        if not self.dataflow_config:
            logger.error("Really? No Dataflow config properties? What's the point")
        if not self.skipper_config and self.dataflow_config and not self.dataflow_config.streams_enabled:
            logger.error("Skipper config is required if streams are enabled")
