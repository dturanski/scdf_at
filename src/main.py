import logging
import os
import sys
sys.path.append(os.path.join(sys.path[0], ""))

from cloudfoundry.cli import CloudFoundry
from cloudfoundry.config import CloudFoundryDeployerConfig, CloudFoundryConfig, DataflowConfig, DatasourceConfig
from optparse import OptionParser
import cloudfoundry.environment
import json_fix

json_fix.patch()

logging.basicConfig(level=logging.INFO, format='%(name)s - %(asctime)s - %(levelname)s:  %(message)s')

logger = logging.getLogger(__name__)


def enable_debug_logging():
    level = logging.DEBUG
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
    logger.debug("DEBUG logging enabled")


def parse_run_task(args):
    arguments = []
    run_task = None
    for arg in args:
        if not arg.startswith('-'):
            arguments.append(arg)
    if len(arguments) != 2:
        logger.info("usage: %s [clean,setup,..] --task options" % arguments[0])
    else:
        run_task = arguments[1];
    return run_task;


def cf_config_from_env():
    deployer_config = CloudFoundryDeployerConfig.from_spring_env_vars()
    db_config = DatasourceConfig.from_spring_env_vars()
    dataflow_config = DataflowConfig.from_spring_env_vars()

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
        cf = CloudFoundry.connect(cf_config_from_env().deployer_config)
        logger.info("cleaning up apps...")
        if not options.serverCleanup:
            logger.info("cleaning services ...")

        cloudfoundry.environment.clean(cf, cf_config_from_env(), options)

    except SystemExit:
        parser.print_help()
        exit(1)


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
        cf = CloudFoundry.connect(cf_config_from_env().deployer_config)
        cloudfoundry.environment.setup(cf, cf_config_from_env(), options)

    except SystemExit:
        parser.print_help()
        exit(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    run_task = parse_run_task(sys.argv)

    if run_task == 'clean':
        clean(sys.argv)
    elif run_task == 'setup':
        setup(sys.argv)
    else:
        logger.info("Invalid task specified:" + str(run_task))
        exit(1)
