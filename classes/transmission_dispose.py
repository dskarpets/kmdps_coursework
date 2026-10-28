from classes.dispose import Dispose


class TransmissionDispose(Dispose):

    def __init__(self, name="DISPOSE"):
        super().__init__(name=name, started_key="created")
        self.ids = []
        self.tx_times = []
        self.interrupted = []

    def in_act(self, transaction=None):
        super().in_act(transaction)
        self.ids.append(transaction["id"])
        self.tx_times.append(self.tcurr - transaction["t_start"])
        self.interrupted.append(bool(transaction.get("interrupted", False)))

    def reset_statistics(self):
        self.quantity = 0
        self.total_time_in_system = 0.0
        self.min_time = float("inf")
        self.max_time = 0.0
        self.ids = []
        self.tx_times = []
        self.interrupted = []
