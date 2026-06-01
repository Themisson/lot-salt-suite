# Pós-processamento profissional (`saltpost`)

Este documento resume a camada de pós-processamento do SaltCreep. O objetivo é transformar
as pastas `results/<caso>/` em figuras, tabelas, dashboards HTML e animações reprodutíveis,
sem tocar no solver C++.

## Entradas esperadas

Cada caso deve ter, quando aplicável:

- `metadata.json` — nome do caso, elemento, GDLs, esquema temporal, flags de fluência,
  timers e metadados de malha.
- `closure.csv` — tempo, fechamento percentual e deslocamento radial da parede.
- `displacements_profile.csv` — perfil `u_r(r,z,t)` para mapas/perfis.
- `wall_profile.csv` — perfil `u_r(z,t)` na parede interna.
- `damage_wall.csv` e `damage_events.csv` — diagnóstico de dano/falha.
- `*.vtu` e `*.pvd` — campos espaciais para ParaView/PyVista.

## Comparação clássica

```bash
python post/compare_cases.py results/modelo_A_L3 results/modelo_A_Q8
python post/compare_cases.py --glob "results/modelo_A_*" --group-by element
python post/compare_cases.py --summary --glob "results/*"
```

As saídas padrão são salvas em `results/comparison/`:

- `comparison_table.csv`
- `comparison_table.md`
- figuras PNG/PDF com 300 dpi

## Estudos declarativos

Quando os resultados seguem uma convenção de nomes ou metadados, use `--study` e `--vary`.
Isso evita escrever globs diferentes para cada campanha.

```bash
python post/compare_cases.py --study modelo_A --vary element
python post/compare_cases.py --study modelo_A --vary constitutive
python post/compare_cases.py --study modelo_A --vary thermal
```

Eixos disponíveis:

- `element` — compara L3, Q4, T3, Q8, Q9, T6 e AQ9.
- `constitutive` — infere DM, EDMT, Motta, Wang, Aubertin ou ISV_SH_DM pelos metadados
  e nomes de caso.
- `thermal` — infere `none`, `profile`, `conduction_1d` ou `conduction_2d`.

Use `--results-root` para estudar uma árvore alternativa:

```bash
python post/compare_cases.py --study modelo_A --vary element --results-root results/campanha_01
```

## Exportação científica

O modo `--format paper` cria um subdiretório `paper/` com nomes determinísticos,
figuras em PNG/PDF e tabelas CSV/Markdown/LaTeX.

```bash
python post/compare_cases.py --study modelo_A --vary element --format paper
```

Exemplos de arquivos:

- `paper/fig_01_closure_vs_tempo_modelo_a_by_element.png`
- `paper/fig_01_closure_vs_tempo_modelo_a_by_element.pdf`
- `paper/tab_comparison_table_modelo_a_by_element.csv`
- `paper/tab_comparison_table_modelo_a_by_element.md`
- `paper/tab_comparison_table_modelo_a_by_element.tex`
- `paper/paper_manifest.csv`

## Dashboard HTML estático

Use `--report` para gerar `results/report/index.html` com figuras, resumo de metadados,
tabelas e links diretos para CSV/VTU/PVD dos casos.

```bash
python post/compare_cases.py --study modelo_A --vary element --report
python post/compare_cases.py --glob "results/modelo_A_*" --report --out-dir results/modelo_A_report
```

O dashboard é estático e offline-first: basta abrir `results/report/index.html` no navegador.

## Animações

O CLI pode gerar GIFs, e MP4 quando `ffmpeg` estiver disponível.

```bash
python post/compare_cases.py results/modelo_A_Q8 --animate closure
python post/compare_cases.py results/modelo_A_Q8 --animate ur
python post/compare_cases.py results/modelo_A_Q8 --animate damage
python post/compare_cases.py results/modelo_A_Q8 --animate temperature
python post/compare_cases.py results/modelo_A_Q8 --animate all --animation-format mp4
```

Fontes dos campos:

- `closure` usa `closure.csv`.
- `ur` usa `displacements_profile.csv`.
- `damage` usa `damage_D` nos VTUs.
- `temperature` usa `temperature_K` nos VTUs.

Se PyVista ou os arquivos VTU não estiverem disponíveis, as animações de campo são puladas
sem impedir os demais gráficos.

## Exemplo completo

```bash
python post/compare_cases.py \
  --study modelo_A \
  --vary element \
  --format paper \
  --report \
  --animate closure \
  --out-dir results/comparison/modelo_A_element \
  --report-dir results/report/modelo_A_element
```

