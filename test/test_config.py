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

import unittest

from cloudfoundry.config import TestConfig


class TestConfigObjects(unittest.TestCase):
    def test_datasource_config(self):
        pass

    def test_dataflow_and_skipper_versions_required(self):
        with self.assertRaises(ValueError):
            TestConfig.from_env_vars(env={})
        with self.assertRaises(ValueError):
            TestConfig.from_env_vars(env={'DATAFLOW_VERSION': '2.10.0-SNAPSHOT'})
        with self.assertRaises(ValueError):
            TestConfig.from_env_vars(env={'SKIPPER_VERSION': '2.9.0-SNAPSHOT'})
        test_config = TestConfig.from_env_vars(env={'SKIPPER_VERSION': '2.9.0-SNAPSHOT', 'DATAFLOW_VERSION': '2.10.0-SNAPSHOT'})
        self.assertEqual('2.9.0-SNAPSHOT',test_config.skipper_version)
        self.assertEqual('2.10.0-SNAPSHOT', test_config.dataflow_version)

    def test_env_present_test_config(self):
        test_config = TestConfig.from_env_vars(env={'DATAFLOW_VERSION': '2.10.0-SNAPSHOT',
                                                    'SKIPPER_VERSION': '2.9.0-SNAPSHOT',
                                                    'DEPLOY_WAIT_SEC': '60',
                                                    'MAX_RETRIES': '10'})
        self.assertEqual(60, test_config.deploy_wait_sec)
        self.assertEqual(10, test_config.max_retries)
        self.assertEqual(test_config.maven_repos['repo1'], 'https://repo.spring.io/libs-snapshot')
