from classes.element import Element

FREE, BUSY, BLOCKED = 0, 1, 2
INF = float("inf")


class Route:

    def __init__(self, target, blocked=None):
        self.target = target
        self.blocked = blocked
        self.passed = 0

    def is_closed(self, t):
        return self.blocked is not None and self.blocked(t)


class Process(Element):

    def __init__(self, name, delay=None, end_time=None, num_devices=1, max_queue=0):
        super().__init__(name=name)
        self.delay = delay
        self.end_time = end_time
        self.max_queue = max_queue
        self.k = [FREE] * num_devices
        self.request = [None] * num_devices
        self.end = [INF] * num_devices
        self.queue = []
        self.routes = []
        self.refused = 0
        self.busy_time = 0.0

    def add_route(self, target, blocked=None):
        r = Route(target, blocked)
        self.routes.append(r)
        return r

    def queue_len(self):
        return len(self.queue)

    def in_act(self, transaction=None):
        if FREE in self.k:
            self._start(self.k.index(FREE), transaction)
        elif len(self.queue) < self.max_queue:
            self.queue.append(transaction)
        else:
            self.refused += 1

    def out_act(self):
        for j in range(len(self.k)):
            if self.k[j] == BUSY and self.end[j] <= self.tcurr:
                route = self._open_route()
                if route is None:
                    self.k[j] = BLOCKED
                    self.end[j] = INF
                else:
                    tr = self.request[j]
                    self.k[j] = FREE
                    self.request[j] = None
                    self.end[j] = INF
                    self.quantity += 1
                    route.passed += 1
                    if self.queue:
                        self._start(j, self.queue.pop(0))
                    route.target.in_act(tr)
        self._refresh()

    def update_state(self):
        changed = False
        for j in range(len(self.k)):
            if self.k[j] == BLOCKED and self._open_route() is not None:
                self.k[j] = BUSY
                self.end[j] = self.tcurr
                changed = True
        self._refresh()
        return changed

    def _open_route(self):
        for r in self.routes:
            if not r.is_closed(self.tcurr):
                return r
        return None

    def _start(self, j, tr):
        self.k[j] = BUSY
        self.request[j] = tr
        if self.end_time is not None:
            self.end[j] = self.end_time(self, tr)
        else:
            self.end[j] = self.tcurr + self.delay(tr)
        self._refresh()

    def _refresh(self):
        ends = [self.end[j] for j in range(len(self.k)) if self.k[j] == BUSY]
        self.tnext = min(ends) if ends else INF

    def do_statistics(self, delta):
        self.busy_time += sum(1 for s in self.k if s != FREE) * delta

    def reset_statistics(self):
        self.quantity = 0
        self.busy_time = 0.0
        self.refused = 0
        for r in self.routes:
            r.passed = 0

    def print_result(self):
        print(f"{self.name}: пройшло заявок = {self.quantity}")
