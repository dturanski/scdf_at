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
import sys
import subprocess
import re
import os
import sys
import cloudfoundry.manifest

from cloudfoundry.config import ServiceConfig
from scdf_at.db import init_db, db_name
from scdf_at.shell import Shell

logger = logging.getLogger(__name__)


class Tile:
    @classmethod
    def credentials_from_service_key(cls):
        dataflow_service_instance = sys.argv[1]
        service_key = sys.argv[2]
        get_service_key = "cf service-key %s %s" % (dataflow_service_instance, service_key)
        out = subprocess.getoutput(get_service_key)
        if 'FAILED' in out:
            print(out)
            exit(1)

        creds = re.sub("Getting key.+\n", "", out)
        doc = json.loads(creds)
        print("export SPRING_CLOUD_DATAFLOW_CLIENT_AUTHENTICATION_TOKEN_URI=%s; " % doc['access-token-url'])
        print("export SPRING_CLOUD_DATAFLOW_CLIENT_AUTHENTICATION_CLIENT_ID=%s; " % doc['client-id'])
        print("export SPRING_CLOUD_DATAFLOW_CLIENT_AUTHENTICATION_CLIENT_SECRET=%s; " % doc['client-secret'])
        print("export SPRING_CLOUD_DATAFLOW_CLIENT_SERVER_URI=%s" % doc['dataflow-url'])

    @classmethod
    def setup(cls, cf, config, options):
        cf.deployer_config.log_masked()
        if config.service_configs:
            logger.info("Setting up services...")
            logger.debug("Getting current services...")
            services = cf.services()
            logger.debug("checking required services:" + json.dumps(config.service_configs))

    @classmethod
    def clean(cls, cf, config, options):
        cf.deployer_config.log_masked()
        if config.service_configs:
            logger.info("deleting current services...")
            services = cf.services()
        else:
            logger.info("using current services...")

    # def user_provided_postgresql(self,db, server):
    #     name = dbname(db, server)
    #     user_provided = {}
    #     port = int(db['port'])
    #     user_provided['uri'] = "postgresql://%s:%d/%s?user=%s&password=%s" % (
    #     db['host'], port, name, db['username'], db['password'])
    #     user_provided['jdbcUrl'] = "jdbc:%s" % user_provided['uri']
    #     user_provided['username'] = db['username']
    #     user_provided['password'] = db['password']
    #     user_provided['dbname'] = name
    #     user_provided['host'] = db['host']
    #     user_provided['port'] = port
    #     user_provided['tags'] = ['postgres']
    #     ups = {}
    #     ups['user-provided'] = user_provided
    #     return ups
    #
    # def user_provided_oracle(self, db, server):
    #     name = dbname(db, server)
    #     user_provided = {}
    #     port = int(db['port'])
    #     user_provided['uri'] = "oracle:thin://%s:%d/%s?user=%s&password=%s" % (
    #     db['host'], port, name, db['username'], db['password'])
    #     user_provided['jdbcUrl'] = "jdbc:%s" % user_provided['uri']
    #     user_provided['username'] = db['username']
    #     user_provided['password'] = db['password']
    #     user_provided['dbname'] = name
    #     user_provided['host'] = db['host']
    #     user_provided['port'] = port
    #     user_provided['tags'] = ['oracle']
    #     ups = {}
    #     ups['user-provided'] = user_provided
    #     return ups
    #
    # def user_provided(self, db, server):
    #     if db['provider'] == 'postgresql':
    #         return self.user_provided_postgresql(db, server)
    #     elif db['provider'] == 'oracle':
    #         return self.user_provided_oracle(db, server)
    #     else:
    #         raise Exception("Invalid db provider %s" % db['provider'])
    #
    # schedules_enabled = os.getenv(
    #     "SPRING_CLOUD_DATAFLOW_FEATURES_SCHEDULES_ENABLED", 'false')
    # dataflow_tile_configuration = os.getenv("DATAFLOW_TILE_CONFIGURATION")
    # if dataflow_tile_configuration:
    #     config = json.loads(dataflow_tile_configuration)
    #
    # if not config.get('relational-data-service') or not config.get('skipper-relational'):
    #     db
    #
    # if not config.get('skipper-relational'):
    #     config['skipper-relational'] = user_provided(db, 'skipper')
    #
    # if not config.get('relational-data-service'):
    #     config['relational-data-service'] = user_provided(db, 'dataflow')
    #
    # if not config.get('maven-cache'):
    #     config['maven-cache'] = True
    #
    # if schedules_enabled.lower() == 'true' and not 'scheduler' in config.keys():
    #     schedules_service_name = os.environ['SCHEDULES_SERVICE_NAME']
    #     schedules_plan_name = os.environ['SCHEDULES_PLAN_NAME']
    #     config['scheduler'] = {'name': schedules_service_name, 'plan': schedules_plan_name}
    # if config:
    #     print(json.dumps(config))


