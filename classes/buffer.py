from classes.element import Element
from classes.process import Route


class Buffer(Element):
    def __init__(self, name="BUFFER", max_queue=float("inf")):
        super().__init__(name=name)
        self.max_queue = max_queue
        self.routes = []
        self.queue = []
        self.refused = 0

    def add_route(self, target, blocked_fn=None):
        self.routes.append(Route(target, 1.0, blocked_fn))

    def queue_len(self):
        return len(self.queue)

    def in_act(self, transaction=None):
        if len(self.queue) >= self.max_queue:
            self.refused += 1
            return
        self.queue.append(transaction)
        self.update_state()

    def update_state(self):
        moved = False
        while self.queue:
            target = None
            for route in self.routes:
                if not route.is_blocked(self, self.queue[0]):
                    target = route.target
                    break
            if target is None:
                break
            target.in_act(self.queue.pop(0))
            moved = True
        return moved

    def reset_statistics(self):
        super().reset_statistics()
        self.refused = 0
