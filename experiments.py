import statistics
from scipy import stats
from main import run
from network import PARAMS, build_model

T_MOD = 110000.0
WARMUP = 2000.0
N_REP = 20
EPS = 0.05

RESPONSES = {
    "rho_rez": "завантаження резервного ρ",
    "lam": "частота відмов λ_f, 1/с",
    "nint": "інтенсивність перерваних N_int/T, 1/с",
    "tx": "середній час передачі, с",
}


def snapshot(model, parts):
    t = model.tcurr
    tx = parts["exit_osn"].tx_times + parts["exit_rez"].tx_times
    return {
        "rho_rez": parts["smo"][4].busy_time / t,
        "lam": parts["route_failure"].passed / t,
        "nint": parts["route_interrupted"].passed / t,
        "tx": sum(tx) / len(tx),
    }


def pilot_run(horizon, step):
    model, parts = build_model()
    history = []
    t = step
    while t <= horizon:
        model.simulate(t, print_result=False)
        history.append((t, snapshot(model, parts)))
        t += step
    return history


def transient_period(histories, eps):
    result = {}
    for name in RESPONSES:
        found = None
        for k in range(len(histories[0]) - 1, -1, -1):
            values = [h[k][1][name] for h in histories]
            if max(values) - min(values) >= eps[name]:
                break
            found = histories[0][k][0]
        result[name] = found
    return result


def transient_study(horizon=200000.0, step=500.0, n_runs=4):
    histories = [pilot_run(horizon, step) for _ in range(n_runs)]
    final = {n: statistics.mean(h[-1][1][n] for h in histories) for n in RESPONSES}
    eps = {n: EPS * final[n] for n in RESPONSES}
    periods = transient_period(histories, eps)
    print(f"Перехідний період ({n_runs} спостереження, ε = {EPS:.0%} від середнього):")
    for n, label in RESPONSES.items():
        value = "не досягнуто" if periods[n] is None else f"{periods[n]:.0f} с"
        print(f"  {label}: ε = {eps[n]:.5f}, T = {value}")
    return periods


def bias_study(n_runs=300, horizon=10000.0, window=1000.0):
    names = ["rho_rez", "lam", "nint", "tx"]
    sums = {n: [0.0] * int(horizon / window) for n in names}
    for _ in range(n_runs):
        model, parts = build_model()
        prev = {"busy": 0.0, "fail": 0, "int": 0, "k1": 0, "k2": 0}
        for w in range(int(horizon / window)):
            model.simulate((w + 1) * window, print_result=False)
            new_tx = parts["exit_osn"].tx_times[prev["k1"]:] + parts["exit_rez"].tx_times[prev["k2"]:]
            busy = parts["smo"][4].busy_time
            fail = parts["route_failure"].passed
            inter = parts["route_interrupted"].passed
            sums["rho_rez"][w] += (busy - prev["busy"]) / window
            sums["lam"][w] += (fail - prev["fail"]) / window
            sums["nint"][w] += (inter - prev["int"]) / window
            sums["tx"][w] += sum(new_tx) / max(len(new_tx), 1)
            prev = {"busy": busy, "fail": fail, "int": inter,
                    "k1": len(parts["exit_osn"].tx_times), "k2": len(parts["exit_rez"].tx_times)}
    print(f"Зміщення через початковий стан ({n_runs} запусків, вікна по {window:.0f} с):")
    for n, label in RESPONSES.items():
        means = [s / n_runs for s in sums[n]]
        rest = means[1:]
        print(f"  {label}: перше вікно {means[0]:.5f}, вікна 2–{len(means)}: від {min(rest):.5f} до {max(rest):.5f}")


def replicate(n, t_mod=T_MOD, warmup=WARMUP, p=PARAMS):
    out = {"rho_rez": [], "lam": [], "nint": [], "n_int": [], "failures": [], "tx": [], "sigma": [],
           "over10": [], "tx_int": []}
    for k in range(n):
        r, parts = run(p, t_mod=t_mod, warmup=warmup)
        tx = parts["exit_osn"].tx_times + parts["exit_rez"].tx_times
        flags = parts["exit_osn"].interrupted + parts["exit_rez"].interrupted
        interrupted = [x for x, f in zip(tx, flags) if f]
        out["rho_rez"].append(r["rho_rez"])
        out["lam"].append(r["lam"])
        out["nint"].append(r["n_int"] / r["time"])
        out["n_int"].append(r["n_int"])
        out["failures"].append(r["failures"])
        out["tx"].append(r["tx_mean"])
        out["sigma"].append(r["tx_std"])
        out["over10"].append(sum(x > 10 for x in tx) / len(tx))
        out["tx_int"].append(statistics.mean(interrupted))
    return out


def replication_study(n_pilot=40):
    pilot = replicate(n_pilot)
    print(f"Кількість повторів (пілот {n_pilot} запусків, T_mod = {T_MOD:.0f} с, ε = {EPS:.0%}):")
    needed = []
    for name, label in RESPONSES.items():
        mean = statistics.mean(pilot[name])
        n = 20.0 * (statistics.stdev(pilot[name]) / (EPS * mean)) ** 2
        needed.append(n)
        print(f"  {label}: середнє {mean:.5f}, n = {n:.1f}")
    print(f"Потрібно щонайменше {max(needed):.0f} повторів; приймаємо N = {N_REP}")


def confidence_interval(values, p=0.95):
    mean = statistics.mean(values)
    half = stats.t.ppf((1 + p) / 2, len(values) - 1) * statistics.stdev(values) / len(values) ** 0.5
    return mean, half


def baseline(n_rep=N_REP):
    data = replicate(n_rep)
    rows = [
        ("Завантаження резервного каналу ρ", "rho_rez", 4),
        ("Частота відмов λ_f, збоїв/с", "lam", 5),
        (f"Число збоїв за {T_MOD - WARMUP:.0f} с", "failures", 1),
        (f"Число перерваних повідомлень за {T_MOD - WARMUP:.0f} с", "n_int", 1),
        ("Середній час передачі, с", "tx", 3),
        ("Середнє квадратичне відхилення часу передачі, с", "sigma", 3),
        ("Частка передач довше 10 с", "over10", 4),
        ("Середній час перерваних повідомлень, с", "tx_int", 2),
    ]
    print(f"Оцінки ({n_rep} повторів, T_mod = {T_MOD:.0f} с, перші {WARMUP:.0f} с відкинуто):")
    for label, key, digits in rows:
        mean, half = confidence_interval(data[key])
        print(f"  {label}: {mean:.{digits}f} ± {half:.{digits}f}")
    return data
