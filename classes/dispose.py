from classes.element import Element


class Dispose(Element):
    def __init__(self, name="DISPOSE", started_key="created"):
        super().__init__(name=name)
        self.started_key = started_key
        self.total_time_in_system = 0.0
        self.min_time = float("inf")
        self.max_time = 0.0

    def in_act(self, transaction=None):
        self.quantity += 1
        if transaction is not None and self.started_key in transaction:
            spent = self.tcurr - transaction[self.started_key]
            self.total_time_in_system += spent
            self.min_time = min(self.min_time, spent)
            self.max_time = max(self.max_time, spent)

    def get_mean_time_in_system(self):
        if self.quantity == 0:
            return 0.0
        return self.total_time_in_system / self.quantity

    def print_result(self):
        super().print_result()
        if self.quantity > 0:
            print(f"    середній час у системі = {self.get_mean_time_in_system():.4f} "
                  f"(min={self.min_time:.4f}, max={self.max_time:.4f})")
