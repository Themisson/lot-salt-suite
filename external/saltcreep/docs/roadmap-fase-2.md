# Roadmap Fase 2 — Extensões além do roadmap original

As Etapas 0–5 entregaram o solver completo do roadmap original (69 testes C++ + 3 Python).
Esta Fase 2 cobre as extensões de pesquisa. Cada etapa segue o MESMO protocolo das anteriores:

> **Protocolo por etapa:** ler docs → propor plano → aprovação → implementar → testar (regressão
> + novos) → atualizar `docs/index.html` (manual) → atualizar `docs/dev-log.md` + `AGENTS.md` →
> commit. Mostrar o plano ANTES de implementar quando a etapa for arquiteturalmente sensível.

Ordem recomendada (cada uma é independente, mas esta sequência maximiza o valor incremental):

| Etapa | Tema | Dependências | Complexidade |
|---|---|---|---|
| 6 | Saída VTU (visualização) | nenhuma | baixa |
| 7 | AQ9 enriquecido | baseline Q4–T6 (pronto) | alta |
| 8 | Mais modelos constitutivos | DM, Motta (prontos) | média |
| 9 | Mais envoltórias de dilatância | Spier (pronta) | baixa |
| 10 | Conduction 2D | Conduction1D (pronto) | média |
| 11 | Verificação formal vs SESTSAL | casos TCC (prontos) | média |
| 12 | Refinamento adaptativo | tudo acima | alta |

Recomendo começar pela **Etapa 6 (VTU)** — baixa complexidade, alto valor visual, e habilita a
inspeção dos campos que as etapas seguintes vão produzir (dano, tensão em 2D).

═══════════════════════════════════════════════════════════════════════════
## ETAPA 6 — Saída VTU para ParaView / PyVista
═══════════════════════════════════════════════════════════════════════════

**Objetivo:** exportar os campos (deslocamento, tensão, deformação viscosa, dano, temperatura)
em formato VTU (VTK Unstructured Grid) para visualização 3D em ParaView ou PyVista.

**Prompt:**
> "Etapa 6 — saída VTU. Leia `docs/architecture.md` e a classe de output atual.
>
> 1. Criar `VtuWriter` em `include/io/` + `src/io/` que escreve `.vtu` (formato XML do VTK)
>    com a malha (nós + conectividade) e os campos por nó/célula: u_r, u_z, σ (4 componentes
>    Voigt), ε_v, dano D, temperatura T.
> 2. Para o caso axissimétrico, exportar o setor 2D (r,z); opcionalmente revolver em 3D para
>    visualização (flag `output.revolve_3d`).
> 3. Flag YAML: `output.vtu: true` e `output.vtu_every_n_steps: N` (não escrever todo passo —
>    seria caro). Escrever sempre o passo final.
> 4. Suportar série temporal: `caso_0000.vtu`, `caso_0001.vtu`, ... + um `.pvd` que o ParaView
>    abre como animação.
> 5. Teste: rodar modelo_A, abrir o VTU em PyVista no teste Python, verificar que os arrays de
>    campo existem e têm o tamanho certo (n_nodes).
> 6. Atualizar `post/saltpost` com um módulo `vtk.py` que carrega VTU em PyVista para plots 3D.
> 7. Atualizar o manual (`docs/index.html`): card do VtuWriter na seção I/O, e mencionar VTU na
>    seção de pós-processamento.
> 8. Commit: `feat(io): saída VTU + série temporal .pvd para ParaView/PyVista`."

═══════════════════════════════════════════════════════════════════════════
## ETAPA 7 — Elemento AQ9 enriquecido (Trefftz / base de Lamé)
═══════════════════════════════════════════════════════════════════════════

**Objetivo:** portar o elemento da dissertação (Araújo 2012; Vasconcelos 2019) cuja base de
interpolação inclui o campo analítico de Lamé (1/r), capturando o gradiente da parede com
pouquíssimos GDLs. Comparar precisão por GDL contra os elementos clássicos.

