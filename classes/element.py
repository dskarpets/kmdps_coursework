class Element:

    _next_id = 0

    def __init__(self, name=None):
        self.tcurr = 0.0
        self.tnext = float("inf")

        self.state = 0
        self.quantity = 0

        self.next_element = None

        self.id = Element._next_id
        Element._next_id += 1
        self.name = name if name else f"element{self.id}"

    def in_act(self, transaction=None):
        pass

    def out_act(self):
        self.quantity += 1

    def update_state(self):
        return False

    def do_statistics(self, delta):
        pass

    def reset_statistics(self):
        self.quantity = 0

    def print_info(self):
        print(f"{self.name}: state={self.state} quantity={self.quantity} tnext={self.tnext}")

    def print_result(self):
        print(f"{self.name}: quantity = {self.quantity}")
