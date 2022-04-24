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
import os

import cloudfoundry.platform.manifest.skipper as skipper_manifest
import cloudfoundry.platform.manifest.dataflow as dataflow_manifest

from scdf_at.shell import Shell
from scdf_at.util import Poller, wait_for_200
from cloudfoundry.platform.registration import register_apps

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

    skipper_uri = None
    if config.dataflow_config.streams_enabled:
        logger.debug("deploying skipper server")
        deploy(cf=cf, manifest_path='skipper_manifest.yml',
               create_manifest=skipper_manifest.create_manifest, application_name='skipper-server',
               cf_config=config, params={})
        skipper_app = cf.app('skipper-server')
        # TODO: Try https
        skipper_uri = 'http://%s/api' % skipper_app.route
        logger.debug("waiting for skipper api %s to be live" % skipper_uri)
        if not wait_for_200(poller, skipper_uri):
            raise RuntimeError("skipper server deployment failed")

    logger.debug("getting dataflow server url")
    logger.debug("waiting for dataflow server to start")
    deploy(cf=cf, manifest_path='dataflow_manifest.yml', application_name='dataflow-server',
           create_manifest=dataflow_manifest.create_manifest, cf_config=config,
           params={'skipper_uri': skipper_uri})

    dataflow_app = cf.app('dataflow-server')
    dataflow_uri = "https://" + dataflow_app.route
    if not wait_for_200(poller, dataflow_uri):
        raise RuntimeError("dataflow server deployment failed")

    register_apps(cf, config, dataflow_uri)
    return dataflow_uri


def clean(cf, config, apps_only):
    if config.services_config and not apps_only:
        logger.info("deleting current services...")
        services = cf.services()
        for service in services:
            cf.delete_service(service.name)
    else:
        logger.info("'apps-only' option is set, keeping existing current services")
    logger.info("cleaning apps")
    cf.delete_apps()


def deploy(cf, application_name, manifest_path, create_manifest, cf_config, params={}):
    manifest = open(manifest_path, 'w')
    try:
        mf = create_manifest(cf_config, application_name=application_name, params=params)
        manifest.write(mf)
        manifest.close()
        cf.push('-f ' + manifest_path)
    finally:
        manifest.close()


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

    cmd = 'wget %s -q -O %s' % (url, destination)
    try:
        proc = shell.exec(cmd, capture_output=False)
        if proc.returncode:
            raise RuntimeError('FATAL: Unable to download maven artifact %s to %s' % (url, destination))
    except BaseException as e:
        logger.error(e)
        raise e
