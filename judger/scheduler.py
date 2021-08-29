from typing import List, Iterator


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