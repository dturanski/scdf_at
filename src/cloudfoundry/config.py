import json
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


class CloudFoundryConfig:
    def __init__(self, api_endpoint, org, space, app_domain, username, password, skipSslValidation=True):
        self.api_endpoint = api_endpoint
        self.org = org
        self.space = space
        self.skip_ssl_validation = skipSslValidation
        self.app_domain = app_domain
        self.username = username
        self.password = password
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
        logger.info("Using configuration:\n" + json.dumps({'api_endpoint':self.api_endpoint,
                               'org':self.org,
                               'space':self.space,
                               'username':self.username,
                               'password':"*******",
                               'app_domain':self.app_domain,
                               'skipSslValidation':self.skip_ssl_validation}, indent=4, sort_keys=True))



class DatasourceConfig:
    URL_KEY = 'SPRING_DATASOURCE_URL'
    USERNAME_KEY = 'SPRING_DATASOURCE_USERNAME'
    PASSWORD_KEY = 'SPRING_DATASOURCE_PASSWORD'
    DRIVER_CLASS_NAME_KEY = 'SPRING_DATASOURCE_DRIVER_CLASS_NAME'


class DataflowConfig(CloudFoundryConfig):
    TASK_SERVICES_KEY = 'TASK_SERVICES'
    APPLICATION_NAME_KEY = 'SPRING_APPLICATION_NAME'
    PROFILES_ACTIVE_KEY = 'SPRING_PROFILES_ACTIVE'
    SCHEDULER_URL_KEY = "scheduler-url"


class SkipperConfig(CloudFoundryConfig):
    STREAM_SERVICES_KEY = 'STREAM_SERVICES'
    PROFILES_ACTIVE_KEY = 'SPRING_PROFILES_ACTIVE'
