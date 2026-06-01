# Especificação do arquivo de caso (YAML)

Um arquivo por simulação, em `cases/`. O parser converte unidades de campo (lb/gal, polegadas) para SI
na borda; internamente tudo é SI. Schema:

```yaml
name: modelo_A                 # nome do caso (vira pasta de saída results/modelo_A/)

geometry:
  well_radius_m: 0.1556        # Ri (12.25 pol → m)
  outer_radius_factor: 1000    # Re = factor * Ri (domínio semi-infinito)
  layer_thickness_m: 20        # espessura da camada salina em estudo

depths:
  water_depth_m: 100           # lâmina d'água (LDA)
  burial_m: 500                # soterramento
  salt_above_m: 0              # sal acima da camada em estudo (H)

lithology:
  primary: halita              # halita | taquidrita | carnalita
  intercalations:              # opcional; vazio se não houver
    - material: taquidrita
      thickness_m: 10
      position: center

fluid:
  weight_lb_per_gal: 10        # peso do fluido de perfuração

stress:
  k0: 1.0                      # coeficiente de empuxo horizontal

# --- discretização: tipo de elemento e malha ---
element:
  type: axisym_1d_L3           # axisym_1d_L3 | axisym_2d_Q4 | axisym_2d_T3 | axisym_2d_Q8 | axisym_2d_Q9 | axisym_2d_AQ9 | axisym_2d_T6
mesh:
  n_elements_radial: 30
  ratio: 1000                  # razão comprimento último/primeiro elemento (refino na parede)
  n_elements_axial: 1          # >1 só para 2D
  adaptive: false              # ativa pre-refinamento h por estimador Zienkiewicz-Zhu
  error_threshold: 0.10        # marca elementos com eta_rel acima deste limite
  max_refinement_levels: 3     # teto de ciclos de refinamento
  damage_refinement_threshold: -1.0 # opcional; se >=0, refina onde max(D) ultrapassa o valor

# --- estágios de fluência: LIGA/DESLIGA por flag ---
creep:
  elastic_only: false          # se true, só resolve o elástico e para
  secondary: true              # mecanismo duplo (DM)
  primary: false               # fluência primária (EDMT / ISV_SH_DM)
  tertiary: false              # fluência terciária
  damage: false                # critério de dano / dilatância
  primary_model: EDMT          # usado só se primary:true  (EDMT | isv_sh_dm)
  tertiary_model: null         # usado só se tertiary:true (MottaV1 | wang_2004 | aubertin_isv_sh_d | Motta_v2)
  dilatancy_envelope: null     # usado só se damage:true   (Spier | Ratigan | DeVries | Hunsche)
  isv_sh_dm:
    e0_s: 5.0e-7               # [1/s]
    sig_ref: 1.0e6             # [Pa]
    n: 1.5
    Q_J_mol: 51.6e3            # [J/mol]
    T0: 359.15                 # [K]
    K_h: 1.2                   # hardening h = 1/sinh(asinh(1)+K_h eps_vp)
  motta_v1:
    n_d: 2.0                   # eps_dot = eps_dot_DM / (1-D)^n_d
    A_d: 1.0e-24               # coeficiente Kachanov
    m_d: 1.0                   # expoente da sobrepassagem da envoltória
    p_d: 0.0                   # expoente de aceleração por dano
    D_max: 0.99                # limite numérico; D nunca atinge 1
  spier:
    a: 0.25                    # f_dil = sqrt(J2) - a*I1_comp - b
    b_Pa: 0.0
  ratigan:
    c: 0.81                    # f_dil = sqrt(J2) - c*(I1_comp+d)^m
    d_Pa: 0.0
    m: 1.0
  devries:
    e_Pa: 10.0e6               # f_dil = sqrt(J2) - e*sinh(f*I1_comp/sigma0)
    f: 1.0
    sigma0_Pa: 30.0e6
  hunsche:
    g_Pa: 10.0e6               # f_dil = sqrt(J2) - g*(I1_comp/I1_ref)^h
    I1_ref_Pa: 30.0e6
    h: 1.0
  wang_2004:
    n_d: 2.0                   # eps_dot = eps_dot_DM / (1-D)^n_d
    A_d: 1.2e-8                # [1/s/Pa^m_d], default por litologia
    m_d: 2.5                   # expoente da tensão efetiva
    p_d: 1.0                   # expoente de aceleração por dano
    D_max: 0.99                # limite numérico; D nunca atinge 1
  aubertin_isv_sh_d:
    e0_s: 5.0e-7               # [1/s]
    sig0: 1.0e6                # [Pa]
    n: 3.0
    Q_J_mol: 51.6e3            # [J/mol]
    T0: 359.15                 # [K]
    K1: 0.8                    # f_primary = 1 + K1 exp(-K2 eps_vp)
    K2: 2.5                    # [1/strain]
    A_d: 1.5e-8                # dano intrínseco ISV_SH_D
    m_d: 2.5
    n_d: 2.0
    p_d: 1.0
    D_max: 0.99

# --- acoplamento termomecânico FRACO (Vasconcelos 2019) ---
thermal:
  enabled: false               # liga/desliga o acoplamento fraco
  mode: profile                # profile (analítico T(z)) | conduction_1d | conduction_2d
  seabed_temp_C: 4
  geothermal_gradient_C_per_m: 0.03 # alias preferido para profile
  grad_C_per_m: 0.03          # alias legado ainda aceito pelo parser
  grad_burial_C_per_m: 0.03    # gradiente do soterramento
  grad_salt_C_per_m: 0.012     # gradiente da rocha salina
  initial_temp_C: 90           # se mode=conduction_*: condição inicial uniforme
  inner_wall_temp_C: 90        # se mode=conduction_*: T prescrita em r=Ri
  outer_bc: prescribed         # prescribed (padrão) | flux_zero
  outer_temp_C: 60             # usado se outer_bc=prescribed em r=Re
  top_bc: flux_zero            # conduction_2d: prescribed | flux_zero
  top_temp_C: 50               # conduction_2d: usado se top_bc=prescribed
  bottom_bc: flux_zero         # conduction_2d: prescribed | flux_zero
  bottom_temp_C: 80            # conduction_2d: usado se bottom_bc=prescribed
  k_W_m_K: 2.5                 # condutividade térmica
  rho_kg_m3: 2160              # densidade
  cp_J_kg_K: 900               # calor específico
  layers:                      # conduction_2d: propriedades por camada em z
    - z_top_m: 0
      z_bottom_m: 500
      k_W_per_mK: 5.4
      rho_kg_per_m3: 2160
      cp_J_per_kgK: 860
    - z_top_m: 500
      z_bottom_m: 520
      k_W_per_mK: 3.1
      rho_kg_per_m3: 1600
      cp_J_per_kgK: 920
  dt_thermal_h: null           # passo térmico (Crank-Nicolson); null → mesmo do mecânico
  beta: 0.5                    # 0.5 = Crank-Nicolson (padrão); 1 = Euler implícito; 0 = explícito

time:
  total_h: 480                 # tempo total de simulação
  scheme: explicit             # explicit | implicit_adaptive
  dt_h: 0.5                    # passo (inicial, se adaptativo)
  tol_local: 1.0e-10           # Newton local do implícito
  tol_global: 1.0e-4           # erro relativo por step-doubling
  dt_min_h: 1.0e-12            # aborta abaixo deste passo
  dt_max_h: 10.0               # teto do passo adaptativo

output:
  every_n_steps: 10
  fields: [displacement, stress, damage]   # campos a gravar (VTU)
  series: [wall_closure_pct, closure_rate]  # séries temporais (CSV)
  vtu: false                    # true → escreve VTU para ParaView/PyVista
  vtu_every_n_steps: 10         # frequência da série VTU; passo final sempre é escrito
  revolve_3d: false             # reservado; hoje exporta o setor axissimétrico (r,z)
  damage_tracking: false        # true + creep.damage:true → damage_events.csv e damage_wall.csv
  damage_thresholds: [0.1, 0.3, 0.5, 0.8]
  failure_D_critical: 0.5       # critério operacional de falha da rocha
  creep_rate_multiplier_threshold: 10.0 # evento quando eps_dot >= 10× DM pura
```

