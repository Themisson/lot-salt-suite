#!/usr/bin/env python3
"""Generate a minimal HTML report for modern LOT/PKN outputs.

This script consumes only outputs produced by the modern `lot-sim run --mode lot-pkn`
pipeline. It does not read legacy files and does not perform legacy regression.
"""
from __future__ import annotations

import argparse
import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


REPORT_LABEL = "Modern synthetic LOT/PKN output - no legacy regression"
REPORT_NOTICE = (
    "This report uses modern synthetic LOT/PKN outputs only. "
    "No numerical regression against legacy was performed."
)

REQUIRED_COLUMNS = (
    "time_s",
    "injected_volume_m3",
    "fracture_length_m",
    "fracture_width_m",
    "fracture_volume_m3",
    "leakoff_volume_m3",
    "net_pressure_Pa",
)

PLOTS = (
    ("pressure_vs_time.png", "time_s", "net_pressure_Pa", "Time (s)", "Net pressure (Pa)"),
    (
        "pressure_vs_volume.png",
        "injected_volume_m3",
        "net_pressure_Pa",
        "Injected volume (m3)",
        "Net pressure (Pa)",
    ),
    (
        "length_vs_time.png",
        "time_s",
        "fracture_length_m",
        "Time (s)",
        "Fracture length (m)",
    ),
    (
        "width_vs_time.png",
        "time_s",
        "fracture_width_m",
        "Time (s)",
        "Fracture width (m)",
    ),
    (
        "leakoff_vs_time.png",
        "time_s",
        "leakoff_volume_m3",
        "Time (s)",
        "Leakoff volume (m3)",
    ),
)


def resolve_inputs(run_dir: Path | None, input_csv: Path | None, summary_json: Path | None) -> tuple[Path, Path]:
    """Resolve input paths from either --run-dir or explicit --input/--summary."""
    if run_dir is not None:
        if input_csv is not None or summary_json is not None:
            raise ValueError("Use either --run-dir or --input/--summary, not both.")
        return run_dir / "timeseries.csv", run_dir / "result.json"
    if input_csv is None or summary_json is None:
        raise ValueError("Provide --run-dir or both --input and --summary.")
    return input_csv, summary_json


def load_timeseries(path: Path) -> pd.DataFrame:
    """Load and validate the LOT/PKN timeseries CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Timeseries CSV not found: {path}")
    frame = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Timeseries CSV is missing required column(s): {', '.join(missing)}")
    if frame.empty:
        raise ValueError("Timeseries CSV has no rows.")
    numeric = frame.loc[:, REQUIRED_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ValueError("Timeseries CSV contains non-numeric or NaN values.")
    finite_mask = numeric.map(math.isfinite)
    if not finite_mask.all().all():
        raise ValueError("Timeseries CSV contains Inf or non-finite values.")
    return numeric


def load_summary(path: Path) -> dict[str, Any]:
    """Load and validate the JSON summary."""
    if not path.exists():
        raise FileNotFoundError(f"Summary JSON not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Summary JSON must contain an object at the top level.")
    summary = data.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("Summary JSON is missing object field: summary")
    for key, value in summary.items():
        if isinstance(value, (int, float)) and not math.isfinite(float(value)):
            raise ValueError(f"Summary JSON contains non-finite value in summary.{key}")
    return data


def plot_timeseries(frame: pd.DataFrame, output_dir: Path) -> list[str]:
    """Create the required PNG plots and return their filenames."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for filename, x_column, y_column, x_label, y_label in PLOTS:
        fig, ax = plt.subplots(figsize=(8.0, 4.8), dpi=140)
        ax.plot(frame[x_column], frame[y_column], color="#1f6f6b", linewidth=2.0)
        ax.set_title(REPORT_LABEL)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, color="#d7d0c4", linewidth=0.8, alpha=0.8)
        fig.tight_layout()
        fig.savefig(output_dir / filename)
        plt.close(fig)
        written.append(filename)
    return written


def final_values(frame: pd.DataFrame) -> dict[str, float]:
    """Return the final row values from the timeseries."""
    row = frame.iloc[-1]
    return {column: float(row[column]) for column in REQUIRED_COLUMNS}