**Prompt:**
> "Etapa 7 — elemento AQ9 enriquecido. Use o subagente `legacy-explorer` para mapear a
> formulação AQ9 no Matlab em `legacy/ModeloDissertacao_31out/`.
>
> 1. PRIMEIRO: legacy-explorer reporta como o AQ9 monta a base enriquecida (funções de forma
>    clássicas + termo 1/r de Lamé), a integração usada, e como a matriz B fica. Mostre esse
>    mapeamento ANTES de implementar.
> 2. Mostrar o desenho do elemento (base enriquecida, pontos de integração, matriz B) e
>    aguardar aprovação — este elemento é não-trivial (base de Trefftz).
> 3. Implementar `AxisymAQ9` seguindo o contrato Element. Registrar no factory.
> 4. Testes: patch test, Lamé (deve convergir com MUITO menos GDLs que Q8/Q9 — esse é o ponto),
>    regressão TCC modelo_A_AQ9.
> 5. Atualizar `post/convergence.py` para incluir AQ9 na comparação erro × GDL — o AQ9 deve
>    aparecer dramaticamente à esquerda (menos GDLs para o mesmo erro).
> 6. Atualizar o manual: tabela de elementos + card AQ9 + nota sobre a vantagem de GDLs.
> 7. Commit: `feat(elements): AQ9 enriquecido com base de Lamé — alta precisão por GDL`."

═══════════════════════════════════════════════════════════════════════════
## ETAPA 8 — Mais modelos constitutivos
═══════════════════════════════════════════════════════════════════════════

**Objetivo:** ampliar o catálogo de leis de fluência. Implementar um por vez, na ordem.

### 8a — Wang 2004 (Lemaitre/Chaboche CDM)
> "Etapa 8a — modelo Wang 2004. Leia `docs/constitutive-models.md` (seção Wang). Implementar
> `Wang2004` como ConstitutiveModel: CDM clássico com tensão efetiva σ̃ = σ/(1−D), D evolui com
> taxa dependente de tensão e estado. Limite numérico D_max ≈ 0.99. Tangente analítica.
> Testes: sem dano = DM, monotonia de D, limite numérico, caso severo com implícito. Atualizar
> manual (card Wang2004 na seção constitutiva). Commit: `feat(constitutive): Wang 2004 CDM`."

### 8b — Aubertin ISV_SH_D (unificado)
> "Etapa 8b — modelo Aubertin ISV_SH_D. Formulação unificada com variáveis de estado interno
> (ISV) acoplando primária + secundária + terciária + dano numa lei só. Mais parâmetros, mais
> robusto. Implementar como ConstitutiveModel, tangente analítica ou numérica. Testes: reduz aos
> regimes conhecidos nos limites apropriados, monotonia de dano. Atualizar manual. Commit:
> `feat(constitutive): Aubertin ISV_SH_D unificado`."

### 8c — ISV_SH_DM (primária seno-hiperbólico)
> "Etapa 8c — modelo ISV_SH_DM. Alternativa à EDMT para a primária, usando função
> seno-hiperbólico no hardening. Deve saturar para DM no permanente (mesmo teste da EDMT).
> Implementar, testar saturação, atualizar manual. Commit: `feat(constitutive): ISV_SH_DM`."

═══════════════════════════════════════════════════════════════════════════
## ETAPA 9 — Mais envoltórias de dilatância
═══════════════════════════════════════════════════════════════════════════

**Objetivo:** além da Spier, implementar Ratigan, DeVries e Hunsche. São critérios de início de
dano (funções f(σ)=0 no espaço de tensões). Devem ser intercambiáveis via flag.

**Prompt:**
> "Etapa 9 — envoltórias de dilatância. Implementar Ratigan, DeVries e Hunsche como classes
> intercambiáveis (interface `DilatancyEnvelope` ou similar; refatorar a Spier para essa
> interface se ainda não estiver). Cada uma é f(σ) = 0 em invariantes I1, J2. Flag YAML
> `creep.dilatancy_envelope: Ratigan|DeVries|Hunsche|Spier`. Testes: cada envoltória dispara no
> nível de tensão esperado; comparação das quatro num mesmo caso. Atualizar manual (seção
> constitutiva + select do construtor interativo). Commit: `feat(constitutive): envoltórias
> Ratigan, DeVries, Hunsche + interface DilatancyEnvelope`."

═══════════════════════════════════════════════════════════════════════════
## ETAPA 10 — Conduction 2D (contraste térmico vertical)
═══════════════════════════════════════════════════════════════════════════

**Objetivo:** equação de calor 2D (r,z) para quando há contraste de condutividade vertical —
intercalações de litologias com k diferente. Extensão natural do Conduction1DField.

