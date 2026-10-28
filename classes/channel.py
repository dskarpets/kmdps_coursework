from classes.element import Element
from classes.process import Route


class CountedRoute(Route):

    def __init__(self, target, blocked_fn=None):
        super().__init__(target, 1.0, blocked_fn)
        self.passed = 0


class Channel(Element):

    def __init__(self, finish_fn, name="CHANNEL"):
        super().__init__(name=name)
        self.finish_fn = finish_fn
        self.routes = []
        self.transaction = None
        self.busy_time = 0.0

    @property
    def busy(self):
        return self.transaction is not None

    def add_route(self, target, blocked_fn=None):
        route = CountedRoute(target, blocked_fn)
        self.routes.append(route)
        return route

    def in_act(self, transaction=None):
        if self.transaction is not None:
            raise RuntimeError(f"{self.name}: вхід у зайнятий пристрій (відмова мала б бути заблокована)")
        self.transaction = transaction
        transaction.setdefault("t_start", self.tcurr)
        self.tnext = self.finish_fn(self, transaction)

    def out_act(self):
        transaction = self.transaction
        for route in self.routes:
            if not route.is_blocked(self, transaction):
                self.transaction = None
                self.tnext = float("inf")
                self.quantity += 1
                route.passed += 1
                route.target.in_act(transaction)
                return
        raise RuntimeError(f"{self.name}: усі маршрути виходу закриті")

    def do_statistics(self, delta):
        if self.transaction is not None:
            self.busy_time += delta

    def reset_statistics(self):
        super().reset_statistics()
        self.busy_time = 0.0
        for route in self.routes:
            route.passed = 0
