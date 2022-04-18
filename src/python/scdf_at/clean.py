import logging
import sys

from cloudfoundry.cli import CloudFoundry
from cloudfoundry.config import CloudFoundryDeployerConfig, CloudFoundryConfig, DataflowConfig, DatasourceConfig
from optparse import OptionParser
import cloudfoundry.environment
from scdf_at import enable_debug_logging

logger = logging.getLogger(__name__)


def cf_config_from_env():
    deployer_config = CloudFoundryDeployerConfig.from_env_vars()
    db_config = DatasourceConfig.from_spring_env_vars()
    dataflow_config = DataflowConfig.from_env_vars()

    return CloudFoundryConfig(deployer_config=deployer_config, db_config=db_config,
                              dataflow_config=dataflow_config)


def clean(args):
    parser = OptionParser()
    parser.usage = "%prog clean options"

    parser.add_option('-v', '--debug',
                      help='debug level logging',
                      dest='debug', default=False, action='store_true')
    parser.add_option('-p', '--platform',
                      help='the platform type (cloudfoundry, tile)',
                      dest='platform', default='cloudfoundry')
    parser.add_option('--serverCleanup',
                      help='run the cleanup for the apps, but excluding services',
                      dest='serverCleanup', action='store_true')
    try:
        options, arguments = parser.parse_args(args)
        if options.debug:
            enable_debug_logging()
        cf = CloudFoundry.connect(cf_config_from_env().deployer_config)
        logger.info("cleaning up apps...")
        if not options.serverCleanup:
            logger.info("cleaning services ...")

        cloudfoundry.environment.clean(cf, cf_config_from_env(), options)

    except SystemExit:
        parser.print_help()
        exit(1)


if __name__ == '__main__':
    clean(sys.argv)
