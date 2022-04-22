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
import json
import os

import cloudfoundry.manifest

from cloudfoundry.config import ServiceConfig
from scdf_at.shell import Shell
from cloudfoundry.platform.util import Poller, wait_for_200

logger = logging.getLogger(__name__)


def setup(cf, config, do_not_download, shell=Shell()):
    """
    :param cf:
    :param config:
    :param do_not_download:
    :param shell:
    :return:
    """
    poller = Poller(config.test_config.deploy_wait_sec, config.test_config.max_retries)

    if do_not_download:
        logger.info("skipping download server of jars")
    else:
        logger.info("downloading jars")
        download_server_jars(config.test_config, shell)

    logger.debug("Setup using config:\n" + json.dumps(config, indent=4))
    if config.service_configs:
        logger.info("Getting current services...")
        services = cf.services()
        logger.info("verifying availability of required services:" + str([str(s) for s in config.service_configs]))
        required_services = {'create': [], 'wait': [], 'failed': [], 'deleting': [], 'unknown': []}

    for required_service in config.service_configs:
        if required_service not in [ServiceConfig.of_service(service) for service in services]:
            logger.debug("Adding %s to required services" % required_service)
            required_services['create'].append(required_service)
        else:
            logger.debug("Checking health of required service %s" % str(required_service))
            for service in services:
                if ServiceConfig.of_service(service) == required_service:
                    if service.status not in ['create succeeded', 'update succeeded']:
                        logger.warning(
                            "status of required service %s is %s" % (service.name, service.status))
                        if service.status == 'create in progress':
                            required_services['wait'].append(service)
                        elif service.status == 'delete in progress':
                            required_services['deleting'].append(service)
                        elif service.status == 'create failed':
                            required_services['failed'].append(service)
                        else:
                            required_services['unknown'].append(service)
                else:
                    logger.debug("required service is healthy %s" % str(required_service))

        for s in required_services['deleting']:
            logger.info("waiting for required service %s to be deleted" % str(s))
            if not cf.wait_for(success_condition=lambda: cf.service(s.name) is None,
                               wait_message="waiting for %s to be deleted" % s.name):
                raise RuntimeError("FATAL: %s " % cf.service(s.name))
            required_services['create'].append(ServiceConfig.of_service(s))

        for s in required_services['wait']:
            if not cf.wait_for(success_condition=lambda: cf.service(s.name).status == 'create succeeded',
                               wait_message="waiting for %s status 'create succeeded'" % s.name):
                raise RuntimeError("FATAL: %s " % cf.service(s.name))

        for s in required_services['create']:
            logger.info("creating service:" + str(s))
            cf.create_service(s)

    skipper_uri=None
    if config.dataflow_config.streams_enabled:
        logger.debug("deploying skipper server")
        deploy(cf, 'skipper_manifest.yml', cloudfoundry.manifest.create_for_skipper, config)
        skipper_app = cf.app('skipper-server')
        skipper_uri = 'https://%s/api' % skipper_app.route
        logger.debug("waiting for skipper api live")
        if not wait_for_200(skipper_uri):
            raise RuntimeError("skipper server deployment failed")

    logger.debug("getting dataflow server url")
    logger.debug("waiting for dataflow server to start")
    deploy(cf, 'dataflow_manifest.yml', cloudfoundry.manifest.create_for_scdf, config, {'skipper_uri': skipper_uri})
    dataflow_app = cf.app('dataflow_uri')
    dataflow_uri = dataflow_app.route
    if not wait_for_200(dataflow_uri):
        raise RuntimeError("dataflow server deployment failed")
    return dataflow_uri



def clean(cf, config, apps_only):
    if config.service_configs:
        logger.info("deleting current services...")
        services = cf.services()
        for service in services:
            cf.delete_service(service.name)
    else:
        logger.info("using current services")


def deploy(cf, manifest_path, create_manifest, cf_config, params={}):
    manifest = open(manifest_path, 'w')
    manifest.write(create_manifest(cf_config, params))
    manifest.close()
    cf.push('-f ' + manifest_path)


def download_server_jars(test_config, shell):
    skipper_url = 'https://repo.spring.io/libs-snapshot/org/springframework/cloud/spring-cloud-skipper-server/%s/spring-cloud-skipper-server-%s.jar' \
                  % (test_config.skipper_version, test_config.skipper_version)
    download_maven_jar(skipper_url, test_config.skipper_jar_path, shell)

    dataflow_url = 'https://repo.spring.io/libs-snapshot/org/springframework/cloud/spring-cloud-dataflow-server/%s/spring-cloud-dataflow-server-%s.jar' \
                   % (test_config.dataflow_version, test_config.dataflow_version)
    download_maven_jar(dataflow_url, test_config.dataflow_jar_path, shell)


def download_maven_jar(url, destination, shell):
    logger.info("downloading jar %s to %s" % (url, destination))
    from os.path import exists
    from pathlib import Path
    path = Path(destination)

    if not exists(path.parent):
        logger.info("creating directory %s" % path.parent)
        os.mkdir(path.parent)

    if exists(destination):
        logger.debug("deleting existing file %s" % destination)
        os.remove(destination)

    cmd = 'wget %s -v -o %s' % (url, destination)
    try:
        proc = shell.exec(cmd, capture_output=False)
        if proc.returncode:
            raise RuntimeError('FATAL: Unable to download maven artifact %s to %s' % (url, destination))
    except BaseException as e:
        logger.error(e)
        raise e
