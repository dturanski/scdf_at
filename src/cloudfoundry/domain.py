import json


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
