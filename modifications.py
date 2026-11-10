from experiments import N_REP, confidence_interval, replicate
from network import PARAMS

MODIFICATIONS = [
    ("Базовий", {}),
    ("Вмикання 0.5 с", {"switch": 0.5}),
    ("Відновлення 15±7 с", {"recovery": (15, 7)}),
    ("Безвідмовна робота 300±35 с", {"work": (300, 35)}),
    ("Вмикання 0.5 с + відновлення 15±7 с", {"switch": 0.5, "recovery": (15, 7)}),
    ("Вмикання 0.5 с + безвідмовна робота 300±35 с", {"switch": 0.5, "work": (300, 35)}),
]


def modifications(n_rep=N_REP):
    print(f"Пробні запуски модифікацій ({n_rep} повторів, T_mod = 110000 с, перші 2000 с відкинуто):")
    print("Модифікація | ρ_рез | N_перерваних | t̄, с | σ, с | частка > 10 с | t̄ перерваних, с")
    for name, changes in MODIFICATIONS:
        data = replicate(n_rep, p={**PARAMS, **changes})
        cells = []
        for key, digits in (("rho_rez", 4), ("n_int", 1), ("tx", 3), ("sigma", 3)):
            mean, half = confidence_interval(data[key])
            cells.append(f"{mean:.{digits}f} ± {half:.{digits}f}")
        share = sum(data["over10"]) / len(data["over10"])
        mean, half = confidence_interval(data["tx_int"])
        cells.append(f"{share:.2%}")
        cells.append(f"{mean:.2f} ± {half:.2f}")
        print(f"{name} | " + " | ".join(cells))


if __name__ == "__main__":
    modifications()