**Prompt:**
> "Etapa 10 — Conduction2DField. Leia `docs/thermal-coupling.md` e a classe Conduction1DField.
> Implementar a equação de calor 2D axissimétrica com os mesmos elementos 2D (Q8 recomendado),
> Crank-Nicolson β=½, matriz [C + Δt·β·H] fatorada uma vez. Suportar k variável por litologia
> (intercalações). Flag YAML `thermal.mode: conduction_2d`. Testes: estado estacionário 2D
> analítico (onde existir), consistência com conduction_1d no limite sem contraste vertical,
> balanço de energia. Atualizar manual (card Conduction2DField). Commit: `feat(thermal):
> Conduction2DField — calor 2D com contraste vertical de condutividade`."

═══════════════════════════════════════════════════════════════════════════
## ETAPA 11 — Verificação formal vs SESTSAL
═══════════════════════════════════════════════════════════════════════════

**Objetivo:** formalizar a comparação com o SESTSAL como testes automáticos no ctest, em vez de
checagem manual. Este é o objetivo central de "verificador independente".

**Prompt:**
> "Etapa 11 — verificação formal vs SESTSAL. Use o legacy-explorer para localizar os casos e
> resultados de referência do SESTSAL em `legacy/sestsal/examples/`.
>
> 1. legacy-explorer mapeia: quais casos o SESTSAL tem, formato dos arquivos de entrada (.nf) e
>    de saída, e quais grandezas comparar (fechamento, tensão na parede, perfil radial).
> 2. Criar um conversor `.nf → .yaml` (ou casos YAML equivalentes) para rodar os mesmos casos
>    no SaltCreep. Colocar em `cases/sestsal/`.
> 3. Criar testes de regressão em `tests/cpp/test_sestsal_verification.cpp` que rodam os casos e
>    comparam com os resultados do SESTSAL dentro de tolerância documentada.
> 4. Onde houver divergência, NÃO relaxar tolerância — investigar e documentar a causa (pode ser
>    diferença de formulação legítima, ou bug).
> 5. Atualizar manual: seção de verificação com a comparação SESTSAL formalizada.
> 6. Commit: `test(verification): comparação formal vs SESTSAL no ctest`."

═══════════════════════════════════════════════════════════════════════════
## ETAPA 12 — Refinamento adaptativo de malha
═══════════════════════════════════════════════════════════════════════════

**Objetivo:** estimador de erro a posteriori (Zienkiewicz-Zhu) que marca elementos com erro alto
para refino h. Útil para malhas com intercalações onde o gradiente não está só na parede.

**Prompt:**
> "Etapa 12 — refinamento adaptativo. Leia a seção de refinamento adaptativo em
> `docs/elements.md`. Implementar estimador de erro Zienkiewicz-Zhu (recuperação de gradiente):
> compara o campo de tensão descontínuo (por elemento) com um campo recuperado suavizado; a
> diferença estima o erro local. Marcar elementos acima de um limiar para refino h.
>
> 1. Mostrar o plano (como o estimador é calculado, como a malha é refinada, como os campos são
>    transferidos para a nova malha) ANTES de implementar — é arquiteturalmente sensível.
> 2. Flag YAML `mesh.adaptive: true`, `mesh.error_threshold: ...`, `mesh.max_refinement_levels`.
> 3. Testes: num caso com gradiente conhecido, o refino concentra onde o erro é alto; a solução
>    refinada converge mais rápido que malha uniforme com mesmos GDLs.
> 4. Comparar adaptativo vs progressão geométrica fixa no estudo de convergência.
> 5. Atualizar manual: seção de elementos (refinamento adaptativo, agora implementado).
> 6. Commit: `feat(mesh): refinamento adaptativo h com estimador Zienkiewicz-Zhu`."

═══════════════════════════════════════════════════════════════════════════
## Notas gerais da Fase 2
═══════════════════════════════════════════════════════════════════════════

- **Cada etapa preserva 100% da regressão.** A contagem de testes só cresce.
- **O manual é atualizado em toda etapa** que toca a API pública (subagente docs-sync ou manual).
- **Plano antes de implementar** para etapas marcadas como "alta complexidade" (7, 12) e qualquer
  uma que mexa em infraestrutura.