## Regras de validação que o parser deve impor
- Exatamente um regime coerente: se `elastic_only:true`, ignore os demais flags de creep e avise.
- `primary_model`/`tertiary_model`/`dilatancy_envelope` só são lidos se o flag correspondente for true.
- `dilatancy_envelope` aceita `Spier`, `Ratigan`, `DeVries`, `Hunsche` (alias `Huensche`).
  Os blocos `spier`, `ratigan`, `devries` e `hunsche` são opcionais e substituem os defaults
  operacionais usados pelo `MottaV1`.
- `primary_model: isv_sh_dm` exige `primary:true`; recomenda-se `secondary:true`, pois o termo
  primário seno-hiperbólico decai para zero e a saturação física vem da DM secundária.
- `n_elements_axial > 1` exige um `element.type` 2D; com `axisym_1d_L3` deve ser 1.
- `mesh.adaptive:true` exige elemento 2D. O estimador Zienkiewicz-Zhu calcula erro em norma
  de energia para qualquer elemento 2D; a subdivisão conformante implementada atualmente cobre
  `axisym_2d_Q4` e `axisym_2d_T3`. Para outros elementos, se o estimador marcar refinamento, o
  solver aborta com mensagem explícita em vez de trocar a ordem do elemento silenciosamente.
- `mesh.error_threshold` deve ser não negativo; `mesh.max_refinement_levels` deve ser >= 0.
- `mesh.damage_refinement_threshold` é opcional. Valores negativos desativam marcação por dano;
  valores entre 0 e 0.99 marcam elementos cujo `InternalState::damage_D` máximo ultrapassa o limiar;
  valores acima de 0.99 são inválidos.
