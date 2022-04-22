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
import random
import re
# Runs package initialization
import scdf_at

from string import Template

logger = logging.getLogger(__name__)

dataflow_manifest_template = '''
---
applications:
- name: $application_name
  host: $host_name
  memory: 2G
  disk_quota: 2G
  instances: 1
  buildpack: $buildpack
  path: $path

  env:
    SPRING_PROFILES_ACTIVE: cloud
    JBP_CONFIG_SPRING_AUTO_RECONFIGURATION: '{enabled: false}'
    JBP_JRE_VERSION: '$jbp_jre_version'   
    SPRING_APPLICATION_NAME: $application_name
    SPRING_CLOUD_SKIPPER_CLIENT_SERVER_URI: '$skipper_uri'
    $app_config
    $datasource_config_as_env
    $kafka_config
    $spring_application_json
  $services
'''

skipper_manifest_template = '''
---
applications:
- name: $application_name
  host: $host_name
  memory: 2G
  disk_quota: 2G
  instances: 1
  buildpack: $buildpack
  path: $path

  env:
    SPRING_PROFILES_ACTIVE: cloud
    JBP_CONFIG_SPRING_AUTO_RECONFIGURATION: '{enabled: false}'    
    SPRING_APPLICATION_NAME: $application_name
    JBP_JRE_VERSION: '$jbp_jre_version'
    $app_config
    $datasource_config_as_env
    $kafka_config
    $spring_application_json
  $services
'''


def generate_manifest(cf_at_config, manifest_template, platform_accounts_key, application_name, datasource_config,
                      jar_path, server_services=[], app_deployment={}, app_config={}, params = {}):
    logger.info('creating manifest for application %s using jar path %s' % (application_name, jar_path))
    logger.debug('app_config:' + str(app_config))
    saj = format_saj(spring_application_json(cf_at_config, app_deployment, platform_accounts_key))
    kafka_config = cf_at_config.kafka_config
    template = Template(manifest_template)
    format_yaml_list(server_services)
    return template.substitute({
        'application_name': application_name,
        'host_name': "%s-%d" % (application_name, random.randint(0, 1000)),
        'buildpack': cf_at_config.test_config.buildpack,
        'path': jar_path,
        'app_config' : format_env(app_config),
        'skipper_uri': params.get('skipper_uri'),
        'kafka_config': format_env(kafka_config.as_env()) if kafka_config else '',
        'jbp_jre_version': cf_at_config.test_config.jbp_jre_version,
        'datasource_config_as_env': format_env(datasource_config.as_env()),
        'spring_application_json': saj,
        'services': "services:\n" + format_yaml_list(server_services) if server_services else ''})


def create_for_scdf(cf_at_config, application_name='dataflow-server', params={}):
    dataflow_config = cf_at_config.dataflow_config
    datasource_config = cf_at_config.datasources_config['dataflow']
    test_config = cf_at_config.test_config
    jar_path = test_config.dataflow_jar_path
    deployer_config = cf_at_config.deployer_config
    app_deployment = {'services': test_config.task_services}
    if test_config.scheduler_enabled:
        app_deployment['scheduler-url'] = deployer_config.scheduler_url

    return generate_manifest(cf_at_config=cf_at_config,
                             manifest_template=dataflow_manifest_template,
                             platform_accounts_key='spring.cloud.dataflow.task.platform.cloudfoundry.accounts',
                             application_name=application_name,
                             app_deployment=app_deployment,
                             server_services=[cf_at_config.services_config.get('sql').name],
                             datasource_config=datasource_config, jar_path=jar_path,
                             app_config=dataflow_config.as_env(),
                             params=params
                             )


def create_for_skipper(cf_at_config, application_name='skipper-server', params={}):
    datasource_config = cf_at_config.datasources_config['skipper']
    test_config = cf_at_config.test_config
    deployer_config = cf_at_config.deployer_config
    app_deployment = {'services': test_config.stream_services,
                      'deleteRoutes': False,
                      'enableRandomAppNamePrefix': False,
                      'memory': 2048
                      }

    return generate_manifest(cf_at_config=cf_at_config,
                             platform_accounts_key='spring.cloud.skipper.server.platform.cloudfoundry.accounts',
                             manifest_template=skipper_manifest_template,
                             application_name=application_name,
                             datasource_config=datasource_config,
                             jar_path=test_config.skipper_jar_path,
                             app_deployment=app_deployment,
                             app_config=cf_at_config.skipper_config.as_env(),
                             server_services=[cf_at_config.services_config.get('sql').name],
                             params=params
                             )


def spring_application_json(cf_config, app_deployment, platform_accounts_key):
    logger.debug("generating spring_application_json for platform_accounts_key %s" % platform_accounts_key)
    logger.debug("deployment config %s" % str(app_deployment))
    saj = {'maven': {
        "remoteRepositories": {key: {'url': val} for (key, val) in cf_config.test_config.maven_repos.items()}
    }, platform_accounts_key: {
        "default": {'connection': cf_config.deployer_config.connection(), 'deployment': app_deployment}}}
    return saj


def format_saj(spring_application_json):
    saj = ''
    for k, v in spring_application_json.items():
        for line in json.dumps({k: v}, indent=1).split('\n'):
            match = re.match('^(\s*)(.*)', line)
            if match.group(1):
                indent = ' ' * (4 * (len(match.group(1)) + 2))
                # 1 leading space must be top level element.
                if line == ' }':
                    line = line + ' ,'
                saj = saj + indent + line + '\n'
    # Remove trailing comma
    if saj.endswith(',\n'):
        saj = saj[0:-2]
    return "SPRING_APPLICATION_JSON: |-\n%s{\n%s}" % (indent, saj)


def format_yaml_list(items, indent=4):
    s = ""
    i = len(items)
    for item in items:
        i = i - 1
        s = s + "%s- %s" % (' ' * indent, item)
        if i > 0:
            s = s + '\n'
    return s


def format_env(env, delim=': '):
    s = ""
    i = 0
    for k, v in env.items():
        spaces_not_tabs = ' ' * 4 if i > 0 else ''
        format_str = "%s%s%s%s" if i == len(env) - 1 else "%s%s%s%s\n"
        s = s + format_str % (spaces_not_tabs, k, delim, v)
        i = i + 1
    return s
