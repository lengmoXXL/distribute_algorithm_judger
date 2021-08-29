import logging
from typing import List, Dict, Callable

from judger.scheduler import SchedulerBase


logger = logging.getLogger()


class RoleState:

    READY = 1
    WAITING = 2
    DEAD = 3


class RoleInfo:

    def __init__(self, name: str) -> None:
        self.name = name
        self.state: RoleState = RoleState.READY
        self.active_ts = 0
        self.pending_queue = [Event(f'{name}-on_start')]


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
        self.persistent_states: Dict[str, dict] = dict()
        self.global_config: Dict[str, RoleInfo] = dict()
        self.global_ts = 0

    def send_message(self, target, method, *args, **kwargs):
        role_info = self.global_config[target]
        role_info.pending_queue.append(
            Event(f'{target}-{method}',
                  *args,
                  **kwargs)
        )

    def register_handler(self, name: str, handler: Callable):
        self.handlers[name] = handler

    def register_role(self, name: str):
        self.global_config[name] = RoleInfo(name)
        self.persistent_states[name] = dict()
    
    def persistent_state(self, name):
        return self.persistent_state[name]

    def run(self, scheduler: SchedulerBase):
        plan = scheduler.schedule_plan()
        while True:
            self.global_ts += 1

            if not self.exist_ready_role():
                logger.info(f'{self.global_ts} idle')
                continue

            role_info = None
            while True:
                active_role = next(plan)
                role_info: RoleInfo = self.global_config[active_role]
                if role_info.state == RoleState.READY and len(role_info.pending_queue) > 0:
                    break
                if role_info.state == RoleState.WAITING and role_info.active_ts <= self.global_ts:
                    role_info.state = RoleState.READY
                    if len(role_info.pending_queue) > 0:
                        break

            event: Event = role_info.pending_queue.pop(0)
            handler = self.handlers.get(event.name)
            r = handler(*event.args, **event.kwargs)
            logger.debug(f'on event {event}, return {r}')

            
    def exist_ready_role(self):
        for role_info in self.global_config.values():
            if role_info.state == RoleState.READY and len(role_info.pending_queue) > 0:
                return True
            if role_info.state == RoleState.WAITING and role_info.active_ts <= self.global_ts and len(role_info.pending_queue) > 0:
                return True
        return False

    def sleep(self, name: str, ts: int):
        self.global_config[name].state = RoleState.WAITING
        self.global_config[name].active_ts = self.global_ts + ts


class CoreHandle:

    def __init__(self, name: str, core: Core) -> None:
        self._name = name
        self._core = core
    
    def send_message(self, target, method, *arg, **kwargs):
        self._core.send_message(target, method, *arg, **kwargs)

    def sleep(self, ts: int):
        self._core.sleep(self._name, ts)

    def roles(self):
        return self._core.global_config.keys()