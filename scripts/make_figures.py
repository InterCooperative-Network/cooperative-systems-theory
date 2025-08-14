#!/usr/bin/env python3
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- Model ----------

@dataclass
class Params:
    a: float
    b: float
    delta: float
    alpha: float
    beta: float
    g: float
    d: float
    s_pi: float
    p: float
    C0: float
    chi: float
    N_bar: float
    lam: float
    eta: float
    tau: float
    E_cap: float
    theta: float
    kappa: float

def softplus(z: float, kappa: float) -> float:
    t = kappa * z
    if t > 0:
        return (t + math.log1p(math.exp(-t))) / kappa
    else:
        return math.log1p(math.exp(t)) / kappa

def sigma(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def e_max(theta: float, cap: float) -> float:
    # democratic control lowers cap; nonzero floor at 0.05 for continuity
    return max(0.0, cap * (1.0 - theta) + 0.05 * theta)

def step(Q: float, N: float, K: float, prm: Params):
    # controls (interior/binding-ish, smoothed)
    E_cap = e_max(prm.theta, prm.E_cap)
    pressure = prm.g * K
    E_raw = prm.beta * (pressure / max(1.0, pressure))
    E = E_cap * sigma(E_raw / max(E_cap, 1e-12))
    R_floor = prm.alpha * prm.g * K if prm.g > 0 else 0.0
    R = R_floor + max(0.0, 0.05 * pressure)

    # state updates
    Q1 = Q + prm.a * math.sqrt(max(R, 0.0)) * (1.0 - Q) - prm.b * (E**2) / (1.0 + Q) - prm.delta * Q
    U = Q / (1.0 + Q) - (E**2)
    N1 = N * (1.0 + prm.lam * (1.0 - N / prm.N_bar) + prm.eta * (U - prm.tau))

    revenue = (prm.p + E * (1.0 - E / max(E_cap, 1e-12))) * N
    costs = R + prm.C0 + prm.chi / (1.0 + Q)
    Pi = revenue - costs

    K1 = (1.0 - prm.d) * K + prm.s_pi * softplus(Pi, prm.kappa)
    return Q1, N1, K1, E, R, Pi

def simulate(T: int, init: dict[str, float], prm: Params) -> pd.DataFrame:
    Q, N, K = float(init["Q"]), float(init["N"]), float(init["K"])
    rows = []
    for t in range(T + 1):
        rows.append({"t": t, "Q": Q, "N": N, "K": K})
        if t == T:
            break
        Q, N, K, E, R, Pi = step(Q, N, K, prm)
    return pd.DataFrame(rows)

# ---------- Figures ----------

def fig_time_series(df_x: pd.DataFrame, df_c: pd.DataFrame, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    for name, df in (("extractive", df_x), ("coop", df_c)):
        # sanitize data to avoid overflow/NaNs during plotting
        df = df.copy()
        for col in ("Q", "N", "K"):
            s = pd.to_numeric(df[col], errors="coerce").astype(float)
            s = s.replace([np.inf, -np.inf], np.nan)
            df[col] = s

        fig, ax = plt.subplots()
        ax.plot(df["t"], df["Q"], label="Q (quality)")
        ax.plot(df["t"], df["N"], label="N (users)")
        ax.plot(df["t"], df["K"], label="K (capital)")
        # robust y-limits and scale
        yvals = pd.concat([df["Q"], df["N"], df["K"]], ignore_index=True).to_numpy()
        yvals = yvals[np.isfinite(yvals)]
        if yvals.size > 0:
            lo = float(np.nanpercentile(yvals, 1))
            hi = float(np.nanpercentile(yvals, 99))
            if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
                lo = float(np.nanmin(yvals))
                hi = float(np.nanmax(yvals))
            # cap extremes
            hi = min(hi, 1e12)
            lo = max(lo, -1e12)
            if hi == lo:
                hi = lo + 1.0
            ax.set_ylim(lo, hi)
        ax.set_yscale("symlog", linthresh=1.0)
        ax.set_xlabel("t")
        ax.set_ylabel("state")
        ax.set_title(f"Time Series – {name}")
        ax.legend()
        fig.savefig(out / f"time_series_{name}.png", bbox_inches="tight")
        plt.close(fig)

def fig_phase_portrait(prm: Params, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    Q = np.linspace(0.05, 0.95, 25)
    N = np.linspace(1e6, 1e8, 25)
    QQ, NN = np.meshgrid(Q, N)

    def dQ(Q, N):
        # Local field approximation around modest K; enough for a qualitative portrait
        K = 1e9
        E_cap = e_max(prm.theta, prm.E_cap)
        pressure = prm.g * K
        E_raw = prm.beta * (pressure / max(1.0, pressure))
        E = E_cap * 1.0 / (1.0 + np.exp(-(E_raw / max(E_cap, 1e-12))))
        R_floor = prm.alpha * prm.g * K if prm.g > 0 else 0.0
        R = R_floor + max(0.0, 0.05 * pressure)
        return prm.a * np.sqrt(max(R, 0.0)) * (1.0 - Q) - prm.b * (E**2) / (1.0 + Q) - prm.delta * Q

    def dN(Q, N):
        U = Q / (1.0 + Q) - (e_max(prm.theta, prm.E_cap) ** 2)  # coarse E-term
        return N * (prm.lam * (1.0 - N / prm.N_bar) + prm.eta * (U - prm.tau))

    DQ = dQ(QQ, NN)
    DN = dN(QQ, NN)

    fig, ax = plt.subplots()
    ax.streamplot(QQ, NN, DQ, DN, density=1.2)
    ax.set_xlabel("Q")
    ax.set_ylabel("N")
    ax.set_title("Phase Portrait (Q vs N)")
    fig.savefig(out / "phase_portrait.png", bbox_inches="tight")
    plt.close(fig)

def fig_stability_lambdaK(out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    d = 0.05
    s_pi = 0.3
    g_vals = np.linspace(0.0, 0.30, 400)
    lamK = 1.0 - d + s_pi * g_vals
    fig, ax = plt.subplots()
    ax.plot(g_vals, lamK, label=r"$\lambda_K = 1 - d + s_\pi g$")
    ax.axhline(1.0, linestyle="--", linewidth=1)
    ax.axhline(-1.0, linestyle="--", linewidth=1)
    ax.set_xlabel("g (capital growth requirement)")
    ax.set_ylabel("λ_K")
    ax.set_title("Capital Stability (λ_K vs g)")
    ax.legend()
    fig.savefig(out / "stability_lambdaK.png", bbox_inches="tight")
    plt.close(fig)

# ---------- Params ----------

def load_yaml(path: Path) -> tuple[Params, dict[str, float], int]:
    cfg = yaml.safe_load(path.read_text())
    model_raw = cfg["model"]
    model = {k: float(v) for k, v in model_raw.items()}
    prm = Params(**model)
    init_raw = cfg["init"]
    init = {k: float(v) for k, v in init_raw.items()}
    T = int(cfg["sim"]["T"])
    return prm, init, T

def default_cfgs(base: Path):
    base.mkdir(parents=True, exist_ok=True)
    x = base / "params.extractive.yaml"
    c = base / "params.coop.yaml"
    if not x.exists():
        x.write_text("""model:
  a: 0.3
  b: 0.4
  delta: 0.1
  alpha: 0.2
  beta: 0.15
  g: 0.12
  d: 0.05
  s_pi: 0.3
  p: 10.0
  C0: 1.0
  chi: 0.5
  N_bar: 1.0e8
  lam: 0.02
  eta: 5.0
  tau: 0.1
  E_cap: 0.5
  theta: 0.0
  kappa: 10.0
init: { Q: 0.7, N: 2.0e7, K: 1.0e9 }
sim: { T: 300 }
""", encoding="utf-8")
    if not c.exists():
        c.write_text("""model:
  a: 0.3
  b: 0.25
  delta: 0.08
  alpha: 0.25
  beta: 0.03
  g: 0.0
  d: 0.05
  s_pi: 0.0
  p: 8.0
  C0: 1.0
  chi: 0.4
  N_bar: 1.0e8
  lam: 0.02
  eta: 5.0
  tau: 0.08
  E_cap: 0.1
  theta: 0.8
  kappa: 10.0
init: { Q: 0.75, N: 1.0e7, K: 5.0e8 }
sim: { T: 300 }
""", encoding="utf-8")

# ---------- Main ----------

def main():
    repo = Path(__file__).resolve().parents[1]
    examples = repo / "examples"
    figures = repo / "figures"
    default_cfgs(examples)

    prm_x, init_x, T_x = load_yaml(examples / "params.extractive.yaml")
    prm_c, init_c, T_c = load_yaml(examples / "params.coop.yaml")

    df_x = simulate(T_x, init_x, prm_x)
    df_c = simulate(T_c, init_c, prm_c)

    fig_time_series(df_x, df_c, figures)
    fig_phase_portrait(prm_x, figures)  # portrait using extractive-ish params
    fig_stability_lambdaK(figures)

    print("Wrote figures to:", figures.resolve())

if __name__ == "__main__":
    main()
