import unittest
from cloudfoundry.platform.tile import setup_certs
from scdf_at.shell import Shell
from scdf_at import enable_debug_logging

enable_debug_logging()

class TestCerts(unittest.TestCase):
    def test_certs(self):
        setup_certs('uaa.sys.avenal.cf-app.com', Shell(dry_run=True))


if __name__ == '__main__':
    unittest.main()
