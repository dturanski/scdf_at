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
import shutil
from scdf_at.util import masked
from os.path import exists

from scdf_at.shell import Shell

logger = logging.getLogger(__name__)


def client_credentials_from_service_key(cf, service_name, key_name):
    service_key = cf.create_service_key(service_name, key_name)
    cf.delete_service_key(service_name, key_name)
    return {
        'SPRING_CLOUD_DATAFLOW_CLIENT_AUTHENTICATION_TOKEN_URI': service_key['access-token-url'],
        'SPRING_CLOUD_DATAFLOW_CLIENT_AUTHENTICATION_CLIENT_ID': service_key['client-id'],
        'SPRING_CLOUD_DATAFLOW_CLIENT_AUTHENTICATION_CLIENT_SECRET': service_key['client-secret'],
        'SPRING_CLOUD_DATAFLOW_CLIENT_SERVER_URI': service_key['dataflow-url'],
        'SERVER_URI': service_key['dataflow-url']
    }


def setup(cf, config):
    setup_certs(config.test_config.cert_host)
    service_name = config.services_config['dataflow'].name
    key_name = config.test_config.service_key_name
    return client_credentials_from_service_key(cf, service_name, key_name)


def configure_dataflow_service(config):
    logger.info("configuring dataflow tile")
    dataflow_tile_configuration = {'maven-cache': True}
    #
    # TODO: It does appear that you can pass any native properties this way, but this is undocumented AFAIK
    #
    dataflow_tile_configuration.update(config.dataflow_config.as_env())
    if config.dataflow_config.schedules_enabled:
        scheduler = config.services_config['scheduler']
        dataflow_tile_configuration.update({'scheduler': {'name': scheduler.name, 'plan': scheduler.plan}})
    if config.db_config:
        if config.dataflow_config.streams_enabled:
            print(config.datasources_config.get('skipper'))
            dataflow_tile_configuration['skipper-relational'] = user_provided(config.datasources_config.get('skipper'))
        if config.dataflow_config.tasks_enabled:
            dataflow_tile_configuration['relational-data-service'] = user_provided(config.datasources_config.get('dataflow'))
    logger.debug("dataflow_tile_configuration:\n%s" % masked(dataflow_tile_configuration))
    return dataflow_tile_configuration


def setup_certs(cert_host, shell=Shell()):
    logger.debug("importing the cert_host certificate for %s to a JDK trust-store" % cert_host)
    proc = shell.exec(
        'openssl s_client -connect %s:443 -showcerts > %s.cer < /dev/null' % (cert_host, cert_host))
    if proc.returncode > 0:
        logger.warning('openssl command returns a non zero status, but seems to work anyway')
    java_home = os.getenv('JAVA_HOME')
    if not java_home:
        raise ValueError('JAVA_HOME is not set')
    # The cacerts location is different for Java 8 and 11.
    # Java 1.8
    jre_cacerts = "%s/jre/lib/security/cacerts" % java_home
    if not exists(jre_cacerts):
        logger.info("%s does not exist" % jre_cacerts)
        # Java 11
        jre_cacerts = "%s/lib/security/cacerts" % java_home
        logger.info("trying %s" % jre_cacerts)
    if not exists(jre_cacerts):
        raise RuntimeError("%s does not exist" % jre_cacerts)
    shutil.copyfile(jre_cacerts, 'mycacerts')
    proc = shell.exec(
        '%s/bin/keytool -import -alias myNewCertificate -file %s.cer -noprompt -keystore mycacerts -storepass changeit'
        % (java_home, cert_host))
    if proc.returncode > 0:
        raise RuntimeError("Unable to create keystore ' %s" % shell.stdout_to_s(proc))


def user_provided(datasource_config):
    return {'user-provided':
                {'uri': datasource_config.url.replace('jdbc:', ''),
                 'jdbcUrl': datasource_config.url,
                 'username': datasource_config.username,
                 'password': datasource_config.password,
                 'dbname': datasource_config.name
                 }
            }


def clean(cf, config):
    pass
