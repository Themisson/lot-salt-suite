"""Command-line interface for saltpost."""

from __future__ import annotations

from pathlib import Path
import argparse

from .compare import comparison_table
from .axisym3d import make_axisym_3d
from .animations import animate_result
from .export import export_paper_bundle, write_table_formats
from .plots import (
    plot_creep_rate,
    plot_damage_comparison,
    plot_damage_wall,
    plot_closure,
    plot_field_map,
    plot_final_closure_vs_dofs,
    plot_diameter_at_depth,
    plot_lithology_column,
    plot_radial_profile,
    plot_relative_error,
    plot_wellbore_diameter_profile,
    plot_wall_displacement,
    plot_wall_profile,
    plot_phase_space,
    write_comparison_outputs,
)
from .report import generate_dashboard
from .registry import discover_results
from .studies import VALID_VARY, discover_study_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compara resultados do saltcreep.")
    parser.add_argument("paths", nargs="*", help="Pastas de resultados especificas.")
    parser.add_argument("--glob", dest="glob_pattern", help="Padrao glob para results/*.")
    parser.add_argument("--study", help="Nome do estudo fisico a descobrir em results/.")
    parser.add_argument("--vary", choices=sorted(VALID_VARY),
                        help="Eixo declarativo do estudo: element, constitutive ou thermal.")
    parser.add_argument("--results-root", default="results",
                        help="Raiz onde --study procura resultados.")
    parser.add_argument("--group-by", choices=["element", "n_dofs"], default=None)
    parser.add_argument(
        "--plot",
        choices=["all", "closure", "displacement", "radial_profile",
                 "wall_profile", "field_map", "damage", "creep_rate",
                 "damage_comparison", "phase_space", "diameter_profile",
                 "diameter_time", "lithology_column", "axisym_3d"],
        default="all",
        help="Tipo de grafico a gerar.",
    )
    parser.add_argument("--time", type=float, default=None,
                        help="Tempo em horas para plots de perfil/mapa.")
    parser.add_argument("--depth", type=float, default=None,
                        help="Profundidade absoluta [m] para plots de diametro vs tempo.")
    parser.add_argument("--angle", type=float, default=270.0,
                        help="Angulo de revolucao para --plot axisym_3d.")
    parser.add_argument("--scale", type=float, default=None,
                        help="Escala da deformada para --plot axisym_3d.")
    parser.add_argument("--format", choices=["default", "paper"], default="default",
                        help="Formato de exportacao; paper cria nomes padronizados e LaTeX.")
    parser.add_argument("--report", action="store_true",
                        help="Gera dashboard HTML estatico em results/report.")
    parser.add_argument("--report-dir", default="results/report",
                        help="Diretorio do dashboard HTML.")
    parser.add_argument("--animate",
                        choices=["all", "closure", "ur", "damage", "temperature"],
                        help="Gera animacoes GIF/MP4 para cada caso.")
    parser.add_argument("--animation-format", choices=["gif", "mp4"], default="gif")
    parser.add_argument("--fps", type=int, default=4, help="Frames por segundo das animacoes.")
    parser.add_argument("--summary", action="store_true", help="Gera apenas tabela-resumo.")
    parser.add_argument("--reference", help="Nome ou caminho do caso de referencia.")
    parser.add_argument("--out-dir", default="results/comparison", help="Diretorio de saida.")
    return parser


def choose_reference(results, reference_hint: str | None):
    if not results:
        return None
    if reference_hint:
        for result in results:
            if reference_hint in {result.case_name, str(result.path), result.path.name}:
                return result
    return results[0]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    study_vary = args.vary
    if args.study:
        study_vary = args.vary or "element"
        results = discover_study_results(args.study, study_vary, args.results_root)
    else:
        results = discover_results(args.glob_pattern, args.paths)
    if not results:
        raise SystemExit("Nenhum resultado encontrado.")

    out_dir = Path(args.out_dir)
    group_by = args.group_by
    if group_by is None and (study_vary or "") == "element":
        group_by = "element"
    reference = choose_reference(results, args.reference)

    if args.summary:
        table = comparison_table(results, reference)
        out_dir.mkdir(parents=True, exist_ok=True)
        write_table_formats(table, out_dir, "summary", args.format)
        if args.format == "paper":
            export_paper_bundle(out_dir, args.study, study_vary)
        if args.report:
            generate_dashboard(results, out_dir, args.report_dir, args.study, study_vary)
        print(f"Resumo salvo em {out_dir}")
        return 0

    write_comparison_outputs(results, out_dir, reference, args.format)

    if args.plot in {"all", "closure"}:
        plot_closure(results, out_dir, group_by)
        if reference is not None:
            plot_relative_error(results, reference, out_dir, group_by)
        plot_final_closure_vs_dofs(results, out_dir)
    if args.plot in {"all", "displacement"}:
        plot_wall_displacement(results, out_dir, group_by)
    if args.plot in {"radial_profile"}:
        for result in results:
            plot_radial_profile(result, out_dir, args.time)
    if args.plot in {"wall_profile"}:
        for result in results:
            plot_wall_profile(result, out_dir, args.time)
    if args.plot in {"field_map"}:
        for result in results:
            plot_field_map(result, out_dir, args.time)
    if args.plot in {"diameter_profile"}:
        plot_wellbore_diameter_profile(results, out_dir, args.time, group_by)
    if args.plot in {"diameter_time"}:
        plot_diameter_at_depth(results, out_dir, args.depth, group_by)
    if args.plot in {"lithology_column"}:
        for result in results:
            plot_lithology_column(result, out_dir)
    if args.plot in {"axisym_3d"}:
        for result in results:
            make_axisym_3d(
                result.path,
                out_dir / f"{result.case_name}_axisym_3d.png",
                args.time,
                args.angle,
                args.scale,
            )
    if args.plot in {"all", "damage"}:
        plot_damage_wall(results, out_dir, group_by)
    if args.plot in {"all", "creep_rate"}:
        plot_creep_rate(results, out_dir, group_by)
    if args.plot in {"damage_comparison"}:
        plot_damage_comparison(results, out_dir, group_by)
    if args.plot in {"all", "phase_space"}:
        plot_phase_space(results, out_dir, group_by)
    if args.animate:
        for result in results:
            animate_result(result, args.animate, out_dir, args.fps, args.animation_format)
    if args.format == "paper":
        export_paper_bundle(out_dir, args.study, study_vary)
    if args.report:
        generate_dashboard(results, out_dir, args.report_dir, args.study, study_vary)
    print(f"Comparacao salva em {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
