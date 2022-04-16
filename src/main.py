import sys, os, logging

sys.path.append(os.path.join(sys.path[0], ""))
from cloudfoundry.cli import CloudFoundry
from cloudfoundry.config import CloudFoundryDeployerConfig, CloudFoundryConfig, DataflowConfig, SkipperConfig, \
    DatasourceConfig
from optparse import OptionParser
from cloudfoundry import cf_setup
import json_fix

json_fix.patch()
logging.basicConfig(level=logging.INFO, format='%(name)s - %(asctime)s - %(levelname)s:  %(message)s')

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
        print("usage: %s [clean,setup,..] --task options" % arguments[0])
    else:
        run_task = arguments[1];
    return run_task;


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
        print(options)
        print(arguments)
        cf = CloudFoundry.connect(cf_config_from_env().deployer_config)
        print("cleaning up apps...")
        if not options.serverCleanup:
            print("cleaning services ...")

    except SystemExit:
        parser.print_help()
        sys.exit(1)


def cf_config_from_env():

    deployer_config = CloudFoundryDeployerConfig.from_spring_env_vars()
    db_config = DatasourceConfig.from_spring_env_vars()

    return CloudFoundryConfig(deployer_config=deployer_config, db_config=db_config,
                              dataflow_config=DataflowConfig())


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
                      dest='schedulesEnabled', action='store_true')
    parser.add_option('-d', '--doNotDownload',
                      help='skip the downloading of the SCDF/Skipper servers',
                      dest='doNotDownload', action='store_true')
    # TODO: This needs work, but here for legacy reasons
    parser.add_option('--cc', '--skipCloudConfig',
                      help='skip configuration of Cloud Config server',
                      dest='cloudConfig', default=True, action='store_false')
    try:
        options, arguments = parser.parse_args(args)
        if options.debug:
            enable_debug_logging()
        cf = CloudFoundry.connect(cf_config_from_env().deployer_config)
        cf_setup.setup(cf, cf_config_from_env(), options)

    except SystemExit:
        parser.print_help()
        sys.exit(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    run_task = parse_run_task(sys.argv)

    if run_task == 'clean':
        clean(sys.argv)
    elif run_task == 'setup':
        setup(sys.argv)
    else:
        print("Invalid task specified:" + str(run_task))
        exit(1);