- **legacy-explorer** é a ponte para o conhecimento do Matlab/SESTSAL (etapas 7 e 11).
- Quando concluir uma etapa, me envie a saída + dev-log atualizado e eu reviso + preparo a próxima.

═══════════════════════════════════════════════════════════════════════════
## ETAPA 6.5 — OpenMP + benchmarking de desempenho
═══════════════════════════════════════════════════════════════════════════

**Prompt:**
> "Etapa 6.5 — paralelismo OpenMP e benchmarking. Leia `docs/architecture.md`.
>
> 1. Adicionar `#pragma omp parallel for` nos loops de pontos de Gauss do Assembler
>    (`assemble_stiffness`, `assemble_pseudo_force`, `assemble_thermal_force`) e dos dois
>    integradores (avaliação constitutiva por GP).
> 2. No CMakeLists.txt: `find_package(OpenMP)` e `target_link_libraries(... OpenMP::OpenMP_CXX)`.
>    Se OpenMP não disponível, compilar sem (fallback sequencial, sem erro).
> 3. Verificar que o resultado é IDÊNTICO com 1 vs N threads. Rodar modelo_A com Q8 e comparar
>    closure final: diferença deve ser < epsilon de floating point (~1e-14). Se não for, há
>    data race — debugar antes de commitar.
> 4. Criar `post/benchmark.py` que roda o mesmo caso com OMP_NUM_THREADS=1,2,4,8, coleta
>    wall_time_s de cada metadata.json, e plota speedup vs threads.
> 5. Adicionar campos ao metadata.json: `omp_threads`, `time_assembly_s`, `time_solve_s`,
>    `time_constitutive_s` (timers granulares).
> 6. Atualizar o manual: seção de desempenho com resultados do benchmark, nota sobre OpenMP.
> 7. Commit: `perf(solver): OpenMP nos loops de GP + benchmark de desempenho`."

═══════════════════════════════════════════════════════════════════════════
## ETAPA 8d — Diagnóstico de falha (detecção do ponto de ruptura)
═══════════════════════════════════════════════════════════════════════════

Adicionar após a Etapa 8c (ISV_SH_DM). Funciona com QUALQUER modelo que tenha dano (Motta, Wang,
Aubertin) — é uma camada de diagnóstico, não uma lei constitutiva nova.

**Prompt:**
> "Etapa 8d — diagnóstico de falha por dano. Leia `docs/constitutive-models.md` (seção Motta v1)
> e a implementação de `InternalState::damage_D`.
>
> **Contexto físico:** quando D → D_max, a taxa de fluência diverge e a tensão efetiva explode.
> O ponto de inflexão na curva ε × t (onde a taxa para de desacelerar e começa a acelerar) é o
> indicador clássico da transição secundária → terciária. D > D_crítico (configurável) é o
> critério operacional de 'falha da rocha'.
>
> **O que implementar:**
>
> 1. **Registro de eventos de dano.** Durante a simulação, registrar em um log estruturado
>    (CSV ou seção do metadata.json) os instantes e posições (r, z, GP) onde:
>    - D ultrapassa limiares configuráveis (ex.: 0.1, 0.3, 0.5, 0.8, D_max).
>    - A taxa de fluência atinge um limiar (ex.: 10× taxa DM pura).
>    - A inflexão da curva ε × t é detectada (d²ε/dt² muda de sinal).
>    Formato sugerido: `damage_events.csv` com colunas [t_h, r, z, gp_id, D, eps_dot, event].
>
> 2. **Flag YAML:**
>    ```yaml
>    output:
>      damage_tracking: true
>      damage_thresholds: [0.1, 0.3, 0.5, 0.8]
>      failure_D_critical: 0.5     # critério operacional de falha
>    ```
>
> 3. **Plot de D(t) na parede.** No saltpost, adicionar função que plota a evolução do dano no
>    ponto de Gauss mais danificado (tipicamente na parede interna, na interseção com a
>    intercalação mais fraca). Plotar D × tempo com os limiares marcados como linhas horizontais.
>
> 4. **Gráfico de taxa de fluência × tempo.** Plotar ε̇ × t para o mesmo ponto, mostrando:
>    - Regime primário (taxa decrescente);
>    - Regime secundário (taxa constante = DM);
>    - Regime terciário (taxa crescente, após D iniciar).
>    - Marcar o ponto de inflexão como 'início da terciária'.
>
> 5. **Curva σ_ef × D (espaço de fase).** Plotar a trajetória no espaço tensão efetiva vs dano
>    para o GP mais danificado — mostra como o dano cresce com o estado de tensão.
>
> 6. **Comparação com/sem terciária.** Casos lado a lado:
>    - `modelo_A_pri_sec.yaml` (primária + secundária, sem dano)
>    - `modelo_A_pri_sec_ter.yaml` (com terciária + dano + Spier + implícito)
>    Plotar as curvas de closure sobrepostas — a separação entre elas mostra exatamente o
>    momento em que o dano inicia e o quanto ele acelera o fechamento.
>
> 7. **Testes:**
>    - damage_events.csv é gerado corretamente quando damage_tracking: true.
>    - Limiares são atingidos na ordem crescente (0.1 antes de 0.3, etc.).
>    - Sem terciária/dano, o CSV é vazio (nenhum evento).
>    - Regressão: 69 C++ + 4 Python verdes.
>
> 8. **Atualizar o manual** (`docs/index.html`):
>    - Na seção constitutiva (MottaV1), adicionar subseção 'Diagnóstico de falha'.
>    - Na seção de pós-processamento, adicionar os novos plots de dano.
>    - Na seção de input, mostrar os campos de damage_tracking no YAML anotado.
>
> 9. **Commit:** `feat(diagnostics): rastreamento de dano + detecção de falha + plots D(t)`."

