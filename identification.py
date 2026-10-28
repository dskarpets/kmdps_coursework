import os
import random

import numpy as np
from scipy import stats

from network import PARAMS, build_model

TARGET_ID = 300
GRID = 0.001


def sample_one(seed):
    random.seed(seed)
    model, parts = build_model()
    t = 3500.0
    while True:
        model.simulate(t, print_result=False)
        for d in (parts["exit_main"], parts["exit_backup"]):
            if TARGET_ID in d.ids:
                k = d.ids.index(TARGET_ID)
                return d.tx_times[k], d.interrupted[k]
        t += 200.0


def collect_sample(n_runs, seed0):
    pairs = [sample_one(seed0 + k) for k in range(n_runs)]
    return np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs], dtype=bool)


def uniform_cdf(a, b):
    return lambda x: np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0.0, 1.0)


def interrupted_distribution():
    a, b = PARAMS["tx"][0] - PARAMS["tx"][1], PARAMS["tx"][0] + PARAMS["tx"][1]
    xs = np.arange(0.0, b, GRID) + GRID / 2
    fe = np.where(xs < a, 1.0, (b - xs) / (b - a)) / ((a + b) / 2)
    ks = np.arange(a, b, GRID) + GRID / 2
    dens = np.convolve(fe, np.full(ks.shape, 1.0 / (b - a))) * GRID
    grid = np.arange(len(dens)) * GRID + (xs[0] + ks[0]) + PARAMS["switch"]
    cdf_vals = np.cumsum(dens) * GRID
    cdf_vals /= cdf_vals[-1]
    return grid, dens, (lambda x: np.interp(x, grid, cdf_vals, left=0.0, right=1.0))


def mixture_cdf(p_int, a, b, g_cdf):
    uniform = uniform_cdf(a, b)
    return lambda x: (1 - p_int) * uniform(x) + p_int * g_cdf(x)


def chi2_test(sample, cdf, lo, hi, k, n_params):
    edges = [-np.inf]
    for j in range(1, k):
        left, right = lo, hi
        for _ in range(60):
            mid = 0.5 * (left + right)
            left, right = (mid, right) if cdf(mid) < j / k else (left, mid)
        edges.append(0.5 * (left + right))
    edges.append(np.inf)
    edges = np.array(edges)
    observed, _ = np.histogram(sample, bins=edges)
    finite = np.where(np.isinf(edges), 0.0, edges)
    cdf_edges = np.where(np.isinf(edges), (edges > 0).astype(float), cdf(finite))
    expected = len(sample) * np.diff(cdf_edges)
    chi2 = float(((observed - expected) ** 2 / expected).sum())
    df = k - 1 - n_params
    return chi2, df, float(stats.chi2.ppf(0.95, df))


def sturges(n):
    return int(1 + 3.322 * np.log10(n))


def plot_histogram(x, p_int, a, b, grid, dens, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = np.linspace(3, 23, 2000)
    pdf = (1 - p_int) * np.where((t >= a) & (t <= b), 1.0 / (b - a), 0.0) \
        + p_int * np.interp(t, grid, dens, left=0, right=0)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.hist(x, bins=sturges(len(x)) * 2, density=True, alpha=0.6, label="спостереження")
    ax.plot(t, pdf, linewidth=2, label="теоретична суміш")
    ax.set_xlabel("час передачі, с")
    ax.set_ylabel("щільність")
    ax.legend()
    fig.tight_layout()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def verdict(chi2, critical):
    return "відхиляється" if chi2 >= critical else "не відхиляється"


def identify(n_runs=8000, seed0=100000, plot_path="results/histogram_tx.png"):
    x, interrupted = collect_sample(n_runs, seed0)
    a, b = PARAMS["tx"][0] - PARAMS["tx"][1], PARAMS["tx"][0] + PARAMS["tx"][1]
    k = sturges(len(x))
    print(f"Масив: {len(x)} значень (по одному з кожного запуску), середнє {x.mean():.3f} с, σ {x.std(ddof=1):.3f} с")

    a_hat, b_hat = x.mean() - 3 ** 0.5 * x.std(ddof=1), x.mean() + 3 ** 0.5 * x.std(ddof=1)
    chi2, df, crit = chi2_test(x, uniform_cdf(a_hat, b_hat), a_hat - 1, b_hat + 1, k, 2)
    print(f"Гіпотеза 1, рівномірний закон ({a_hat:.2f}; {b_hat:.2f}): "
          f"χ² = {chi2:.1f}, критичне {crit:.1f} (k = {k}, ступенів вільності {df}), {verdict(chi2, crit)}")

    p_int = float(interrupted.mean())
    grid, dens, g_cdf = interrupted_distribution()
    chi2, df, crit = chi2_test(x, mixture_cdf(p_int, a, b, g_cdf), 3.0, 25.0, k, 1)
    print(f"Гіпотеза 2, суміш (частка перерваних {p_int:.3f}, unif({a:.0f}; {b:.0f})): "
          f"χ² = {chi2:.1f}, критичне {crit:.1f} (k = {k}, ступенів вільності {df}), {verdict(chi2, crit)}")

    plot_histogram(x, p_int, a, b, grid, dens, plot_path)


if __name__ == "__main__":
    identify()
