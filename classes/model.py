class Model:

    def __init__(self, elements):
        self.elements = elements
        self.tcurr = 0.0
        self.tnext = 0.0
        self.t_reset = 0.0

    def update_blocking(self):
        for e in self.elements:
            e.update_state()

    def observed_time(self):
        return self.tcurr - self.t_reset

    def simulate(self, time_modeling, warmup=0.0, verbose=False, print_result=True):
        reset_done = warmup <= 0.0
        while self.tcurr < time_modeling:
            self.tnext = min(e.tnext for e in self.elements)
            if self.tnext == float("inf"):
                break
            if not reset_done and self.tnext >= warmup:
                for e in self.elements:
                    e.do_statistics(warmup - self.tcurr)
                for e in self.elements:
                    e.reset_statistics()
                self.t_reset = warmup
                reset_done = True
                for e in self.elements:
                    e.do_statistics(self.tnext - warmup)
            else:
                for e in self.elements:
                    e.do_statistics(self.tnext - self.tcurr)
            self.tcurr = self.tnext
            for e in self.elements:
                e.tcurr = self.tcurr
            for e in self.elements:
                if e.tnext == self.tcurr:
                    e.out_act()
            self.update_blocking()
            if verbose:
                self.print_info()
        if print_result:
            self.print_result()

    def print_info(self):
        print(f"\n--- t = {self.tcurr:.4f} ---")
        for e in self.elements:
            e.print_info()

    def print_result(self):
        for e in self.elements:
            e.print_result()
