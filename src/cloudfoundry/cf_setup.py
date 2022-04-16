import logging
from cloudfoundry.environment import Tile, Standalone

logger = logging.getLogger(__name__)


def setup_tile(cf, config, options):
    logger.info("setting up the CF environment for platform %s and binder %a" % (options.platform, options.binder))


def setup(cf, config, options):
    if options.platform == "tile":
        return Tile.setup(cf, config, options)
    elif options.platform == "cloudfoundry":
        return Standalone.setup(cf, config, options)
    else:
        logger.error("invalid platform type %s should be in [cloudfoundry,tile]" % options.platform)
