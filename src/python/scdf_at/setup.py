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
from cloudfoundry.platform import standalone, tile
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

    elif platform == 'tile':
        pass


def setup(args):
    parser = OptionParser()
    parser.usage = "%prog setup options"

    try:
        config = CloudFoundryATConfig.from_env_vars()
        add_options_for_platform(parser, config.test_config.platform)
        options, arguments = parser.parse_args(args)
        if options.debug:
            enable_debug_logging()

        cf = CloudFoundry.connect(deployer_config=config.deployer_config,
                                  test_config=config.test_config)
        if config.db_config:
            init_db(config)

        if config.test_config.platform == "tile":
            return tile.setup(cf, config)
        elif config.test_config.platform == "cloudfoundry":
            return standalone.setup(cf, options.do_not_download)
        else:
            logger.error("invalid platform type %s should be in [cloudfoundry,tile]" % config.test_config.platform)

    except SystemExit:
        parser.print_help()
        exit(1)


if __name__ == '__main__':
    setup(sys.argv)
