"""Interactive wall displacement viewer for saltcreep results."""

from __future__ import annotations

from pathlib import Path
import argparse
import html
import json

import pandas as pd

from saltpost.io import load_result
from saltpost.units import auto_displacement_unit


def load_wall_profile(result_dir: str | Path) -> tuple[object, pd.DataFrame]:
    result = load_result(result_dir)
    if result.wall_profile is None or result.wall_profile.empty:
        raise SystemExit(f"Nenhum wall_profile.csv encontrado em {result.path}")
    required = {"t_h", "z_m", "u_r_m"}
    missing = required.difference(result.wall_profile.columns)
    if missing:
        raise SystemExit(f"wall_profile.csv sem colunas obrigatorias: {sorted(missing)}")
    return result, result.wall_profile.copy()


def _frames(df: pd.DataFrame) -> list[dict]:
    frames: list[dict] = []
    for time_h, frame in df.groupby("t_h", sort=True):
        ordered = frame.sort_values("z_m")
        rows = []
        for row in ordered.to_dict(orient="records"):
            item = {
                "z_m": float(row["z_m"]),
                "u_r_m": float(row["u_r_m"]),
            }
            if "sigma_rr" in row and pd.notna(row["sigma_rr"]):
                item["sigma_rr"] = float(row["sigma_rr"])
            rows.append(item)
        frames.append({"t_h": float(time_h), "rows": rows})
    return frames


def _viewer_payload(result_dir: str | Path) -> dict:
    result, df = load_wall_profile(result_dir)
    max_u = float(df["u_r_m"].abs().max())
    scale, unit = auto_displacement_unit(max_u)
    return {
        "case_name": result.case_name,
        "element_type": result.element_type,
        "scale": scale,
        "unit": unit,
        "frames": _frames(df),
    }


def generate_html(result_dir: str | Path, output_path: str | Path | None = None) -> Path:
    payload = _viewer_payload(result_dir)
    result_path = Path(result_dir)
    out = Path(output_path) if output_path else result_path / "displacement_viewer.html"
    out.write_text(_html_document(payload), encoding="utf-8")
    return out


def show_matplotlib(result_dir: str | Path) -> None:
    result, df = load_wall_profile(result_dir)
    max_u = float(df["u_r_m"].abs().max())
    scale, unit = auto_displacement_unit(max_u)
    times = sorted(float(t) for t in df["t_h"].unique())

    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button, Slider

    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    plt.subplots_adjust(bottom=0.22)

    def frame_at(index: int) -> pd.DataFrame:
        return df[df["t_h"] == times[index]].sort_values("z_m")

    initial = frame_at(0)
    if len(initial) == 1:
        (line,) = ax.plot(initial["u_r_m"] * scale, initial["z_m"], "o-", lw=1.5)
    else:
        (line,) = ax.plot(initial["u_r_m"] * scale, initial["z_m"], "o-", lw=1.5)
    ax.set_xlabel(f"Deslocamento radial [{unit}]")
    ax.set_ylabel("Profundidade local z [m]")
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    title = ax.set_title(f"{result.case_name} - t = {times[0]:.4g} h")

    slider_ax = fig.add_axes([0.18, 0.10, 0.62, 0.04])
    slider = Slider(
        slider_ax,
        "Tempo",
        0,
        max(len(times) - 1, 0),
        valinit=0,
        valstep=1,
    )
    play_ax = fig.add_axes([0.82, 0.095, 0.12, 0.05])
    button = Button(play_ax, "Play")
    timer = fig.canvas.new_timer(interval=300)
    playing = {"value": False}

    def update(index_value: float) -> None:
        index = int(index_value)
        frame = frame_at(index)
        line.set_data(frame["u_r_m"] * scale, frame["z_m"])
        title.set_text(f"{result.case_name} - t = {times[index]:.4g} h")
        ax.relim()
        ax.autoscale_view()
        ax.invert_yaxis()
        fig.canvas.draw_idle()

    def advance() -> None:
        next_index = (int(slider.val) + 1) % len(times)
        slider.set_val(next_index)

    def toggle(_event) -> None:
        playing["value"] = not playing["value"]
        button.label.set_text("Pause" if playing["value"] else "Play")
        if playing["value"]:
            timer.start()
        else:
            timer.stop()

    slider.on_changed(update)
    button.on_clicked(toggle)
    timer.add_callback(advance)
    plt.show()


