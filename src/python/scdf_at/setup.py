import logging
import sys

from cloudfoundry.cli import CloudFoundry
from cloudfoundry.config import CloudFoundryDeployerConfig, CloudFoundryConfig, DataflowConfig, DatasourceConfig, \
    DBConfig
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
                      dest='debug', default=False, action='store_true')
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
                      dest='cloud_config', default=True, action='store_false')
    parser.add_option('--ts', '--taskServices',
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

        cloudfoundry_config = CloudFoundryConfig.from_env_vars()
        cf = CloudFoundry.connect(cloudfoundry_config.deployer_config)
        cloudfoundry.environment.setup(cf, cloudfoundry_config, options)

    except SystemExit:
        parser.print_help()
        exit(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    setup(sys.argv)
