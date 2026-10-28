import random
import statistics

from network import PARAMS, build_model


def collect_results(model, s):
    t = model.observed_time()
    tx = s["exit_main"].tx_times + s["exit_backup"].tx_times
    return {
        "time": t,
        "rho2": s["backup"].busy_time / t,
        "rho1": s["main"].busy_time / t,
        "failures": s["failure"].failures,
        "lam": s["failure"].failures / t,
        "n_int": s["route_b3"].passed,
        "delivered": len(tx),
        "tx_mean": statistics.mean(tx),
        "tx_std": statistics.stdev(tx),
    }


def run(p=PARAMS, t_mod=100000.0, warmup=0.0, seed=None):
    if seed is not None:
        random.seed(seed)
    model, parts = build_model(p)
    model.simulate(t_mod, warmup=warmup, print_result=False)
    return model, parts, collect_results(model, parts)


def print_report(r):
    print(f"Час спостереження: {r['time']:.0f} с, передано повідомлень: {r['delivered']}")
    print(f"Завантаження резервного каналу: {r['rho2']:.4f}")
    print(f"Частота відмов: {r['lam']:.5f} збоїв/с (збоїв: {r['failures']})")
    print(f"Перервано повідомлень: {r['n_int']}")
    print(f"Час передачі: середнє {r['tx_mean']:.3f} с, σ {r['tx_std']:.3f} с")


if __name__ == "__main__":
    _, _, result = run(t_mod=100000.0, seed=1)
    print_report(result)
