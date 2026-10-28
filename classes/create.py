from classes.element import Element


class Create(Element):

    def __init__(self, delay_generator, name="CREATE", first_time=0.0, transaction_factory=None):
        super().__init__(name=name)
        self.delay_generator = delay_generator
        self.transaction_factory = transaction_factory
        self.tnext = first_time
        self._counter = 0

    def out_act(self):
        self.quantity += 1
        if self.transaction_factory is not None:
            transaction = self.transaction_factory(self._counter)
            transaction["created"] = self.tcurr
        else:
            transaction = {"id": self._counter, "created": self.tcurr}
        self._counter += 1

        self.tnext = self.tcurr + self.delay_generator(transaction)

        if self.next_element is not None:
            self.next_element.in_act(transaction)

    def print_result(self):
        print(f"{self.name}: створено заявок = {self.quantity}")
