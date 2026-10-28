from classes.element import Element


class Route:

    def __init__(self, target, weight=1.0, blocked_fn=None):
        self.target = target
        self.weight = weight
        self.blocked_fn = blocked_fn

    def is_blocked(self, process, transaction):
        if self.blocked_fn is None:
            return False
        return self.blocked_fn(process, transaction)


class Process(Element):

    def __init__(self, delay_generator, name="PROCESS", num_devices=1, max_queue=float("inf"),
                 queue_discipline="fifo", routing_mode="probability", routes=None, accept_fn=None,
                 priority_key=None):
        super().__init__(name=name)

        self.delay_generator = delay_generator

        self.num_devices = num_devices
        self.max_queue = max_queue
        self.queue_discipline = queue_discipline.lower()
        self.priority_key = priority_key
        self.routing_mode = routing_mode.lower()
        self.routes = routes if routes is not None else []
        self.accept_fn = accept_fn

        self.devices = [] if num_devices is None else [None] * num_devices
        self.queue = []

        self.failure = 0

        self.mean_queue = 0.0
        self.busy_time = 0.0

    def add_route(self, target, weight=1.0, blocked_fn=None):
        self.routes.append(Route(target, weight, blocked_fn))

    def _free_device_index(self):
        for i, d in enumerate(self.devices):
            if d is None:
                return i
        if self.num_devices is None:
            self.devices.append(None)
            return len(self.devices) - 1
        return None

    def _busy_count(self):
        return sum(1 for d in self.devices if d is not None)

    def _recompute_tnext(self):
        busy_finish_times = [d[0] for d in self.devices if d is not None]
        self.tnext = min(busy_finish_times) if busy_finish_times else float("inf")

    def _default_accept(self, transaction):
        return self.queue_len() < self.max_queue

    def queue_len(self):
        return len(self.queue)

    def in_act(self, transaction=None):
        idx = self._free_device_index()
        if idx is not None:
            self.devices[idx] = [self.tcurr + self.delay_generator(transaction), transaction]
            self.state = 1
            self._recompute_tnext()
            return

        accept = self.accept_fn(self, transaction) if self.accept_fn else self._default_accept(transaction)
        if accept:
            self.queue.append(transaction)
        else:
            self.failure += 1

    def _pop_from_queue(self):
        if not self.queue:
            return None
        if self.queue_discipline == "lifo":
            return self.queue.pop()
        if self.queue_discipline == "priority" and self.priority_key is not None:
            best_idx = min(range(len(self.queue)), key=lambda i: self.priority_key(self.queue[i]))
            return self.queue.pop(best_idx)
        return self.queue.pop(0)

    def _select_route(self, transaction):
        if not self.routes:
            return self.next_element

        available = [r for r in self.routes if not r.is_blocked(self, transaction)]
        if not available:
            return None

        if self.routing_mode == "priority":
            chosen = min(available, key=lambda r: r.weight)
            return chosen.target

        import random
        total_weight = sum(r.weight for r in available)
        if total_weight <= 0:
            return available[0].target
        rnd = random.random() * total_weight
        cumulative = 0.0
        for r in available:
            cumulative += r.weight
            if rnd <= cumulative:
                return r.target
        return available[-1].target

    def out_act(self):
        self.quantity += 1

        finished_indices = [i for i, d in enumerate(self.devices) if d is not None and d[0] == self.tcurr]
        for idx in finished_indices:
            finished_transaction = self.devices[idx][1]
            self.devices[idx] = None

            target = self._select_route(finished_transaction)
            if target is not None:
                target.in_act(finished_transaction)

            next_transaction = self._pop_from_queue()
            if next_transaction is not None:
                self.devices[idx] = [self.tcurr + self.delay_generator(next_transaction), next_transaction]

        self.state = 1 if self._busy_count() > 0 else 0
        self._recompute_tnext()

    def do_statistics(self, delta):
        self.mean_queue += self.queue_len() * delta
        self.busy_time += self._busy_count() * delta

    def get_mean_queue(self, total_time):
        return self.mean_queue / total_time if total_time > 0 else 0.0

    def get_utilization(self, total_time):
        if total_time <= 0 or not self.num_devices:
            return 0.0
        return self.busy_time / (self.num_devices * total_time)

    def get_failure_probability(self):
        total = self.quantity + self.failure
        if total == 0:
            return 0.0
        return self.failure / total

    def print_info(self):
        super().print_info()
        print(f"    queue={self.queue_len()} busy={self._busy_count()}/{self.num_devices} failure={self.failure}")

    def print_result(self):
        super().print_result()
        print(f"    failure = {self.failure}")
