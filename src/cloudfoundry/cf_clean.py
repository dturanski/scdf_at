import logging
from cloudfoundry.environment import Tile, Standalone

logger = logging.getLogger(__name__)


def clean(cf, config, options):
    if options.platform == "tile":
        return Tile.clean(cf, config, options)
    elif options.platform == "cloudfoundry":
        return Standalone.clean(cf, config, options)
    else:
        logger.error("invalid platform type %s should be in [cloudfoundry,tile]" % options.platform)
