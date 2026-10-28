from classes.funrand import FunRand
from classes.create import Create
from classes.buffer import Buffer
from classes.channel import Channel
from classes.chains import MainChain, BackupChain
from classes.transmission_dispose import TransmissionDispose
from classes.model import Model

PARAMS = {
    "arrival": (9, 4),
    "tx": (7, 3),
    "work": (200, 35),
    "switch": 2.0,
    "recovery": (23, 7),
}


def unif(d, s):
    return FunRand.uniform(d - s, d + s)


class State:

    def attach(self, main_chain, backup_chain, main, backup, front):
        self._main_chain = main_chain
        self._backup_chain = backup_chain
        self._main = main
        self._backup = backup
        self._front = front

    @property
    def k_work(self):
        return self._main_chain.n_work

    @property
    def k_on(self):
        return self._backup_chain.n_on

    @property
    def k_main(self):
        return 1 if self._main.busy else 0

    @property
    def k_backup(self):
        return 1 if self._backup.busy else 0

    @property
    def l_front(self):
        return max(0, self._front.queue_len() - 1)

    def b1(self):
        return self.k_work == 0 or self.k_main == 1

    def b2(self):
        return self.k_work == 1 or self.k_backup == 1 or self.l_front >= 1

    def b3(self):
        return self.k_work == 1

    def b4(self):
        return (self.k_work == 0 and self.k_on == 0) or self.k_backup == 1

    def b5(self):
        return self.k_work == 1

    def b6(self):
        return self.k_work == 0


def build_model(p=PARAMS):
    st = State()

    main_chain = MainChain(work_fn=lambda: unif(*p["work"]),
                           repair_fn=lambda: unif(*p["recovery"]))
    backup_chain = BackupChain(switch_fn=lambda: p["switch"],
                               b5=lambda: st.b5(), b6=lambda: st.b6())

    def main_finish(channel, transaction):
        tau = unif(*p["tx"])
        t_fail = main_chain.work_end()
        if channel.tcurr + tau <= t_fail:
            return channel.tcurr + tau
        transaction["interrupted"] = True
        return t_fail

    def backup_finish(channel, transaction):
        return channel.tcurr + unif(*p["tx"])

    create = Create(delay_generator=lambda tr: unif(*p["arrival"]), name="CREATE",
                    first_time=unif(*p["arrival"]))
    buffer = Buffer(name="BUFFER")
    front = Buffer(name="BACKUP_FRONT", max_queue=2)
    main = Channel(main_finish, name="MAIN")
    backup = Channel(backup_finish, name="BACKUP")
    exit_main = TransmissionDispose("EXIT_N1")
    exit_backup = TransmissionDispose("EXIT_N2")
    st.attach(main_chain, backup_chain, main, backup, front)

    create.next_element = buffer
    buffer.add_route(main, lambda o, tr: st.b1())
    buffer.add_route(front, lambda o, tr: st.b2())
    front.add_route(backup, lambda o, tr: st.b4())
    route_b3 = main.add_route(front, lambda o, tr: st.b3())
    main.add_route(exit_main)
    backup.add_route(exit_backup)

    model = Model([main_chain, backup_chain, create, main, backup, front, buffer,
                   exit_main, exit_backup])
    parts = {"failure": main_chain, "backup_chain": backup_chain, "create": create,
             "buffer": buffer, "front": front, "main": main, "backup": backup,
             "exit_main": exit_main, "exit_backup": exit_backup, "route_b3": route_b3}
    return model, parts
