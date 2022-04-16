import logging

logger = logging.getLogger(__name__)

class Tile:
    pass



def clean_tile(cf, config, options):
    logger.info("setting up the CF environment for platform %s and binder %a" % (options.platform, options.binder))


def clean_standalone(cf, config, options):
    logger.info("setting up the CF environment for platform %s and binder %a" % (options.platform, options.binder))
    cf.connect.log_masked()
    logger.info("Getting current services...")
    services = cf.services()
    logger.info("Required services...")


def clean(cf, config, options):
    if options.platform == "tile":
        return clean_tile(cf, config, options)
    elif options.platform == "cloudfoundry":
        return clean_standalone(cf, config, options)
    else:
        logger.error("invalid platform:%s" % options.platform)
