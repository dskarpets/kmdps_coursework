from classes.element import Element


class MainChain(Element):

    WORK, REPAIR = 0, 1

    def __init__(self, work_fn, repair_fn, name="MAIN_CHAIN"):
        super().__init__(name=name)
        self.generators = (work_fn, repair_fn)
        self.phase = MainChain.WORK
        self.tnext = work_fn()
        self.failures = 0

    @property
    def n_work(self):
        return 1 if self.phase == MainChain.WORK else 0

    def work_end(self):
        return self.tnext

    def out_act(self):
        if self.phase == MainChain.WORK:
            self.failures += 1
        self.phase = 1 - self.phase
        self.tnext = self.tcurr + self.generators[self.phase]()

    def reset_statistics(self):
        self.failures = 0


class BackupChain(Element):
    OFF, SWITCH, ON = 0, 1, 2

    def __init__(self, switch_fn, b5, b6, name="BACKUP_CHAIN"):
        super().__init__(name=name)
        self.switch_fn = switch_fn
        self.b5 = b5
        self.b6 = b6
        self.phase = BackupChain.OFF

    @property
    def n_on(self):
        return 1 if self.phase == BackupChain.ON else 0

    def update_state(self):
        if self.phase == BackupChain.OFF and not self.b5():
            self.phase = BackupChain.SWITCH
            self.tnext = self.tcurr + self.switch_fn()
            return True
        if self.phase == BackupChain.ON and not self.b6():
            self.phase = BackupChain.OFF
            return True
        return False

    def out_act(self):
        self.phase = BackupChain.ON
        self.tnext = float("inf")
