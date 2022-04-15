import sys, os, logging

sys.path.append(os.path.join(sys.path[0], "src"))
from cloudfoundry.cli import CloudFoundry
from cloudfoundry.config import CloudFoundryConfig
from shell.core import Shell, Utils
from optparse import OptionParser

CF_INITIALIZED = False
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(asctime)s - %(levelname)s:  %(message)s')
logger = logging.getLogger(__name__)


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

    parser.add_option('-p', '--platform',
                      help='the platform type (cloudfoundry, tile)',
                      dest='platform', default='cloudfoundry')
    parser.add_option('--serverCleanup',
                      help='run the cleanup for only SCDF and Skipper, along with the applications deployed but excluding the DB, message broker',
                      dest='serverCleanup', action='store_true')
    try:
        options, arguments = parser.parse_args(args)
        print(options)
        print(arguments)
        cf = CloudFoundry.connect(cf_config())
        print("cleaning up apps...")
        if not options.serverCleanup:
            print("cleaning services ...")


    except SystemExit:
        parser.print_help()
        sys.exit(1)


def cf_config():
    config = CloudFoundryConfig(api_endpoint=os.getenv("SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_URL"),
                                org=os.getenv("SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_ORG"),
                                space=os.getenv("SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_SPACE"),
                                app_domain=os.getenv("SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_DOMAIN"),
                                username=os.getenv("SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_USERNAME"),
                                password=os.getenv("SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_PASSWORD"),
                                skipSslValidation=os.getenv(
                                    "SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_SKIP_SSL_VALIDATION"))
    return config


def setup(args):
    parser = OptionParser()
    parser.usage = "%prog setup options"

    parser.add_option('-p', '--platform',
                      help='the platform type (cloudfoundry, tile)',
                      dest='platform', default='cloudfoundry')

    parser.add_option('-b', '--binder',
                      help='the broker type for stream apps(rabbit, kafka)',
                      dest='binder', default='rabbit')

    parser.add_option('--se', '--schedulesEnabled',
                      help='cleans the scheduling infrastructure',
                      dest='schedulesEnabled', action='store_true')

    parser.add_option('-d', '--doNotDownload',
                      help='skip the downloading of the SCDF/Skipper servers',
                      dest='doNotDownload', action='store_true')

    try:
        options, arguments = parser.parse_args(args)
        logger.info("setting up the CF environment for platform %s and binder %a" % (options.platform, options.binder))
        cf = CloudFoundry.connect(cf_config())
        cf.config.log_masked()
        cf.services()

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
        print("Invalid task specified:" + run_task)
        exit(1);
