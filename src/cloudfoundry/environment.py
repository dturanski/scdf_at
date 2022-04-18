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
        logger.info("Using config:\n" + json.dumps(config, indent=4))
        if config.services_config:
            logger.info("Getting current services...")
            services = cf.services()
            logger.info("verifying required services:" + str([str(s) for s in config.services_config]))
            required_services = {'create': [], 'wait': [], 'failed': [], 'deleting': [], 'unknown': []}

            for required_service in config.services_config:
                if required_service not in [ServiceConfig.of_service(service) for service in services]:
                    logger.debug("Adding %s to required services" % required_service)
                    required_services['create'].append(required_service)
                else:
                    logger.debug("Checking health of required service %s" % str(required_service))
                    for service in services:
                        if ServiceConfig.of_service(service) == required_service:
                            if service.status not in ['create succeeded', 'update succeeded']:
                                logger.warning(
                                    "status of required service %s is %s" % (service.name, service.status))
                                if service.status == 'create in progress':
                                    required_services['wait'].append(service)
                                elif service.status == 'delete in progress':
                                    required_services['deleting'].append(service)
                                elif service.status == 'create failed':
                                    required_services['failed'].append(service)
                                else:
                                    required_services['unknown'].append(service)
                        else:
                            logger.debug("required service is healthy %s" % str(required_service))

                for s in required_services['deleting']:
                    logger.info("waiting for required service %s to be deleted" % str(s))
                    if not cf.wait_for(success_condition=lambda: cf.service(s.name) is None,
                                       wait_message="waiting for %s to be deleted" % s.name):
                        raise SystemExit("FATAL: %s " % cf.service(s.name))
                    required_services['create'].append(ServiceConfig.of_service(s))

                for s in required_services['wait']:
                    if not cf.wait_for(success_condition=lambda: cf.service(s.name).status == 'create succeeded',
                                       wait_message="waiting for %s status 'create succeeded'" % s.name):
                        raise SystemExit("FATAL: %s " % cf.service(s.name))

                for s in required_services['create']:
                    logger.info("creating service:" + str(s))
                    cf.create_service(s)

    @classmethod
    def clean(cls, cf, config, options):
        if config.services_config:
            logger.info("deleting current services...")
            services = cf.services()
            for service in services:
                cf.delete_service(service.name)
        else:
            logger.info("using current services")


def setup(cf, config, options):
    config.dataflow_config.schedules_enabled = options.schedules_enabled
    if config.dataflow_config.schedules_enabled and config.services_config:
        if not [service for service in config.services_config if service.plan == "scheduler-for-pcf"]:
            scheduler_service = ServiceConfig.scheduler_default()
            logger.info("Adding default scheduler service: %s" % str(scheduler_service))
            config.services_config.append(scheduler_service)
    if options.platform == "tile":
        return Tile.setup(cf, config, options)
    elif options.platform == "cloudfoundry":
        return Standalone.setup(cf, config, options)
    else:
        logger.error("invalid platform type %s should be in [cloudfoundry,tile]" % options.platform)


def clean(cf, config, options):
    if options.platform == "tile":
        return Tile.clean(cf, config, options)
    elif options.platform == "cloudfoundry":
        return Standalone.clean(cf, config, options)
    else:
        logger.error("invalid platform type %s should be in [cloudfoundry,tile]" % options.platform)


