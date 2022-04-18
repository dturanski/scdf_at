import unittest, optparse, logging, json
from cloudfoundry.manifest import create_for_scdf, spring_application_json
from cloudfoundry.config import CloudFoundryDeployerConfig, CloudFoundryConfig, DataflowConfig

logger = logging.getLogger(__name__)


class TestConfig(unittest.TestCase):

    def test_spring_application_json(self):
        saj = spring_application_json(self.config(), self.options(['--taskServices', 'mysql']))
        logger.info(json.dumps(saj, indent=4))
        self.assertEqual({"remoteRepositories": {"repo0": {"url": "https://repo.spring.io/libs-snapshot"}}},
                         saj['maven'])
        self.assertEqual({'url': 'https://api.mycf.org', 'org': 'org', 'space': 'space',
                                      'domain': 'apps.mycf.org', 'username': 'user', 'password': 'password'},
                         saj['spring.cloud.dataflow.task.platform.cloudfoundry.accounts']['default']['connection'])

    def test_basic_dataflow_manifest(self):
        create_for_scdf("./scdf_manifest.yml", self.config(),
                        self.options())

    def config(self):
        deployer_config = CloudFoundryDeployerConfig(api_endpoint="https://api.mycf.org",
                                                     org="org",
                                                     space="space",
                                                     app_domain="apps.mycf.org",
                                                     username="user",
                                                     password="password")
        dataflow_config = DataflowConfig()
        return CloudFoundryConfig(deployer_config=deployer_config, dataflow_config=dataflow_config)

    def options(self, opts=[]):
        parser = optparse.OptionParser()

        parser.add_option('--ts', '--taskServices',
                          help='services to bind to tasks',
                          dest='task_services', default=None)

        parser.add_option('--scdfServices',
                          help='services to bind to the dataflow app',
                          dest='scdf_services')

        parser.add_option('--se', '--schedulesEnabled',
                          help='cleans the scheduling infrastructure',
                          dest='schedules_enabled', action='store_true')

        options, arguments = parser.parse_args(opts)
        return options
