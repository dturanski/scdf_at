import unittest
import cloudfoundry.platform.tile as tile
from cloudfoundry.platform.config.db import DatasourceConfig
from install import shell


class MyTestCase(unittest.TestCase):
    def test_user_provided(self):
        # Not appropriate to use foo bar values here for some reason
        db_config = DatasourceConfig(name="skipper_pro_1_5_0_kafka_0", url="jdbc:postgresql", username="user",
                                     password="password",
                                     driver_class_name="org.postgresql.Driver")

        tile.user_provided(db_config)

    def test_openssl(self):
        sh = shell.Shell(dry_run=True)
        proc =sh.exec(
            'openssl s_client -connect %s:443 -showcerts > %s.cer < /dev/null' % (
            'uaa.sys.avenal.cf-app.com.cer', 'uaa.sys.avenal.cf-app.com.cer'),
            capture_output=False)
        sh.log_command(proc)



if __name__ == '__main__':
    unittest.main()
