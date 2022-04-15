import json
# create the patch
from json import JSONEncoder
def wrapped_default(self, obj):
    return getattr(obj.__class__, "__json__", wrapped_default.default)(obj)
wrapped_default.default = JSONEncoder().default

# apply the patch
JSONEncoder.original_default = JSONEncoder.default
JSONEncoder.default = wrapped_default

class App(json.JSONEncoder):
    def __init__(self, name, requested_state, instances, memory, disk, urls):
        self.name = name
        self.requested_state = requested_state
        self.instances = instances
        self.memory = memory
        self.disk = disk
        self.urls = urls

    def __json__(self):
        return self.__dict__


class Service(json.JSONEncoder):

    def __init__(self, name, service, plan, status, message):
        self.name = name
        self.service = service
        self.plan = plan
        self.status = status
        self.message = message

    def __json__(self):
        return self.__dict__
