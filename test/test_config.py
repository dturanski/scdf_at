import unittest
from cloudfoundry.config import CloudFoundryDeployerConfig, ServiceConfig, CloudFoundryConfig, DataflowConfig, \
    DatasourceConfig, SkipperConfig
import json_fix
json_fix.patch()

class TestConfig(unittest.TestCase):
    def test_dataflow_config(self):
        pass
