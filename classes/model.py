class Model:

    def __init__(self, elements):
        self.elements = elements
        self.tcurr = 0.0
        self.tnext = 0.0
        self.t_reset = 0.0

    def settle(self):
        changed = True
        while changed:
            changed = False
            for e in self.elements:
                if e.update_state():
                    changed = True

    def simulate(self, time_modeling, warmup=0.0, verbose=False, print_result=True):
        reset_done = warmup <= 0.0
        while self.tcurr < time_modeling:
            self.tnext = min(e.tnext for e in self.elements)
            if self.tnext == float("inf"):
                break

            for e in self.elements:
                e.do_statistics(self.tnext - self.tcurr)

            self.tcurr = self.tnext
            for e in self.elements:
                e.tcurr = self.tcurr

            for e in self.elements:
                if e.tnext == self.tcurr:
                    e.out_act()
            self.settle()

            if not reset_done and self.tcurr >= warmup:
                for e in self.elements:
                    e.reset_statistics()
                self.t_reset = self.tcurr
                reset_done = True

            if verbose:
                self.print_info()

        if print_result:
            self.print_result()

    def observed_time(self):
        return self.tcurr - self.t_reset

    def print_info(self):
        print(f"\n--- t = {self.tcurr:.4f} ---")
        for e in self.elements:
            e.print_info()

    def print_result(self):
        print("\n------------- РЕЗУЛЬТАТИ -------------")
        for e in self.elements:
            e.print_result()
