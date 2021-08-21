import logging
from typing import Callable, Dict, Iterator, List

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Event:

    def __init__(self, name: str, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs
    
    def __repr__(self):
        return f'Event{{name={self.name},args={self.args},kwargs={self.kwargs}}}'


class Core:

    def __init__(self) -> None:
        self.handlers = dict()
        self.pending_queues: Dict[str, List[Event]] = dict()
        self.persistent_states: Dict[str, dict] = dict()
        self.global_config: Dict[str, dict] = dict()

    def send_message(self, target, method, *args, **kwargs):
        handler = self.handlers.get(target)
        if target not in self.pending_queues:
            self.pending_queues[target] = []
        self.pending_queues[target].append(
            Event(f'{target}-{method}',
                  *args,
                  **kwargs)
        )

    def register_handler(self, name: str, handler: Callable):
        self.handlers[name] = handler

    def register_role(self, name: str, role):
        self.global_config[name] = role
        self.persistent_states[name] = dict()
    
    def persistent_state(self, name):
        return self.persistent_state[name]

    def role_run(self, role):
        pending_queue: List[Event] = self.pending_queues.get(role)
        if pending_queue and len(pending_queue) > 0:
            event = pending_queue.pop(0)
            handler = self.handlers.get(event.name)
            r = handler(*event.args, **event.kwargs)
            logger.debug(f'on event {event}, return {r}')
        else:
            logger.debug(f'on idle {role}')


class Role:

    def __init__(self, name: str, core: Core):
        self.name = name
        self.core = core

    def event_handlers(self) -> Dict[str, Callable]:
        raise NotImplemented

    def register_handlers(self) -> None:
        for name, handler in self.event_handlers().items():
            self.core.register_handler(f'{self.name}-{name}', handler)


class SchedulerBase:

    def __init__(self, roles: List[str]) -> None:
        self.roles = roles
        self.active_role = None
    
    def schedule_plan(self) -> Iterator[str]:
        return NotImplemented


class RoundRobinScheduler(SchedulerBase):

    def schedule_plan(self):
        idx = 0
        while True:
            role = self.roles[ idx ]
            idx = (idx + 1) % len(self.roles)
            yield role


def run_judger(conf):
    core = Core()

    roles_conf = conf.get('roles', [])
    for name, concrete_role_type in roles_conf.items():
        role: Role = concrete_role_type(name, core)
        role.register_handlers()
        core.register_role(name, role)
        core.pending_queues[name] = [Event(f'{name}-on_start')]

    scheduler = conf['scheduler'](list(roles_conf.keys()))
    for active_role in scheduler.schedule_plan():
        core.role_run(active_role)