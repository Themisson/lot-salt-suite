"""Thin CLI wrapper for SaltCreep axisymmetric 3D visualization."""

from __future__ import annotations

import argparse

from saltpost.axisym3d import make_axisym_3d


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera visualizacao 3D axissimetrica da parede do poco.",
    )
    parser.add_argument("result_dir", help="Pasta de resultado do SaltCreep.")
    parser.add_argument("--time", type=float, default=None, help="Tempo alvo [h].")
    parser.add_argument("--angle", type=float, default=270.0, help="Setor de revolucao [graus].")
    parser.add_argument("--scale", type=float, default=None, help="Escala da deformada.")
    parser.add_argument("--save", default=None, help="PNG de saida.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out = make_axisym_3d(
        args.result_dir,
        save=args.save,
        time_h=args.time,
        angle_deg=args.angle,
        displacement_scale=args.scale,
    )
    print(f"Figura 3D salva em {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
