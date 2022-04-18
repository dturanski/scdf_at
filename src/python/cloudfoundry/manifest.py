import yaml
import json
import logging
import re

logger = logging.getLogger(__name__)

'''
applications:
- name: dataflow-server
  host: dataflow-server-oracle
  memory: 2G
  disk_quota: 2G
  instances: 1
  buildpack: java_buildpack_offline
  path: ./spring-cloud-dataflow-server-2.10.0-SNAPSHOT.jar

  env:
    SPRING_APPLICATION_NAME: data-flow-server
    SPRING_CLOUD_DATAFLOW_SERVER_URI: https://dataflow-server.apps.alturas.cf-app.com
    SPRING_PROFILES_ACTIVE: cloud
    JBP_CONFIG_SPRING_AUTO_RECONFIGURATION: '{enabled: false}'    
    SPRING_CLOUD_SKIPPER_CLIENT_SERVER_URI: https://skipper-server.apps.alturas.cf-app.com/api
    SPRING_DATASOURCE_URL: 'jdbc:oracle:thin:@34.123.44.62:1521:xe'
    SPRING_DATASOURCE_USERNAME: scdf
    SPRING_DATASOURCE_PASSWORD: b1tnam1
    SPRING_DATASOURCE_DRIVER_CLASS_NAME: oracle.jdbc.OracleDriver
    SPRING_APPLICATION_JSON: |-

       {     
          "maven": {
            "remoteRepositories" : {
               "repo1" : {
                  "url": "https://repo.spring.io/libs-snapshot"
               }
            }
          },
          "logging.level.com.zaxxer.hikari": "debug",
          "management.endpoints.web.exposure.include": "*",
          "spring.cloud.dataflow.task.platform.cloudfoundry.accounts" : {
             "default" : {
                "connection": {
                    "url": "https://api.sys.alturas.cf-app.com",
                    "org": "p-dataflow",
                    "space": "dturanski",
                    "domain": "apps.alturas.cf-app.com",
                    "username": "admin",
                    "password": "Or1AbwZqANDQb_3NJfBLy1rol64uYI_m"
                },
                "deployment": {
                   "services" : []
                }
             }
          }
       }
'''


def create_for_scdf(path, cf_config, options):
    dataflow_config = cf_config.dataflow_config
    schedules_enabled = options.schedules_enabled
    datasource_config = cf_config.datasource_config
    test_config = cf_config.test_config
    contents = {'applications': [
        {'name': 'dataflow_server', 'buildacks': test_config.buildpacks, 'timeout': 120, 'path': path, 'memory': '2G',
         'disk_quota': '2G',
         }]}

    app = contents['applications'][0]
    app['env'] = dataflow_config.env

    print(yaml.dump(
        {'SPRING_APPLICATION_JSON': json.dumps(spring_application_json(cf_config, options), indent=4)},
        sort_keys=False, default_flow_style=False, default_style='|'))

    logger.info(yaml.dump(contents, sort_keys=False))
    with open(path, 'w') as manifest:
        yaml.dump(contents, manifest, sort_keys=False)


def spring_application_json(cf_config, options):
    task_services = options.task_services.split(',') if options.task_services else []
    saj = {}
    repos = {}
    for i in range(0, len(cf_config.test_config.maven_repos)):
        repos["repo%d" % i] = {"url": cf_config.test_config.maven_repos[i]}

    saj['maven'] = {"remoteRepositories": repos}
    saj['spring.cloud.dataflow.task.platform.cloudfoundry.accounts'] = \
        {"default": {'connection': cf_config.deployer_config.connection(), 'deployment': {'services': task_services}}}
    return saj


def create_for_skipper(path, cf_config, options):
    pass
