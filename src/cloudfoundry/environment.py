import logging, json
from cloudfoundry.config import ServiceConfig

logger = logging.getLogger(__name__)

class Tile:
    @classmethod
    def setup(cls, cf, config, options):
        cf.deployer_config.log_masked()
        if config.services_config:
            logger.info("Setting up services...")
            logger.debug("Getting current services...")
            services = cf.services()
            logger.debug("checking required services:" + json.dumps(config.services_config))

    @classmethod
    def clean(cls, cf, config, options):
        cf.deployer_config.log_masked()
        if config.services_config:
            logger.info("deleting current services...")
            services = cf.services()
        else:
            logger.info("using current services...")


class Standalone:
    @classmethod
    def setup(cls, cf, config, options):
        config.deployer_config.log_masked()
        if config.services_config:
            logger.info("Getting current services...")
            services = cf.services()
            logger.info("required services:" + json.dumps(config.services_config))
            required_services = {'create': [], 'wait': [], 'failed': [], 'deleting': [], 'unknown': []}

            for required_service in config.services_config:
                if required_service not in [ServiceConfig.of_service(service)
                                            for service in services]:
                    logger.debug("Adding %s to required services" % json.dumps(required_service))
                    required_services['create'].append(required_service)
                else:
                    logger.debug("Checking health of required service" % json.dumps(required_service))
                    for service in services:
                        if ServiceConfig.of_service(service) == required_service:
                            if service.status != 'create succeeded':
                                logger.info("status of required service %s " % service.status)
                                if service.status == 'create in progress':
                                    required_services['wait'].append(service)
                                elif service.status == 'delete in progress':
                                    logger.warning("status of required service %s " % service.status)
                                    required_services['deleting'].append(service)
                                elif service.status == 'create failed':
                                    logger.warning("status of required service %s " % service.status)
                                    required_services['failed'].append(service)
                                else:
                                    logger.warning("status of required service %s " % service.status)
                                    required_services['unknown'].append(service)

                for s in required_services['create']:
                    logger.info("creating service:" + json.dumps(s))
                    cf.create_service(config, s)
                for s in required_services['deleting']:
                    logger.info("waiting for required service %s to be deleted" % json.dumps(s))

    @classmethod
    def clean(cls, cf, config, options):
        cf.deployer_config.log_masked()
        if config.services_config:
            logger.info("deleting current services...")
            services = cf.services()
        else:
            logger.info("using current services...")
