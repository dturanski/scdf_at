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

from cloudfoundry.cli import CloudFoundry
from cloudfoundry.config import CloudFoundryATConfig
from optparse import OptionParser
import cloudfoundry.environment
from scdf_at import enable_debug_logging

logger = logging.getLogger(__name__)


def setup(args):
    parser = OptionParser()
    parser.usage = "%prog setup options"

    parser.add_option('-p', '--platform',
                      help='the platform type (cloudfoundry, tile)',
                      dest='platform', default='cloudfoundry')
    parser.add_option('-v', '--debug',
                      help='debug level logging',
                      dest='debug', action='store_true')
    parser.add_option('-b', '--binder',
                      help='the broker type for stream apps(rabbit, kafka)',
                      dest='binder', default='rabbit')
    parser.add_option('--se', '--schedulesEnabled',
                      help='cleans the scheduling infrastructure',
                      dest='schedules_enabled', action='store_true')
    parser.add_option('-d', '--doNotDownload',
                      help='skip the downloading of the SCDF/Skipper servers',
                      dest='do_not_download', action='store_true')
    # TODO: This needs work, but here for legacy reasons
    parser.add_option('--cc', '--skipCloudConfig',
                      help='skip configuration of Cloud Config server',
                      dest='skip_cloud_config', default=True, action='store_false')
    parser.add_option('--taskServices',
                      help='services to bind to tasks',
                      dest='task_services')
    parser.add_option('--ss', '--streamServices',
                      help='services to bind to streams',
                      dest='stream_services')
    parser.add_option('--scdfServices',
                      help='services to bind to the dataflow app',
                      dest='scdf_services')
    parser.add_option('--skipperServices',
                      help='services to bind to the skipper app',
                      dest='skipper_services')

    try:
        options, arguments = parser.parse_args(args)
        if options.debug:
            enable_debug_logging()

        cloudfoundry_config = CloudFoundryATConfig.from_env_vars()
        if not cloudfoundry_config.kafka_config and options.binder == 'kafka':
            raise ValueError("Kafka environment is not configured for kafka binder")
        cf = CloudFoundry.connect(deployer_config=cloudfoundry_config.deployer_config,
                                  test_config=cloudfoundry_config.test_config)
        cloudfoundry.environment.setup(cf, cloudfoundry_config, options)

    except SystemExit:
        parser.print_help()
        exit(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print(sys.argv)
    # exit(1)
    setup(sys.argv)
