# Distribute Algorithm Judger


该库的主要目标是能够实现对分布式算法的judger。分布式算法存在很多的不确定性，为了实现确定性的judge，所以实现了一个 scheduler，且把 scheduler 支持扩展，用单线程模拟多线程的调度，从而确定的能否复现出一些case，未来如果实现 scheduler 通过配置文件来做确定性的调度，能够辅助对一些分布式算法做开发和测试。

## 如何使用

```
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
```


## 一些设计的思考可以参考 docs 文件夹的md的文件