import random

from classes.model import Model
from classes.process import FREE, BLOCKED
from main import run
from network import PARAMS, build_model


class TraceModel(Model):
    def __init__(self, elements, parts, t_from, t_to):
        super().__init__(elements)
        self.parts = parts
        self.t_from, self.t_to = t_from, t_to
        self.lines = {}

    def print_info(self):
        if not (self.t_from <= self.tcurr <= self.t_to):
            return
        s = self.parts["smo"]

        def tag(smo):
            tr = smo.request[0]
            return "-" if tr is None else f"{tr['id']}{'!' if tr.get('interrupted') else ''}"

        main = "справн" if s[5].k[0] != FREE else "відн"
        if s[9].k[0] == BLOCKED:
            backup = "ввімк"
        elif s[8].k[0] != FREE:
            backup = "вмик"
        else:
            backup = "вимк"
        self.lines[self.tcurr] = (f"t = {self.tcurr:8.3f}  основний: {main:6s} резервний: {backup:5s} "
              f"D2: {tag(s[2]):4s} черга СМО3: {[t['id'] for t in s[3].queue]}  "
              f"D3: {tag(s[3]):4s} D4: {tag(s[4]):4s} черга СМО1: {s[1].queue_len()}")


def trace(seed, t_before, t_after):
    random.seed(seed)
    model, parts = build_model()
    t_fail = parts["smo"][5].end[0]
    tm = TraceModel(model.elements, parts, t_fail - t_before, t_fail + t_after)
    tm.simulate(t_fail + t_after + 1, verbose=True, print_result=False)
    for t in sorted(tm.lines):
        print(tm.lines[t])


def find_seed(interrupted):
    start = random.SystemRandom().randrange(10 ** 6)
    for seed in range(start, start + 1000):
        random.seed(seed)
        model, parts = build_model()
        t_fail = parts["smo"][5].end[0]
        model.simulate(t_fail + 40, print_result=False)
        hit = parts["route_interrupted"].passed > 0
        if hit == interrupted and (interrupted or parts["exit_rez"].quantity >= 2):
            return seed


def print_trace_examples():
    seed = find_seed(True)
    print(f"Збій під час передачі (! – перервано), seed = {seed}:")
    trace(seed, 3, 34)
    seed = find_seed(False)
    print(f"\nЗбій у простої основного каналу, seed = {seed}:")
    trace(seed, 2, 34)
    random.seed()


SCENARIOS = [
    (1, (9, 4, 7, 3, 200, 35, 23, 7), "базові значення", {}),
    (2, None, "без збоїв", {"work": (1e12, 0)}),
    (3, None, "без збоїв, детерміновані", {"arrival": (9, 0), "tx": (7, 0), "work": (1e12, 0)}),
    (4, None, "детерміновані, робота 77, відновлення 23",
     {"arrival": (9, 0), "tx": (7, 0), "work": (77, 0), "recovery": (23, 0)}),
    (5, None, "відновлення 60±7", {"recovery": (60, 7)}),
    (6, None, "робота 100±35", {"work": (100, 35)}),
]


def run_scenario(changes, t_mod=200000.0, seed=None):
    p = dict(PARAMS)
    p.update(changes)
    r, s = run(p, t_mod=t_mod, seed=seed)
    sm = s["smo"]
    inside = sum(sm[i].queue_len() + sum(1 for x in sm[i].k if x != FREE) for i in (1, 2, 3, 4))
    r["balance"] = s["create"].quantity == r["delivered"] + inside
    r["refused"] = sm[1].refused + sm[3].refused
    r["int_via_main"] = sum(s["exit_osn"].interrupted)
    times = [x for x, f in zip(s["exit_rez"].tx_times, s["exit_rez"].interrupted) if f]
    r["min_int"] = min(times) if times else None
    return r


def verification(t_mod=200000.0):
    rows = {}
    print("№  t_надх  t_пер  t_справн  t_відн    ρ_осн   ρ_рез  збоїв  λ_f       перерв.  t̄      σ")
    for num, _, title, ch in SCENARIOS:
        p = dict(PARAMS); p.update(ch)
        r = run_scenario(ch, t_mod)
        rows[num] = r
        f = lambda v: f"{v[0]:g}±{v[1]:g}" if v[1] else f"{v[0]:g}"
        print(f"{num}  {f(p['arrival']):6s}  {f(p['tx']):5s}  {f(p['work']):8s}  {f(p['recovery']):7s}  "
              f"{r['rho_osn']:.4f}  {r['rho_rez']:.4f}  {r['failures']:5d}  {r['lam']:.5f}   {r['n_int']:6d}   "
              f"{r['tx_mean']:.3f}  {r['tx_std']:.3f}")
    a = rows[1]
    checks = [
        abs(rows[2]["rho_osn"] - 7 / 9) < 0.005,
        abs(rows[2]["tx_mean"] - 7) < 0.05,
        abs(rows[2]["tx_std"] - 6 / 12 ** 0.5) < 0.03,
        rows[2]["failures"] == 0 and rows[2]["rho_rez"] == 0,
        abs(rows[3]["rho_osn"] - 7 / 9) < 0.002,
        rows[3]["tx_std"] < 1e-9,
        abs(rows[4]["lam"] - 0.01) < 1e-4,
        abs(a["lam"] - 1 / 223) < 2e-4,
        rows[5]["rho_rez"] > a["rho_rez"],
        rows[6]["rho_rez"] > a["rho_rez"] and rows[6]["lam"] > a["lam"],
        all(r["balance"] for r in rows.values()),
        all(r["refused"] == 0 for r in rows.values()),
        all(r["int_via_main"] == 0 for r in rows.values()),
        a["min_int"] > 6.0,
    ]
    print(f"Перевірки: виконано {sum(checks)} з {len(checks)}")
    return all(checks)


if __name__ == "__main__":
    print_trace_examples()
    print()
    verification()
