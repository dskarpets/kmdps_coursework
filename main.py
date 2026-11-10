import random
import statistics as st
from network import build_model, PARAMS


def collect_results(model, parts):
    t = model.observed_time()
    tx = parts["exit_osn"].tx_times + parts["exit_rez"].tx_times
    return {
        "time": t,
        "rho_rez": parts["smo"][4].busy_time / t,
        "rho_osn": parts["smo"][2].busy_time / t,
        "failures": parts["route_failure"].passed,
        "lam": parts["route_failure"].passed / t,
        "n_int": parts["route_interrupted"].passed,
        "delivered": len(tx),
        "rez_share": len(parts["exit_rez"].tx_times) / len(tx),
        "tx_mean": st.mean(tx),
        "tx_std": st.stdev(tx),
    }


def run(p=PARAMS, t_mod=100000.0, warmup=0.0, seed=None):
    if seed is not None:
        random.seed(seed)
    model, parts = build_model(p)
    model.simulate(t_mod, warmup=warmup, print_result=False)
    return collect_results(model, parts), parts


def print_report(r):
    print(f"Передано повідомлень: {r['delivered']}")
    print(f"Завантаження резервного каналу: {r['rho_rez']:.4f}")
    print(f"Збоїв: {r['failures']}, частота: {r['lam']:.5f} 1/с")
    print(f"Перерваних повідомлень: {r['n_int']}")
    print(f"Частка повідомлень, переданих резервним каналом: {r['rez_share']:.3f}")
    print(f"Час передачі: середнє {r['tx_mean']:.3f}, σ {r['tx_std']:.3f}")


if __name__ == "__main__":
    r, _ = run()
    print_report(r)