- Combinação `secondary:false` com `primary:true` é permitida (estudo da primária isolada) mas emite
  aviso: fisicamente a primária satura na secundária; útil só para análise.
- `scheme: explicit` com litologia taquidrita ou k0 > 1: emitir aviso de possível instabilidade
  (recomendar implicit_adaptive).
- `thermal.mode: conduction_1d` aceita `outer_bc: prescribed` ou `outer_bc: flux_zero`;
  se omitido, o padrão é `prescribed`.
- `thermal.mode: conduction_2d` exige elemento 2D e aceita `outer_bc`, `top_bc` e `bottom_bc`
  como `prescribed` ou `flux_zero`; `layers` é opcional e, se omitido, usa `k_W_m_K`,
  `rho_kg_m3` e `cp_J_kg_K` uniformes.
- `tertiary_model: wang_2004` exige `tertiary:true` e `damage:true`; não usa `dilatancy_envelope`.
  Os parâmetros padrão de `wang_2004` vêm da litologia (`halita` ou `taquidrita`) e podem ser
  sobrescritos no YAML do caso.
- `tertiary_model: aubertin_isv_sh_d` exige `tertiary:true`, mas não exige `damage:true`: o dano
  é intrínseco ao modelo ISV. Se `output.damage_tracking:true`, os CSVs de dano são gerados mesmo
  com `creep.damage:false`.
- `output.damage_tracking:true` só gera CSVs se `creep.damage:true`; sem dano, o solver ignora
  o rastreamento para evitar arquivos vazios.

## Por que flags e não compilação condicional
Permite varrer combinações de estágios e tipos de elemento por arquivos de caso (e em lote pelo
Python via pybind11) sem recompilar — essencial para o estudo de convergência e para a calibração.
