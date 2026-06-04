# Pós-processamento profissional (`saltpost`)

Este documento resume a camada de pós-processamento do SaltCreep. O objetivo é transformar
as pastas `results/<caso>/` em figuras, tabelas, dashboards HTML e animações reprodutíveis,
sem tocar no solver C++.

## Entradas esperadas

Cada caso deve ter, quando aplicável:

- `metadata.json` — nome do caso, elemento, GDLs, esquema temporal, flags de fluência,
  timers, geometria do poço, profundidade de referência e camadas litológicas visuais.
- `closure.csv` — tempo, fechamento percentual, deslocamento radial da parede e diâmetro
  instantâneo do poço.
- `displacements_profile.csv` — perfil `u_r(r,z,t)` para mapas/perfis.
- `wall_profile.csv` — perfil `u_r(z,t)` na parede interna, com `depth_m`,
  `diameter_m`, `diameter_in` e `original_diameter_in` quando gerado por versões atuais.
- `wall_pressure_profile.csv` — pressão e temperatura aplicadas na parede interna por tempo
  e profundidade (`p_wall_Pa`, `T_wall_K`), útil para validar peso de lama hidrostático.
- `wall_stress.csv` — quando `output.stress_diagnostics:true`, tensões no GP mais próximo da
  parede interna: `sigma_theta_Pa`, `sigma_theta_comp_Pa`, desviador, `J2` e `sigma_ef`.
- `stress_profile.csv` — quando `stress_diagnostics_scope: all_gauss`, os mesmos campos para
  todos os pontos de Gauss.
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

## Validação de pressão por peso de lama

Os casos em `cases/apb/` exercitam o modo `fluid.mode: hydrostatic_depth_profile`.
No 1D, a pressão é avaliada na profundidade do caso; no 2D, é avaliada ao longo da
parede interna com `depth_origin + z`.

Para acoplar com outro código APB ou hidráulico, use `fluid.mode: csv_time_depth_profile`
e, opcionalmente, `thermal.mode: csv_wall_temperature`. O CSV recomendado é uma grade
completa `t_h,z_m,p_wall_Pa,T_wall_K`; o solver interpola linearmente em tempo e
profundidade e mantém o primeiro/último valor fora da faixa do arquivo.

## Diagnóstico de tensão para APB

Para reproduzir chamadas legadas como `getSigmaTheta()` e `getDeviatoricStress()` sem colocar
estado dentro do modelo constitutivo, ative:

```yaml
output:
  stress_diagnostics: true
  stress_diagnostics_scope: wall  # ou all_gauss
```

O arquivo `wall_stress.csv` contém a tensão circunferencial interna `sigma_theta_Pa` e a coluna
`sigma_theta_comp_Pa`, que já inverte o sinal para a convenção APB de compressão positiva.
As colunas `sdev_*`, `J2_Pa2` e `sigma_ef_Pa` são calculadas a partir do mesmo tensor de tensão
armazenado em `TimeState::sigma_gp`.

```bash
./build/saltcreep cases/apb/mud_gradient_1d_8p5ppg.yaml
./build/saltcreep cases/apb/mud_gradient_2d_Q8_8p5ppg.yaml
./build/saltcreep cases/apb/apb_1d_constant_mud.yaml
./build/saltcreep cases/apb/apb_1d_schedule_mud_temperature.yaml
./build/saltcreep cases/apb/apb_2d_layered_schedule_Q8.yaml

python - <<'PY'
import pandas as pd
df = pd.read_csv("results/mud_gradient_2d_Q8_8p5ppg/wall_pressure_profile.csv")
print(df[["depth_m", "p_wall_Pa", "T_wall_K"]].head())
PY
```

Os três casos `apb_*` usam fluência ativa. O caso 1D constante serve como baseline, o caso 1D
com agenda lê pressão/temperatura de `data/apb/mud_schedule_example.csv`, e o caso 2D Q8 usa a
mesma agenda com camadas litológicas visuais para testar perfis `p_wall(z,t)`, `T_wall(z,t)` e
diâmetro/deslocamento ao longo da profundidade.

Gráficos específicos de pressão na parede:

```bash
# Perfil p_wall(z) em instantes selecionados
python post/compare_cases.py results/mud_gradient_2d_Q8_8p5ppg --plot wall_pressure_profile

# Evolução p_wall(t) no topo, meio e base da parede
python post/compare_cases.py results/mud_gradient_2d_Q8_8p5ppg --plot wall_pressure_time

# Mapa p_wall(z,t)
python post/compare_cases.py results/mud_gradient_2d_Q8_8p5ppg --plot wall_pressure_map
```

## Benchmark do custo de `p_wall(z,t)`

Para medir o custo incremental da pressão variável na parede, use o benchmark dedicado. Ele
gera casos Q8 2D temporários e compara três modos de carregamento: pressão constante, perfil
hidrostático por peso de lama e CSV operacional `p_wall(t,z)`.

```bash
# Smoke rápido: 3 casos pequenos, um por modo de pressão
python post/benchmark_wall_pressure.py --preset smoke

# Campanha recomendada: malhas small/medium/large com 1 thread
python post/benchmark_wall_pressure.py --preset standard --threads 1

# Campanha completa com OpenMP
python post/benchmark_wall_pressure.py --preset full --threads 1,2,4

# Conferir a matriz planejada sem rodar o solver
python post/benchmark_wall_pressure.py --preset full --threads 1,2,4 --dry-run
```

As saídas ficam em `results/benchmark_wall_pressure/`:

- `benchmark_wall_pressure.json` — resultados brutos e caminhos dos casos.
- `benchmark_wall_pressure.csv` — tabela plana para planilhas.
- `benchmark_wall_pressure.md` — relatório Markdown com resumo por modo e por malha.
- `wall_pressure_time_vs_dofs.png/pdf` — tempo total vs GDLs.
- `wall_pressure_overhead_vs_dofs.png/pdf` — sobrecusto relativo ao modo constante.
- `wall_pressure_breakdown.png/pdf` — composição montagem/solve/constitutivo.

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

## Diâmetro do poço e litologias

Os gráficos de diâmetro convertem o deslocamento radial da parede em:

```text
D(t,z) = 2 * (Ri + u_r(t,z))
```

O eixo de profundidade usa `metadata.depth_origin_m + z_m`, permitindo reproduzir perfis
tipo SESTSAL/ABAQUS em profundidade absoluta.

```bash
# Diâmetro do poço ao longo da profundidade em um instante
python post/compare_cases.py results/modelo_A_Q8 --plot diameter_profile --time 360

# Diâmetro em uma profundidade específica ao longo do tempo
python post/compare_cases.py results/modelo_A_Q8 --plot diameter_time --depth 4100

# Comparar DM vs EDMT na mesma profundidade
python post/compare_cases.py results/modelo_A_secondary_only results/modelo_A_primary_secondary \
  --plot diameter_time --depth 4100

# Coluna litológica anotada a partir de metadata.json
python post/compare_cases.py results/modelo_A_Q8 --plot lithology_column

# Setor 3D axissimétrico da parede do poço
python post/compare_cases.py results/modelo_A_Q8 --plot axisym_3d --time 360 --angle 270
python post/axisym_solid_3d.py results/modelo_A_Q8 --time 360 --save results/modelo_A_Q8/axisym_3d.png
```

As camadas em `lithology.layers` são usadas para anotação visual. Elas ainda não mudam a lei
constitutiva por ponto de Gauss; para contraste mecânico real por litologia, será necessária
uma etapa posterior com material por camada.

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
