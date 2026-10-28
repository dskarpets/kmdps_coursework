import random
import statistics

from scipy import stats

from main import run
from network import PARAMS, build_model

T_MOD = 110000.0
WARMUP = 2000.0
N_REP = 20
EPS = 0.05

RESPONSES = {
    "rho2": "завантаження резервного ρ2",
    "lam": "частота відмов λ_f, 1/с",
    "nint": "інтенсивність перерваних N_int/T, 1/с",
    "tx": "середній час передачі, с",
}


def snapshot(model, parts):
    t = model.tcurr
    tx = parts["exit_main"].tx_times + parts["exit_backup"].tx_times
    return {
        "rho2": parts["backup"].busy_time / t,
        "lam": parts["failure"].failures / t,
        "nint": parts["route_b3"].passed / t,
        "tx": sum(tx) / len(tx),
    }


def pilot_run(seed, horizon, step):
    random.seed(seed)
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


def transient_study(horizon=200000.0, step=500.0, seeds=(201, 202, 203, 204)):
    histories = [pilot_run(s, horizon, step) for s in seeds]
    final = {n: statistics.mean(h[-1][1][n] for h in histories) for n in RESPONSES}
    eps = {n: EPS * final[n] for n in RESPONSES}
    periods = transient_period(histories, eps)
    print(f"Перехідний період ({len(seeds)} спостереження, ε = {EPS:.0%} від середнього):")
    for n, label in RESPONSES.items():
        value = "не досягнуто" if periods[n] is None else f"{periods[n]:.0f} с"
        print(f"  {label}: ε = {eps[n]:.5f}, T = {value}")
    return periods


def replicate(n, seed0, t_mod=T_MOD, warmup=WARMUP):
    out = {"rho2": [], "lam": [], "nint": [], "n_int": [], "tx": [], "sigma": []}
    for k in range(n):
        _, _, r = run(PARAMS, t_mod=t_mod, warmup=warmup, seed=seed0 + k)
        out["rho2"].append(r["rho2"])
        out["lam"].append(r["lam"])
        out["nint"].append(r["n_int"] / r["time"])
        out["n_int"].append(r["n_int"])
        out["tx"].append(r["tx_mean"])
        out["sigma"].append(r["tx_std"])
    return out


def replication_study(n_pilot=40, seed0=7000):
    pilot = replicate(n_pilot, seed0)
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


def baseline(n_rep=N_REP, seed0=1000):
    data = replicate(n_rep, seed0)
    rows = [
        ("Завантаження резервного каналу ρ2", "rho2", 4),
        ("Частота відмов λ_f, збоїв/с", "lam", 5),
        (f"Число перерваних повідомлень за {T_MOD - WARMUP:.0f} с", "n_int", 1),
        ("Середній час передачі, с", "tx", 3),
        ("Середнє квадратичне відхилення часу передачі, с", "sigma", 3),
    ]
    print(f"Оцінки ({n_rep} повторів, T_mod = {T_MOD:.0f} с, перші {WARMUP:.0f} с відкинуто):")
    for label, key, digits in rows:
        mean, half = confidence_interval(data[key])
        print(f"  {label}: {mean:.{digits}f} ± {half:.{digits}f}")
    return data
