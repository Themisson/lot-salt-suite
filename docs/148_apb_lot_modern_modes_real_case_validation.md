# APB/LOT modern modes real case validation

## Resumo executivo

A fase `APB_LOT_VALIDATE_MODERN_MODES_WITH_REAL_APB_CASE` auditou se os modos
modernos APB/LOT ja podem ser exercitados por um caso real/controlado de ponta
a ponta. O resultado e bloqueado:

```text
APB_LOT_REAL_CASE_EXECUTION_BLOCKED_BY_MISSING_RUNNER
```

O parser e os contratos de modo existem, e o `ApbLotJsonOutputWriter` tambem
existe. Entretanto, o runtime `lot-sim run` ainda aceita apenas
`--mode lot-pkn` e nao chama `write_apb_lot_output_json(...)`.

## Auditoria do runtime

| Pergunta | Resultado |
|---|---|
| Existe comando/runner APB/LOT moderno? | Nao. `apps/lot-sim.cpp` rejeita qualquer modo diferente de `lot-pkn`. |
| Existe caso APB/LOT real moderno executavel? | Nao nesta fase. |
| Existe caminho para gerar `*_out.json` a partir do runtime? | Nao. O writer esta isolado em testes de contrato. |
| `volume_balance` e exercitado pelo solver APB? | Nao. O modo existe como contrato/parser/helper. |
| `pre_iterative` e exercitado pelo solver APB? | Nao. O modo existe como contrato/parser/helper. |
| Modos legados permanecem disponiveis? | Sim, como contrato: `legacy_dat`, `legacy_nodal_force`, `legacy_inside_newton`. |

## Fixtures de contrato

Foram adicionadas fixtures pequenas em
`tests/fixtures/comparison/phase_apb_lot_real_case/`:

| Fixture | Papel |
|---|---|
| `apb_lot_modern_real_controlled.yaml` | declara `json + volume_balance + pre_iterative` |
| `apb_lot_legacy_controlled.yaml` | declara os modos legados preservados |
| `apb_lot_modern_explicit_output.yaml` | registra caminho de saida explicito |

Essas fixtures nao sao casos fisicos APB. Elas mantem o contrato rastreavel ate
existir runner real.

## Decisao

Nao foi gerado `*_out.json` real nesta fase. Gerar uma saida fake violaria o
objetivo da validacao. A decisao correta e registrar o bloqueio e planejar a
integracao runtime.

```text
REAL_CASE_RUNNER_INTEGRATION_REQUIRED
PKN_BEHAVIOR_NOT_CHANGED
BUZ29_PENNY_NOT_EXECUTED
```

## Proxima fase recomendada

```text
APB_LOT_IMPLEMENT_REAL_CASE_RUNNER_INTEGRATION
```

Essa fase deve criar uma rota APB/LOT real ou controlada que:

1. aceite `apb_lot.output_format = json`;
2. chame `ApbLotJsonOutputWriter`;
3. preencha `time_series`, `layers`, `annulars` e `summary` com dados efetivos;
4. exercite `volume_balance` e `pre_iterative` no solver, ou bloqueie cada modo
   com motivo tecnico especifico;
5. preserve `lot-pkn` e BUZ29/PENNY.

## Atualizacao posterior

A fase seguinte `APB_LOT_IMPLEMENT_REAL_CASE_RUNNER_INTEGRATION` resolveu o
bloqueio de infraestrutura por meio de uma rota controlada:

```text
APB_LOT_REAL_CASE_RUNNER_IMPLEMENTED
LOT_SIM_APB_LOT_MODE_AVAILABLE
MODERN_JSON_OUTPUT_GENERATED
```

O registro acima permanece como histórico do bloqueio original. A nova rota
continua diagnostica/controlada e nao deve ser interpretada como validacao
fisica APB/LOT ou equivalencia com LOT_Tese.