class Standalone:

    @classmethod
    def setup(cls, cf, config, options, shell=Shell()):
        '''
        :param cf:
        :param config:
        :param options:
        :return:
        '''
        if options.do_not_download:
            logger.info("skipping download server of jars")
        else:
            cls.download_server_jars(config.test_config, shell)

        logger.info("downloading jars")
        logger.info("Using config:\n" + json.dumps(config, indent=4))
        if config.service_configs:
            logger.info("Getting current services...")
            services = cf.services()
            logger.info("verifying required services:" + str([str(s) for s in config.service_configs]))
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
                        raise SystemExit("FATAL: %s " % cf.service(s.name))
                    required_services['create'].append(ServiceConfig.of_service(s))

                for s in required_services['wait']:
                    if not cf.wait_for(success_condition=lambda: cf.service(s.name).status == 'create succeeded',
                                       wait_message="waiting for %s status 'create succeeded'" % s.name):
                        raise SystemExit("FATAL: %s " % cf.service(s.name))

                for s in required_services['create']:
                    logger.info("creating service:" + str(s))
                    cf.create_service(s)

            logger.debug("deploying skipper server")
            cls.deploy(cf, 'skipper_manifest.yml', cloudfoundry.manifest.create_for_skipper, config, options)

            logger.debug("getting skipper server url")
            logger.debug("waiting for skipper server to start")
            cls.deploy(cf,'dataflow_manifest.yml', cloudfoundry.manifest.create_for_scdf, config, options)

    @classmethod
    def clean(cls, cf, config, options):
        if config.service_configs:
            logger.info("deleting current services...")
            services = cf.services()
            for service in services:
                cf.delete_service(service.name)
        else:
            logger.info("using current services")

    @classmethod
    def deploy(self, cf, manifest_path, create_manifest, cf_config, options):
        create_manifest(cf_config, options)
        manifest = open(manifest_path, 'w')
        manifest.write(create_manifest(cf_config, options))
        manifest.close()
        cf.push('-f ' + manifest_path)

    @classmethod
    def download_server_jars(cls, test_config, shell):
        skipper_url = 'https://repo.spring.io/libs-snapshot/org/springframework/cloud/spring-cloud-skipper-server/%s/spring-cloud-skipper-server-%s.jar' \
                      % (test_config.skipper_version, test_config.skipper_version)
        cls.download_maven_jar(skipper_url, test_config.skipper_jar_path, shell)

        dataflow_url = 'https://repo.spring.io/libs-snapshot/org/springframework/cloud/spring-cloud-dataflow-server/%s/spring-cloud-dataflow-server-%s.jar' \
                       % (test_config.dataflow_version, test_config.dataflow_version)
        cls.download_maven_jar(dataflow_url, test_config.dataflow_jar_path, shell)

    @classmethod
    def download_maven_jar(cls, url, destination, shell):
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
                raise RuntimeError('Unable to download maven artifact %s to %s' % (url, destination))
        except BaseException as e:
           logger.error(e)
           raise(e)


def setup(cf, config, options):
    config.dataflow_config.schedules_enabled = options.schedules_enabled
    if config.dataflow_config.schedules_enabled and config.service_configs:
        if not [service for service in config.service_configs if service.plan == "scheduler-for-pcf"]:
            scheduler_service = ServiceConfig.scheduler_default()
            logger.info("Adding default scheduler service: %s" % str(scheduler_service))
            config.service_configs.append(scheduler_service)

    init_db(config, options)

    if options.platform == "tile":
        return Tile.setup(cf, config, options)
    elif options.platform == "cloudfoundry":
        return Standalone.setup(cf, config, options)
    else:
        logger.error("invalid platform type %s should be in [cloudfoundry,tile]" % options.platform)


def clean(cf, config, options):
    if options.platform == "tile":
        return Tile.clean(cf, config, options)
    elif options.platform == "cloudfoundry":
        return Standalone.clean(cf, config, options)
    else:
        logger.error("invalid platform type %s should be in [cloudfoundry,tile]" % options.platform)
