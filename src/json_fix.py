# create the patch
from json import JSONEncoder


def patch():
    def wrapped_default(self, obj):
        return getattr(obj.__class__, "__json__", wrapped_default.default)(obj)

    wrapped_default.default = JSONEncoder().default

    # apply the patch
    JSONEncoder.original_default = JSONEncoder.default
    JSONEncoder.default = wrapped_default
