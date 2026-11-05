from classes.dispose import Dispose


class TransmissionDispose(Dispose):

    def __init__(self, name="DISPOSE"):
        super().__init__(name=name, started_key="created")
        self.ids, self.tx_times, self.interrupted = [], [], []

    def in_act(self, transaction=None):
        super().in_act(transaction)
        self.ids.append(transaction.get("id"))
        self.tx_times.append(self.tcurr - transaction["t_start"])
        self.interrupted.append(bool(transaction.get("interrupted")))

    def reset_statistics(self):
        super().reset_statistics()
        self.total_time_in_system = 0.0
        self.min_time, self.max_time = float("inf"), 0.0
        self.ids, self.tx_times, self.interrupted = [], [], []
