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
from cloudfoundry.platform.config.environment import EnvironmentAware
from cloudfoundry.domain import JSonEnabled

logger = logging.getLogger(__name__)


class DBConfig(EnvironmentAware):
    prefix = "SQL_"
    provider_key = prefix + 'PROVIDER'
    host_key = prefix + 'HOST'
    port_key = prefix + 'PORT'
    username_key = prefix + 'USERNAME'
    password_key = prefix + 'PASSWORD'
    index_key = prefix + 'INDEX'

    @classmethod
    def assert_required_keys(cls, env):
        EnvironmentAware.assert_required_keys( env,
                                              [cls.provider_key,
                                               cls.host_key,
                                               cls.port_key,
                                               cls.username_key,
                                               cls.password_key,
                                               cls.index_key])

    @classmethod
    def from_env_vars(cls, env=os.environ):
        env = cls.env_vars(env, cls.prefix)
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

    def __init__(self, name, url, username, password, driver_class_name):
        self.name = name
        self.url = url
        self.username = username
        self.password = password
        self.driver_class_name = driver_class_name
        self.validate()

    def validate(self):
        if not self.name:
            raise ValueError("'name' is required")
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