═══════════════════════════════════════════════════════════════════════════
## Adição ao manual: seção de Visualização de Resultados
═══════════════════════════════════════════════════════════════════════════

Ao final da Etapa 6.5 ou 8d (ou agora, se quiser antecipar), o subagente `docs-sync` ou o
agente direto deve adicionar ao `docs/index.html` uma seção nova `#visualization` com:

### Conteúdo da nova seção

**Título:** Visualização de Resultados

**Subsections:**

1. **Gráficos automáticos (saltpost)**
   - `python post/compare_cases.py --glob "results/*" --group-by element`
   - Closure × tempo, erro relativo, tabela comparativa
   - Cores fixas por tipo de elemento

2. **Estudo de convergência**
   - `python post/convergence.py`
   - Erro × GDLs para os 6 (ou 7, com AQ9) elementos

3. **Visualização 3D — ParaView**
   - Como abrir `.pvd`; screenshots de exemplo das views úteis
   - Filters recomendados: Warp by Vector, Clip, Plot Over Line
   - Animação temporal (botão Play no ParaView)

4. **Visualização 3D — PyVista (programático)**
   - `pv.read("...vtu")` + `.plot(scalars="u_r")`
   - Perfil radial: `mesh.sample_over_line(...)`
   - Série temporal com PVDReader

5. **Diagnóstico de falha (quando implementado)**
   - D(t) na parede
   - Taxa de fluência × tempo com inflexão marcada
   - Comparação com/sem terciária

**Inserir na sidebar** entre `#post` e `#verify`, com link `<a href="#visualization">`.

### Adição ao manual: seção de Física da Terciária e Falha

Na seção `#physics`, após "Acoplamento termomecânico FRACO", adicionar um bloco:

**Título:** Fluência terciária e detecção de falha

**Conteúdo:**
- A variável de dano D ∈ [0, 0.99] é o indicador de progressão para falha.
- D = 0: material íntegro, taxa = DM pura.
- D → D_max: taxa amplificada por (1−D)^{−n_d}, tensão efetiva σ/(1−D) → ∞.
- O ponto de inflexão na curva ε × t (d²ε/dt² muda de sinal) marca o início da terciária.
- D > D_crítico (configurável) é o critério operacional de falha.
- A envoltória de dilatância (Spier) marca quando o dano pode iniciar: f_dil > 0 → regime
  dilatante → dano evolui; f_dil ≤ 0 → confinamento seguro → dD/dt = 0.
- Para análise quantitativa de falha: os parâmetros do Motta e da Spier DEVEM ser calibrados
  com ensaios triaxiais que incluam o estágio terciário até ruptura.

**Incluir uma nota do tipo warn:**
> "Para identificar o ponto de falha, rode com creep.tertiary: true + creep.damage: true +
> time.scheme: implicit_adaptive. O explícito diverge no regime terciário acelerado."
