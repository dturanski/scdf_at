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
import sys
import json

from cloudfoundry.cli import CloudFoundry
from optparse import OptionParser
from cloudfoundry.platform import standalone, tile
from cloudfoundry.platform.config.at import CloudFoundryATConfig
from cloudfoundry.platform.config.service import ServiceConfig
from scdf_at import enable_debug_logging
from scdf_at.db import init_db

logger = logging.getLogger(__name__)


def add_options_for_platform(parser, platform):
    # No domain related options here, use environment variables for everything.
    parser.add_option('-v', '--debug',
                      help='debug level logging',
                      dest='debug', action='store_true')
    if platform == 'cloudfoundry':
        parser.add_option('-d', '--doNotDownload',
                          help='skip the downloading of the SCDF/Skipper servers',
                          dest='do_not_download', action='store_true')


def setup(args):
    parser = OptionParser()
    parser.usage = "%prog setup options"

    try:
        config = CloudFoundryATConfig.from_env_vars()
        logger.debug("Setup using config:\n" + json.dumps(config, indent=4))
        add_options_for_platform(parser, config.test_config.platform)
        options, arguments = parser.parse_args(args)
        if options.debug:
            enable_debug_logging()

        cf = CloudFoundry.connect(deployer_config=config.deployer_config,
                                  test_config=config.test_config)
        if config.db_config:
            config.datasources_config = init_db(config)

        ensure_required_services(cf, config)
        if config.test_config.platform == "tile":
            return tile.setup(cf, config)
        elif config.test_config.platform == "cloudfoundry":
            return standalone.setup(cf, config, options.do_not_download)
        else:
            logger.error("invalid platform type %s should be in [cloudfoundry,tile]" % config.test_config.platform)


    except SystemExit:
        parser.print_help()
        exit(1)


def ensure_required_services(cf, cf_at_config):
    logger.info("verifying availability of required services:" + str([str(s) for s in cf_at_config.services_config]))

    services = cf.services()
    required_services = {'create': [], 'wait': [], 'failed': [], 'deleting': [], 'unknown': []}

    for required_service in cf_at_config.services_config.values():
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


if __name__ == '__main__':
    dataflow_server_uri = setup(sys.argv)
    #TODO not sure a better way to make this available to calling shell script
    with open('cf_at.properties', 'w') as output:
        output.write('SERVER_URI=%s\n' %dataflow_server_uri)
    output.close()


