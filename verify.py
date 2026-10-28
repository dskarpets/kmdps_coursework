import random

from classes.model import Model
from main import run
from network import PARAMS, build_model


class TraceModel(Model):
    def __init__(self, elements, parts, t_from, t_to):
        super().__init__(elements)
        self.parts = parts
        self.t_from = t_from
        self.t_to = t_to

    def print_info(self):
        if not (self.t_from <= self.tcurr <= self.t_to):
            return
        s = self.parts

        def tag(channel):
            tr = channel.transaction
            return "-" if tr is None else f"{tr['id']}{'!' if tr.get('interrupted') else ''}"

        main_state = "справн" if s["failure"].n_work else "відн"
        backup_state = ["вимк", "вмик", "ввімк"][s["backup_chain"].phase]
        print(f"t = {self.tcurr:8.3f}  основний: {main_state:6s} резервний: {backup_state:5s} "
              f"D1: {tag(s['main']):4s} черга_рез_вх: {[t['id'] for t in s['front'].queue]}  "
              f"D2: {tag(s['backup']):4s} накопичувач: {[t['id'] for t in s['buffer'].queue]}")


def trace(seed, t_before, t_after):
    random.seed(seed)
    model, parts = build_model()
    t_fail = parts["failure"].tnext
    TraceModel(model.elements, parts, t_fail - t_before, t_fail + t_after).simulate(
        t_fail + t_after + 1, verbose=True, print_result=False)
    return t_fail


def print_trace_examples():
    random.seed(2)
    print("Збій під час передачі (знак ! – перервано; повідомлення 23 було в D1 у момент збою):")
    trace(2, 3, 34)
    for seed in range(1, 200):
        random.seed(seed)
        model, parts = build_model()
        t_fail = parts["failure"].tnext
        model.simulate(t_fail + 40, print_result=False)
        if parts["route_b3"].passed == 0 and parts["exit_backup"].quantity >= 2:
            break
    print("\nЗбій у простої основного каналу:")
    trace(seed, 2, 34)


SCENARIOS = [
    ("A", "базові значення", {}),
    ("B", "без збоїв", {"work": (1e12, 0)}),
    ("C", "без збоїв, надходження 9, передача 7 (детерміновані)",
     {"arrival": (9, 0), "tx": (7, 0), "work": (1e12, 0)}),
    ("D", "надходження 9, передача 7, робота 77, відновлення 23 (детерміновані)",
     {"arrival": (9, 0), "tx": (7, 0), "work": (77, 0), "recovery": (23, 0)}),
    ("E", "відновлення 60±7", {"recovery": (60, 7)}),
    ("F", "безвідмовна робота 100±35", {"work": (100, 35)}),
]


def run_scenario(changes, t_mod=200000.0, seed=11):
    p = dict(PARAMS)
    p.update(changes)
    _, s, r = run(p, t_mod=t_mod, seed=seed)
    inside = s["buffer"].queue_len() + s["front"].queue_len() + int(s["main"].busy) + int(s["backup"].busy)
    r["balance"] = s["create"].quantity == r["delivered"] + inside
    r["refused"] = s["front"].refused + s["buffer"].refused
    r["interrupted_via_main"] = sum(s["exit_main"].interrupted)
    times = [x for x, f in zip(s["exit_backup"].tx_times, s["exit_backup"].interrupted) if f]
    r["min_interrupted"] = min(times) if times else None
    return r


def verification(t_mod=200000.0):
    rows = {}
    print(f"Таблиця верифікації (T_mod = {t_mod:.0f} с, seed = 11):")
    print("  №   ρ2      ρ1      збоїв   λ_f       перерв.   t̄      σ      умови")
    for code, title, changes in SCENARIOS:
        r = run_scenario(changes, t_mod)
        rows[code] = r
        print(f"  {code}   {r['rho2']:.4f}  {r['rho1']:.4f}  {r['failures']:5d}   {r['lam']:.5f}   "
              f"{r['n_int']:6d}   {r['tx_mean']:.3f}  {r['tx_std']:.3f}  {title}")

    a = rows["A"]
    checks = [
        ("B: ρ1 без збоїв = 7/9", f"{7 / 9:.4f}", f"{rows['B']['rho1']:.4f}", abs(rows["B"]["rho1"] - 7 / 9) < 0.005),
        ("B: середній час передачі unif(4,10)", "7.000", f"{rows['B']['tx_mean']:.3f}", abs(rows["B"]["tx_mean"] - 7) < 0.05),
        ("B: σ часу передачі unif(4,10)", f"{6 / 12 ** 0.5:.3f}", f"{rows['B']['tx_std']:.3f}", abs(rows["B"]["tx_std"] - 6 / 12 ** 0.5) < 0.03),
        ("B: збоїв і завантаження резервного", "0 і 0", f"{rows['B']['failures']} і {rows['B']['rho2']:.1f}", rows["B"]["failures"] == 0 and rows["B"]["rho2"] == 0),
        ("C: ρ1 у детермінованому режимі", f"{7 / 9:.4f}", f"{rows['C']['rho1']:.4f}", abs(rows["C"]["rho1"] - 7 / 9) < 0.002),
        ("C: σ часу передачі", "0", f"{rows['C']['tx_std']:.3f}", rows["C"]["tx_std"] < 1e-9),
        ("D: λ_f при циклі збою 77 + 23 = 100 с", "0.01000", f"{rows['D']['lam']:.5f}", abs(rows["D"]["lam"] - 0.01) < 1e-4),
        ("A: λ_f = 1/(200 + 23)", f"{1 / 223:.5f}", f"{a['lam']:.5f}", abs(a["lam"] - 1 / 223) < 2e-4),
        ("E: ρ2 зростає при довшому відновленні", f"> {a['rho2']:.4f}", f"{rows['E']['rho2']:.4f}", rows["E"]["rho2"] > a["rho2"]),
        ("F: ρ2 і λ_f зростають при частіших збоях", f"> {a['rho2']:.4f}; > {a['lam']:.5f}",
         f"{rows['F']['rho2']:.4f}; {rows['F']['lam']:.5f}", rows["F"]["rho2"] > a["rho2"] and rows["F"]["lam"] > a["lam"]),
        ("Баланс: надійшло = передано + у системі", "так", "так" if all(r["balance"] for r in rows.values()) else "ні",
         all(r["balance"] for r in rows.values())),
        ("Відмов черги max = 1", "0", str(sum(r["refused"] for r in rows.values())), all(r["refused"] == 0 for r in rows.values())),
        ("Перервані повідомлення, що вийшли через N1", "0", str(sum(r["interrupted_via_main"] for r in rows.values())),
         all(r["interrupted_via_main"] == 0 for r in rows.values())),
        ("A: мінімальний час перерваного (2 + 4 с)", "> 6", f"{a['min_interrupted']:.2f}", a["min_interrupted"] > 6.0),
    ]
    print("\nПеревірка за очікуваними значеннями:")
    for text, expected, got, ok in checks:
        print(f"  {'ок ' if ok else 'ПОМИЛКА'}  {text}: очікується {expected}, отримано {got}")
    passed = all(c[3] for c in checks)
    print("Верифікацію пройдено" if passed else "Верифікацію НЕ пройдено")
    return passed


if __name__ == "__main__":
    print_trace_examples()
    print()
    verification()
