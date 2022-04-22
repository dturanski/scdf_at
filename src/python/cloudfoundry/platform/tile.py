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

import logging
import json
import sys
import subprocess
import re

logger = logging.getLogger(__name__)


def credentials_from_service_key():
    dataflow_service_instance = sys.argv[1]
    service_key = sys.argv[2]
    get_service_key = "cf service-key %s %s" % (dataflow_service_instance, service_key)
    out = subprocess.getoutput(get_service_key)
    if 'FAILED' in out:
        print(out)
        exit(1)

    creds = re.sub("Getting key.+\n", "", out)
    doc = json.loads(creds)
    print("export SPRING_CLOUD_DATAFLOW_CLIENT_AUTHENTICATION_TOKEN_URI=%s; " % doc['access-token-url'])
    print("export SPRING_CLOUD_DATAFLOW_CLIENT_AUTHENTICATION_CLIENT_ID=%s; " % doc['client-id'])
    print("export SPRING_CLOUD_DATAFLOW_CLIENT_AUTHENTICATION_CLIENT_SECRET=%s; " % doc['client-secret'])
    print("export SPRING_CLOUD_DATAFLOW_CLIENT_SERVER_URI=%s" % doc['dataflow-url'])


def setup(cf, config):
    cf.deployer_config.log_masked()
    if config.service_configs:
        logger.info("Setting up services...")
        logger.debug("Getting current services...")
        services = cf.services()
        logger.debug("checking required services:" + json.dumps(config.service_configs))


def clean(cf, config, apps_only):
    cf.deployer_config.log_masked()
    if config.service_configs:
        logger.info("deleting current services...")
        services = cf.services()
    else:
        logger.info("using current services...")

# def user_provided_postgresql(self,db, server):
#     name = dbname(db, server)
#     user_provided = {}
#     port = int(db['port'])
#     user_provided['uri'] = "postgresql://%s:%d/%s?user=%s&password=%s" % (
#     db['host'], port, name, db['username'], db['password'])
#     user_provided['jdbcUrl'] = "jdbc:%s" % user_provided['uri']
#     user_provided['username'] = db['username']
#     user_provided['password'] = db['password']
#     user_provided['dbname'] = name
#     user_provided['host'] = db['host']
#     user_provided['port'] = port
#     user_provided['tags'] = ['postgres']
#     ups = {}
#     ups['user-provided'] = user_provided
#     return ups
#
# def user_provided_oracle(self, db, server):
#     name = dbname(db, server)
#     user_provided = {}
#     port = int(db['port'])
#     user_provided['uri'] = "oracle:thin://%s:%d/%s?user=%s&password=%s" % (
#     db['host'], port, name, db['username'], db['password'])
#     user_provided['jdbcUrl'] = "jdbc:%s" % user_provided['uri']
#     user_provided['username'] = db['username']
#     user_provided['password'] = db['password']
#     user_provided['dbname'] = name
#     user_provided['host'] = db['host']
#     user_provided['port'] = port
#     user_provided['tags'] = ['oracle']
#     ups = {}
#     ups['user-provided'] = user_provided
#     return ups
#
# def user_provided(self, db, server):
#     if db['provider'] == 'postgresql':
#         return self.user_provided_postgresql(db, server)
#     elif db['provider'] == 'oracle':
#         return self.user_provided_oracle(db, server)
#     else:
#         raise Exception("Invalid db provider %s" % db['provider'])
#
# schedules_enabled = os.getenv(
#     "SPRING_CLOUD_DATAFLOW_FEATURES_SCHEDULES_ENABLED", 'false')
# dataflow_tile_configuration = os.getenv("DATAFLOW_TILE_CONFIGURATION")
# if dataflow_tile_configuration:
#     config = json.loads(dataflow_tile_configuration)
#
# if not config.get('relational-data-service') or not config.get('skipper-relational'):
#     db
#
# if not config.get('skipper-relational'):
#     config['skipper-relational'] = user_provided(db, 'skipper')
#
# if not config.get('relational-data-service'):
#     config['relational-data-service'] = user_provided(db, 'dataflow')
#
# if not config.get('maven-cache'):
#     config['maven-cache'] = True
#
# if schedules_enabled.lower() == 'true' and not 'scheduler' in config.keys():
#     schedules_service_name = os.environ['SCHEDULES_SERVICE_NAME']
#     schedules_plan_name = os.environ['SCHEDULES_PLAN_NAME']
#     config['scheduler'] = {'name': schedules_service_name, 'plan': schedules_plan_name}
# if config:
#     print(json.dumps(config))
