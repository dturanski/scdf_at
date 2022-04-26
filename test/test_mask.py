import unittest
import logging
import scdf_at
import json

from scdf_at.util import masked

scdf_at.enable_debug_logging()

logger = logging.getLogger(__name__)


class TestMask(unittest.TestCase):
    def test_logging_secrets(self):
        m = masked(
            "postgresql://12.34.46.789:5432/dbname?user=user&password=password")

        with open('tile-config.json') as config:
            m = json.loads(masked(json.load(config)))
            self.assertEqual("*" * 8, m['skipper-relational']['user-provided']['username'])
            self.assertEqual("*" * 8, m['skipper-relational']['user-provided']['password'])
            self.assertEqual('skipper_db', m['skipper-relational']['user-provided']['dbname'])
            self.assertTrue("password=" + "*" * 8 in m['skipper-relational']['user-provided']['uri'])
            self.assertTrue("user=" + "*" * 8 in m['skipper-relational']['user-provided']['uri'])


if __name__ == '__main__':
    unittest.main()
