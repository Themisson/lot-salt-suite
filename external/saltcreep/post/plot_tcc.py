"""
Plota curvas de fechamento de poço para os casos TCC A-F.
Compara o novo solver com o oracle (SESTSAL output, se disponível).

Uso:
    python post/plot_tcc.py                      # plota todos os casos
    python post/plot_tcc.py results/modelo_A     # plota só o caso A
"""
from __future__ import annotations
import sys
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

CASES = ["modelo_A", "modelo_B", "modelo_C", "modelo_D", "modelo_E", "modelo_F"]
LABELS = {
    "modelo_A": "A — Halita, k₀=1.0, 9.6 ppg",
    "modelo_B": "B — Halita, k₀=1.2, 9.6 ppg",
    "modelo_C": "C — H+T+H, k₀=1.0, 16 ppg",
    "modelo_D": "D — H+T+H, k₀=1.2, 16 ppg",
    "modelo_E": "E — H+T+H, k₀=1.0, 18 ppg",
    "modelo_F": "F — H+T+H, k₀=1.2, 18 ppg",
}
RESULTS_DIR = pathlib.Path("results")
ORACLE_DIR  = pathlib.Path("results/oracle")


def load_closure(case_dir: pathlib.Path) -> pd.DataFrame | None:
    csv = case_dir / "closure.csv"
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    return df


def plot_case(ax: plt.Axes, case: str) -> None:
    df = load_closure(RESULTS_DIR / case)
    if df is not None:
        ax.plot(df["t_h"], df["closure_pct"], label="saltcreep (novo)", lw=2)
    else:
        ax.text(0.5, 0.5, "Sem resultados", ha="center", transform=ax.transAxes)

    # oracle
    oracle_csv = ORACLE_DIR / f"{case}.csv"
    if oracle_csv.exists():
        dfo = pd.read_csv(oracle_csv)
        ax.plot(dfo["t_h"], dfo["closure_pct"],
                "k--", label="SESTSAL (oracle)", lw=1.5)

    ax.set_title(LABELS.get(case, case), fontsize=9)
    ax.set_xlabel("Tempo (h)")
    ax.set_ylabel("Fechamento (%)")
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=1))
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)


def main() -> None:
    if len(sys.argv) > 1:
        cases_to_plot = [pathlib.Path(sys.argv[1]).name]
    else:
        cases_to_plot = CASES

    n = len(cases_to_plot)
    ncols = min(3, n)
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 4 * nrows),
                              squeeze=False)
    axes_flat = [axes[r][c] for r in range(nrows) for c in range(ncols)]

    for i, case in enumerate(cases_to_plot):
        plot_case(axes_flat[i], case)

    # hide unused axes
    for j in range(len(cases_to_plot), len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle("Fechamento de poço em rocha salina — TCC (comparação A–F)",
                  fontsize=12, fontweight="bold")
    fig.tight_layout()
    out = pathlib.Path("results") / "tcc_comparison.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"Salvo em {out}")
    plt.show()


if __name__ == "__main__":
    main()
