from classes.funrand import FunRand
from classes.create import Create
from classes.model import Model
from classes.process import Process, FREE, BUSY, BLOCKED
from classes.transmission_dispose import TransmissionDispose

PARAMS = {"arrival": (9, 4), "tx": (7, 3), "work": (200, 35), "switch": 2.0, "recovery": (23, 7)}


def unif(d, s):
    return FunRand.uniform(d - s, d + s)


def build_model(p=PARAMS):
    smo1 = Process("СМО1", delay=lambda tr: 0.0, max_queue=float("inf"))
    smo3 = Process("СМО3", delay=lambda tr: 0.0, max_queue=1)
    smo4 = Process("СМО4", delay=lambda tr: unif(*p["tx"]))
    smo5 = Process("СМО5", delay=lambda tr: unif(*p["work"]))
    smo6 = Process("СМО6", delay=lambda tr: unif(*p["recovery"]))
    smo7 = Process("СМО7", delay=lambda tr: 0.0)
    smo8 = Process("СМО8", delay=lambda tr: p["switch"])
    smo9 = Process("СМО9", delay=lambda tr: 0.0)

    def end_time_smo2(smo, tr):
        tr.setdefault("t_start", smo.tcurr)
        tau = unif(*p["tx"])
        t_f = smo5.end[0]
        if smo.tcurr + tau <= t_f:
            return smo.tcurr + tau
        tr["interrupted"] = True
        return t_f

    smo2 = Process("СМО2", end_time=end_time_smo2)

    def end_time_smo4(smo, tr):
        tr.setdefault("t_start", smo.tcurr)
        return smo.tcurr + unif(*p["tx"])
    smo4.end_time = end_time_smo4
    smo4.delay = None

    exit_osn = TransmissionDispose("Вихід_осн")
    exit_rez = TransmissionDispose("Вихід_рез")

    b1 = lambda t: smo5.k[0] == FREE or smo2.k[0] != FREE
    b2 = lambda t: smo5.k[0] == BUSY or smo4.k[0] != FREE or smo3.queue_len() >= 1
    b3 = lambda t: smo5.k[0] == BUSY
    b4 = lambda t: (smo5.k[0] == FREE and smo9.k[0] != BLOCKED) or smo4.k[0] != FREE
    b5 = lambda t: smo5.k[0] == BUSY
    b6 = lambda t: smo5.k[0] == FREE

    smo1.add_route(smo2, b1)
    smo1.add_route(smo3, b2)
    route_interrupted = smo2.add_route(smo3, b3)
    smo2.add_route(exit_osn)
    smo3.add_route(smo4, b4)
    smo4.add_route(exit_rez)
    route_failure = smo5.add_route(smo6)
    smo6.add_route(smo5)
    smo7.add_route(smo8, b5)
    smo8.add_route(smo9)
    smo9.add_route(smo7, b6)

    create = Create(lambda tr: unif(*p["arrival"]), name="Генератор", first_time=unif(*p["arrival"]))
    create.next_element = smo1

    elements = [smo5, smo6, smo7, smo8, smo9, smo2, smo4, smo3, smo1, exit_osn, exit_rez, create]
    smo5.in_act({"id": None, "created": 0.0})
    smo7.in_act({"id": None, "created": 0.0})
    parts = {"smo": {1: smo1, 2: smo2, 3: smo3, 4: smo4, 5: smo5, 6: smo6, 7: smo7, 8: smo8, 9: smo9},
             "create": create, "exit_osn": exit_osn, "exit_rez": exit_rez,
             "route_failure": route_failure, "route_interrupted": route_interrupted}
    return Model(elements), parts