def write_html_report(
    output_dir: Path,
    summary_data: dict[str, Any],
    frame: pd.DataFrame,
    plot_filenames: list[str],
) -> Path:
    """Write report.html with summary values, final values, plots, and limitations."""
    metadata = summary_data.get("metadata", {})
    summary = summary_data.get("summary", {})
    case_id = str(metadata.get("case_id", "lot-pkn-modern-run"))
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    finals = final_values(frame)

    def rows(values: dict[str, Any]) -> str:
        rendered = []
        for key, value in values.items():
            rendered.append(
                "<tr>"
                f"<th>{html.escape(str(key))}</th>"
                f"<td>{html.escape(format_value(value))}</td>"
                "</tr>"
            )
        return "\n".join(rendered)

    images = "\n".join(
        f'<figure><img src="{html.escape(name)}" alt="{html.escape(name)}">'
        f"<figcaption>{html.escape(name)}</figcaption></figure>"
        for name in plot_filenames
    )

    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(case_id)} - LOT/PKN report</title>
<style>
  body {{
    margin: 0;
    font-family: Arial, sans-serif;
    color: #211b14;
    background: #f7f3ec;
    line-height: 1.55;
  }}
  main {{ max-width: 1080px; margin: 0 auto; padding: 32px 24px 56px; }}
  h1 {{ margin: 0 0 8px; font-size: 30px; }}
  h2 {{ margin-top: 32px; font-size: 20px; color: #1f6f6b; }}
  .label {{ color: #b4632c; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }}
  .notice {{ padding: 14px 18px; border-left: 4px solid #9a5b1f; background: #f8efe2; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; margin-top: 12px; }}
  th, td {{ text-align: left; border-bottom: 1px solid #e4dccf; padding: 8px 10px; }}
  th {{ width: 38%; color: #4a4239; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
  figure {{ margin: 0; padding: 12px; background: #fff; border: 1px solid #e4dccf; }}
  img {{ max-width: 100%; display: block; }}
  figcaption {{ margin-top: 8px; font-size: 13px; color: #4a4239; }}
</style>
</head>
<body>
<main>
  <div class="label">{html.escape(REPORT_LABEL)}</div>
  <h1>{html.escape(case_id)}</h1>
  <p>Generated at {html.escape(generated_at)}</p>
  <p class="notice">{html.escape(REPORT_NOTICE)}</p>

  <h2>Summary From result.json</h2>
  <table>
    <tbody>
{rows(summary)}
    </tbody>
  </table>

  <h2>Final Values From timeseries.csv</h2>
  <table>
    <tbody>
{rows(finals)}
    </tbody>
  </table>

  <h2>Plots</h2>
  <div class="grid">
{images}
  </div>

  <h2>Limitations</h2>
  <ul>
    <li>No numerical regression against legacy was performed.</li>
    <li>No damage model is included.</li>
    <li>No coupling with salt creep is included.</li>
    <li>R09 is mitigated only for the audited PKN cases.</li>
    <li>R09 still blocks regressions involving idQ == 4.</li>
  </ul>
</main>
</body>
</html>
"""
    path = output_dir / "report.html"
    path.write_text(document, encoding="utf-8")
    return path


def format_value(value: Any) -> str:
    """Format scalar values for HTML tables."""
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def generate_report(input_csv: Path, summary_json: Path, output_dir: Path) -> list[Path]:
    """Generate PNG plots and report.html for one LOT/PKN run."""
    frame = load_timeseries(input_csv)
    summary_data = load_summary(summary_json)
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_filenames = plot_timeseries(frame, output_dir)
    report_path = write_html_report(output_dir, summary_data, frame, plot_filenames)
    return [output_dir / name for name in plot_filenames] + [report_path]


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Generate modern LOT/PKN plots and HTML report")
    parser.add_argument("--run-dir", type=Path, help="Directory containing timeseries.csv and result.json")
    parser.add_argument("--input", dest="input_csv", type=Path, help="Path to timeseries.csv")
    parser.add_argument("--summary", dest="summary_json", type=Path, help="Path to result.json")
    parser.add_argument("--output", required=True, type=Path, help="Output directory for PNGs and report.html")
    return parser


def main() -> int:
    """Command-line entry point."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        input_csv, summary_json = resolve_inputs(args.run_dir, args.input_csv, args.summary_json)
        generated = generate_report(input_csv, summary_json, args.output)
    except Exception as exc:
        parser.exit(2, f"lot_pkn_report: error: {exc}\n")
    for path in generated:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
