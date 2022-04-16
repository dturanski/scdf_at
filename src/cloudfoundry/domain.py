import json


class JSonEnabled(json.JSONEncoder):
    def __json__(self):
        dict = self.__dict__
        for k,v in dict.items():
            if 'password' in k or 'secret' in k:
                dict[k] = "*************" if v else None
        return dict

    def __str__(self):
        return json.dumps(self)


class App(JSonEnabled):
    def __init__(self, name, requested_state, instances, memory, disk, urls):
        self.name = name
        self.requested_state = requested_state
        self.instances = instances
        self.memory = memory
        self.disk = disk
        self.urls = urls


class Service(JSonEnabled):

    def __init__(self, name, service, plan, status, message):
        self.name = name
        self.service = service
        self.plan = plan
        self.status = status
        self.message = message
