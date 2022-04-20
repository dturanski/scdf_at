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
    JBP_JRE_VERSION: $jbp_jre_version   
    SPRING_APPLICATION_NAME: $application_name
    SPRING_CLOUD_SKIPPER_CLIENT_SERVER_URI: $skipper_uri
    $datasource_config_as_env
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
    JBP_JRE_VERSION: $jbp_jre_version
    $datasource_config_as_env
    $spring_application_json
  $services
'''


def generate_manifest(cf_config, manifest_template, application_name, datasource_config, jar_path, server_services=[],
                      app_services=[]):
    logger.info('creating manifest for application %s using jar path %s' % (application_name, jar_path))
    if datasource_config:
        logger.debug("generating datasource config")
    else:
        logger.debug("No datasource is configured will require a SQL resource")
        "get services for dataflow"

    saj = format_saj(spring_application_json(cf_config, app_services))
    template = Template(manifest_template)
    return template.substitute({
        'application_name': application_name,
        'host_name': "%s_%d" % (application_name, random.randint(0, 1000)),
        'buildpack': cf_config.test_config.buildpack,
        'path': jar_path,
        'skipper_uri': cf_config.skipper_config.url + '/api' if cf_config.skipper_config else "''",
        'jbp_jre_version': cf_config.test_config.jbp_jre_version,
        'datasource_config_as_env': format_env(datasource_config.as_env(), delim=': ', indent=8),
        'spring_application_json': saj,
        'services': "services:\n" + format_yaml_list(server_services) if server_services else ''

    })


def format_saj(spring_application_json):
    saj = ''
    for k, v in spring_application_json.items():
        for line in json.dumps({k: v}, indent=1).split('\n'):
            match = re.match('^(\s*)(.*)', line)
            if match.group(1):
                indent = ' ' * (4 * (len(match.group(1)) + 2))
                #1 leading space must be top level element.
                if line == ' }':
                    line = line + ' ,'
                saj = saj + indent + line + '\n'
    indent = ' ' * 8
    #Remove trailing comma
    if saj.endswith(',\n'):
        saj = saj[0:-2]
    return "SPRING_APPLICATION_JSON: |-\n%s{\n%s%s}" % (indent, saj, indent)


def spring_application_json(cf_config, services):
    logger.debug("adding %s" % services)
    saj = {'maven': {
        "remoteRepositories": {key: {'url': val} for (key, val) in cf_config.test_config.maven_repos.items()}
    }, 'spring.cloud.dataflow.task.platform.cloudfoundry.accounts': {
        "default": {'connection': cf_config.deployer_config.connection(), 'deployment': {'services': services}}}}
    return saj


def format_yaml_list(items, indent=4):
    s = ""
    i = len(items)
    for item in items:
        i = i - 1
        s = s + "%s- %s" % (' '*indent, item)
        if i > 0:
            s = s + '\n'
    return s


def format_env(env, delim='=', indent=4):
    s = ""
    i = 0
    for k, v in env.items():
        spaces_not_tabs = ' ' * 4 if i > 0 else ''
        format_str = "%s%s%s%s" if i == len(env) - 1 else "%s%s%s%s\n"
        s = s + format_str % (spaces_not_tabs, k, delim, v)
        i = i + 1
    return s


def create_for_scdf(cf_config, options, application_name='dataflow-server'):
    dataflow_config = cf_config.dataflow_config
    schedules_enabled = options.schedules_enabled
    datasource_config = cf_config.datasource_configs['dataflow']
    test_config = cf_config.test_config
    jar_path = test_config.dataflow_jar_path
    return generate_manifest(cf_config=cf_config,
                             options=options,
                             manifest_template=dataflow_manifest_template,
                             application_name=application_name,
                             datasource_config=datasource_config, jar_path=jar_path,
                             app_services=options.task_services.split(',') if options.task_services else [],
                             server_services=options.scdf_services.split(',') if options.scdf_services else [])


def create_for_skipper(cf_config, options, application_name='skipper-server'):
    datasource_config = cf_config.datasource_configs['skipper']
    test_config = cf_config.test_config
    return generate_manifest(cf_config=cf_config,
                             manifest_template=skipper_manifest_template,
                             application_name=application_name,
                             datasource_config=datasource_config, jar_path=test_config.skipper_jar_path,
                             app_services=options.stream_services.split(',') if options.stream_services else [],
                             server_services=options.skipper_services.split(',') if options.skipper_services else [])
