# 04 — Modelos de Fluência de Sal

**Status:** Planejado | **Última atualização:** 2026-06-01

## Modelos no legado (SESTSAL)

O módulo `sestsal/` em `legance/LOT_Tese/` e `legance/LOT_APB_v5/` implementa
o modelo de mecanismo duplo (double mechanism):

`
dε/dt = A₁·σⁿ¹·exp(-Q₁/RT) + A₂·σⁿ²·exp(-Q₂/RT)
`

Parâmetros hard-coded identificados:

| Material | e0 (1/h) | sig0 (Pa) | n1 | n2 | T0 (°C) |
|----------|----------|-----------|----|----|---------|
| Halita | 1.8792e-6 | 9.92e6 | 3.36 | 7.55 | 86 |
| Carnalita | 1.581e-4 | 5.743e6 | 2.868 | 7.09 | 130 |

## Modelos no saltcreep (referência moderna)

| Modelo | Tipo |
|--------|------|
| `double_mechanism` | Secundária (equivalente ao SESTSAL) |
| `edmt` | Primária |
| `isv_sh_dm` | Primária sinh-hiperbólica |
| `motta_v1` | Terciária + dano Kachanov |
| `wang_2004` | CDM não-linear |
| `aubertin_isv_sh_d` | Unificada ISV |

## Estratégia de integração

Usar `SaltCreepInterface` (interface abstrata) + adapters:
- `SaltCreepSaltcreepAdapter` — usa saltcreep diretamente
- `SaltCreepSESTSALAdapter` — compatibilidade com SESTSAL interno

Ver docs/13_coupling_lot_apb_salt.md para detalhes de integração.
