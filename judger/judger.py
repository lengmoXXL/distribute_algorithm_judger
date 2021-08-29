import logging
from typing import Callable, Dict

from judger.core import Core, CoreHandle, Event

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    level=logging.DEBUG)


class BaseRole:

    def __init__(self, name: str, core_handle: CoreHandle):
        self.name = name
        self.core_handle = core_handle

    def event_handlers(self) -> Dict[str, Callable]:
        raise NotImplemented

def run_judger(conf):
    core = Core()

    roles_conf = conf.get('roles', [])
    for name, concrete_role_type in roles_conf.items():
        role: BaseRole = concrete_role_type(name, CoreHandle(name, core))
        core.register_role(name)
        for handler_name, handler in role.event_handlers().items():
            core.register_handler(f'{name}-{handler_name}', handler)

    scheduler = conf['scheduler'](list(roles_conf.keys()))
    core.run(scheduler)