import logging

from typing import Callable, Dict
from random import choice

from judger.judger import BaseRole, run_judger
from judger.scheduler import RoundRobinScheduler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class SayHiRole(BaseRole):

    def event_handlers(self) -> Dict[str, Callable]:
        return { 'on_start': self.on_start,
                 'say_hi': self.say_hi }
    
    def on_start(self):
        self.roles = list(self.core_handle.roles())
        self.core_handle.send_message(f'{choice(self.roles)}', 'say_hi')

    def say_hi(self):
        self.core_handle.send_message(f'{choice(self.roles)}', 'say_hi')
        self.core_handle.sleep(5)


if __name__ == '__main__':
    run_judger(
        {
            'roles': {
                'Alice': SayHiRole,
                'Bob': SayHiRole,
                'Chalie': SayHiRole
            },
            'scheduler': RoundRobinScheduler
        },
    )