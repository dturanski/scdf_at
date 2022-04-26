import sys, os, logging
from json import JSONEncoder


sys.path.append(os.path.join(sys.path[0], ".."))


def json_patch():
    def wrapped_default(self, obj):
        return getattr(obj.__class__, "__json__", wrapped_default.default)(obj)

    wrapped_default.default = JSONEncoder().default

    # apply the patch
    JSONEncoder.original_default = JSONEncoder.default
    JSONEncoder.default = wrapped_default


json_patch()

logging.basicConfig(level=logging.INFO, format='%(name)s - %(asctime)s - %(levelname)s:  %(message)s')


def enable_debug_logging():
    level = logging.DEBUG
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
    logger.debug("DEBUG logging enabled")