def _html_document(payload: dict) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False)
    title = html.escape(f"{payload['case_name']} - deslocamento na parede")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{ color-scheme: light; font-family: Georgia, 'Times New Roman', serif; }}
    body {{ margin: 0; background: #f6f7f8; color: #1f2933; }}
    main {{ max-width: 980px; margin: 32px auto; padding: 0 20px; }}
    h1 {{ font-size: 24px; margin: 0 0 6px; }}
    .sub {{ color: #5b6470; margin-bottom: 18px; }}
    .panel {{ background: #fff; border: 1px solid #d8dde3; border-radius: 8px; padding: 16px; }}
    canvas {{ width: 100%; height: 560px; display: block; }}
    .controls {{ display: flex; gap: 12px; align-items: center; margin-top: 12px; }}
    input[type=range] {{ flex: 1; }}
    button {{ border: 1px solid #9aa4af; background: #fff; padding: 8px 12px; border-radius: 6px; cursor: pointer; }}
    #timeLabel {{ min-width: 110px; font-variant-numeric: tabular-nums; }}
    #tip {{ position: fixed; display: none; background: rgba(31,41,51,.92); color: #fff; padding: 7px 9px; border-radius: 5px; font-size: 12px; pointer-events: none; }}
  </style>
</head>
<body>
<main>
  <h1>Deslocamento radial na parede</h1>
  <div class="sub">{html.escape(payload['case_name'])} · {html.escape(payload['element_type'])}</div>
  <div class="panel">
    <canvas id="plot" width="920" height="560"></canvas>
    <div class="controls">
      <button id="play">Play</button>
      <input id="slider" type="range" min="0" max="0" value="0" step="1">
      <span id="timeLabel">0 h</span>
      <button id="png">Exportar PNG</button>
    </div>
  </div>
</main>
<div id="tip"></div>
<script>
const payload = {payload_json};
const canvas = document.getElementById('plot');
const ctx = canvas.getContext('2d');
const slider = document.getElementById('slider');
const timeLabel = document.getElementById('timeLabel');
const playBtn = document.getElementById('play');
const pngBtn = document.getElementById('png');
const tip = document.getElementById('tip');
slider.max = Math.max(payload.frames.length - 1, 0);
let timer = null;
let points = [];

function lerp(a, b, t) {{ return a + (b - a) * t; }}
function colorFor(v, maxAbs) {{
  const t = maxAbs > 0 ? Math.min(Math.abs(v) / maxAbs, 1) : 0;
  const r = Math.round(lerp(31, 214, t));
  const g = Math.round(lerp(119, 39, t));
  const b = Math.round(lerp(180, 40, t));
  return `rgb(${{r}},${{g}},${{b}})`;
}}
function niceTime(t) {{ return Math.abs(t) < 1e-12 ? '0 h' : `${{Number(t).toPrecision(4)}} h`; }}
function draw() {{
  const frame = payload.frames[Number(slider.value)] || payload.frames[0];
  const rows = frame.rows;
  const margin = {{left: 82, right: 24, top: 28, bottom: 68}};
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, w, h);
  const us = rows.map(r => r.u_r_m * payload.scale);
  const zs = rows.map(r => r.z_m);
  const maxAbsU = Math.max(...us.map(Math.abs), 1e-12);
  let xmin = Math.min(...us), xmax = Math.max(...us);
  if (Math.abs(xmax - xmin) < 1e-12) {{ xmin -= 1; xmax += 1; }}
  const pad = 0.08 * (xmax - xmin);
  xmin -= pad; xmax += pad;
  let zmin = Math.min(...zs), zmax = Math.max(...zs);
  if (Math.abs(zmax - zmin) < 1e-12) {{ zmin -= 0.5; zmax += 0.5; }}
  const x = u => margin.left + (u - xmin) / (xmax - xmin) * (w - margin.left - margin.right);
  const y = z => margin.top + (z - zmin) / (zmax - zmin) * (h - margin.top - margin.bottom);
  ctx.strokeStyle = '#27313b';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(margin.left, margin.top);
  ctx.lineTo(margin.left, h - margin.bottom);
  ctx.lineTo(w - margin.right, h - margin.bottom);
  ctx.stroke();
  ctx.fillStyle = '#1f2933';
  ctx.font = '16px Georgia';
  ctx.fillText(`Tempo: ${{niceTime(frame.t_h)}}`, margin.left, 22);
  ctx.font = '14px Georgia';
  ctx.fillText(`Deslocamento radial [${{payload.unit}}]`, margin.left + 260, h - 20);
  ctx.save();
  ctx.translate(22, margin.top + 280);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('Profundidade local z [m]', 0, 0);
  ctx.restore();
  points = rows.map(r => ({{row: r, ux: r.u_r_m * payload.scale, x: x(r.u_r_m * payload.scale), y: y(r.z_m)}}));
  for (let i = 1; i < points.length; i++) {{
    ctx.strokeStyle = colorFor(points[i].ux, maxAbsU);
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.moveTo(points[i - 1].x, points[i - 1].y);
    ctx.lineTo(points[i].x, points[i].y);
    ctx.stroke();
  }}
  for (const p of points) {{
    ctx.fillStyle = colorFor(p.ux, maxAbsU);
    ctx.beginPath();
    ctx.arc(p.x, p.y, 4, 0, 2 * Math.PI);
    ctx.fill();
  }}
  timeLabel.textContent = niceTime(frame.t_h);
}}
slider.addEventListener('input', draw);
playBtn.addEventListener('click', () => {{
  if (timer) {{ clearInterval(timer); timer = null; playBtn.textContent = 'Play'; return; }}
  playBtn.textContent = 'Pause';
  timer = setInterval(() => {{
    slider.value = (Number(slider.value) + 1) % payload.frames.length;
    draw();
  }}, 350);
}});
pngBtn.addEventListener('click', () => {{
  const a = document.createElement('a');
  a.download = `${{payload.case_name}}_displacement_viewer.png`;
  a.href = canvas.toDataURL('image/png');
  a.click();
}});
canvas.addEventListener('mousemove', event => {{
  const rect = canvas.getBoundingClientRect();
  const mx = (event.clientX - rect.left) * canvas.width / rect.width;
  const my = (event.clientY - rect.top) * canvas.height / rect.height;
  let best = null, bestD = 1e9;
  for (const p of points) {{
    const d = Math.hypot(mx - p.x, my - p.y);
    if (d < bestD) {{ bestD = d; best = p; }}
  }}
  if (!best || bestD > 18) {{ tip.style.display = 'none'; return; }}
  const sigma = best.row.sigma_rr === undefined ? '' : `<br>σ_rr: ${{best.row.sigma_rr.toExponential(3)}} Pa`;
  tip.innerHTML = `z: ${{best.row.z_m.toFixed(4)}} m<br>u_r: ${{best.ux.toFixed(5)}} ${{payload.unit}}${{sigma}}`;
  tip.style.left = `${{event.clientX + 12}}px`;
  tip.style.top = `${{event.clientY + 12}}px`;
  tip.style.display = 'block';
}});
canvas.addEventListener('mouseleave', () => {{ tip.style.display = 'none'; }});
draw();
</script>
</body>
</html>
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visualiza u_r(z) na parede interna com controle de tempo.",
    )
    parser.add_argument("result_dir", help="Pasta de resultado do saltcreep.")
    parser.add_argument("--html", action="store_true",
                        help="Gera displacement_viewer.html standalone.")
    parser.add_argument("--out", help="Caminho do HTML de saida.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.html:
        out = generate_html(args.result_dir, args.out)
        print(f"Viewer HTML salvo em {out}")
        return 0
    show_matplotlib(args.result_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
