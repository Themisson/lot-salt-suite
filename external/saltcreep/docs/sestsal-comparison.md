# Comparação Formal: SaltCreep vs. SESTSAL

**Objetivo:** Verificação numérica independente do motor SaltCreep contra o legado SESTSAL C++.

**Data de execução:** 2026-05-31  
**Status:** ⏳ TESTES IMPLEMENTADOS (RED, aguardando TimeIntegrator + DM)

---

## Estratégia de Teste

1. **Mapeamento de entrada:** Converter `.inp` (SESTSAL) → `.yaml` (SaltCreep).
2. **Extração de oráculo:** Ler `.out` (SESTSAL) → estrutura C++ com closure % esperado.
3. **Teste de regressão:** Rodar SaltCreep no caso equivalente → comparar fechamento % ± tolerância.
4. **Relatório:** Documento vivo com resultados por caso.

---

## Casos Mapeados

| Caso | Dimensão | Litologia | Tempo | Oracle (SESTSAL) | Arquivo |
|---|---|---|---|---|---|
| `base_model` | 1D axissim | Halita | 450 h | 1.66% | `cases/sestsal/base_model.yaml` |
| `hello_repasse` | 1D axissim | Halita | 480 h | 1.06% | `cases/sestsal/hello_repasse.yaml` |
| `base_model2D` | 2D (multicamada) | Halita+Taquidrita | 360 h | 0.037% | `cases/sestsal/base_model2D.yaml` |
| `hello_repasse2D` | 2D axissim | Halita | 60 h | 0.53% | `cases/sestsal/hello_repasse2D.yaml` |
| `repasse2D` | 2D axissim | Halita | 96 h | 0.25% | `cases/sestsal/repasse2D.yaml` |

**Nota:** `project61` e `keywords` são templates ou casos incompletos; 5 casos válidos mapeados.

---

## Resultados Esperados (após implementação de TimeIntegrator + DM)

### Nível 1: DM Puro (Secundária)

| Caso | SESTSAL [%] | SaltCreep [%] | Diff [%] | Tolerância | Status |
|---|---|---|---|---|---|
| base_model | 1.66 | TBD | — | ±5% | ⏳ RED |
| hello_repasse | 1.06 | TBD | — | ±5% | ⏳ RED |
| base_model2D | 0.037 | TBD | — | ±10%* | ⏳ RED |
| hello_repasse2D | 0.53 | TBD | — | ±10%* | ⏳ RED |
| repasse2D | 0.25 | TBD | — | ±10%* | ⏳ RED |

*Tolerância maior para casos 2D: análise numérica diferente, acoplamento multicamada.

---

## Protocolo de Verificação

**Pré-requisito para GREEN:**
1. ✓ Conversor `.inp` → `.yaml` funcional.
2. ✓ Oracle extrator funcionando → 5 casos com closure % final.
3. ⏳ `TimeIntegrator` implementado (loop Euler, stress update).
4. ⏳ `DoubleMechanism` implementado (taxa creep, Arrhenius).
5. ⏳ Testes de regressão passando (`tests/cpp/test_sestsal_verification.cpp`).

**Quando cada teste virar GREEN:**
```bash
ctest --test-dir build -R sestsal --output-on-failure
```

---

## Divulgação de Divergências

Se um teste virar **AMARELO** (5–15% erro) ou **VERMELHO** (> 15%):

1. **Verificar oracle:** Re-extrair de SESTSAL (.out) para confirmar.
2. **Comparar malha:** SaltCreep vs. SESTSAL têm mesma discretização?
3. **Parâmetros:** E, ν, k0, p_fluido, T, são idênticos?
4. **Formulação:** Diferenças em Voigt order, cálculo de σ_ef, Arrhenius?
5. **Integrador:** SESTSAL usa sub-stepping; SaltCreep usa Euler simples?

**Conclusão esperada:** Erros < 5% são aceitáveis (formulações close mas não idênticas).

---

## Tabela de Rastreamento (Vivo)

Será atualizada automaticamente pelo script `post/verficiation_report.py` após cada `ctest`.

```
Última atualização: (gerada automaticamente após testes)
```

---

## Próximas Etapas

1. Implementar `DoubleMechanism::evaluate()` (mecanismo duplo).
2. Implementar `TimeIntegrator` com loop Euler.
3. Rodar testes → verificar se ficam **GREEN** ou se precisam investigação.
4. Documentar qualquer divergência e sua causa.
5. Commit final: `test(verification): conversor SESTSAL + regressão vs. legacy`

---

## Referências

- **SESTSAL:** `legacy/sestsal/` (código legado C++)
- **Mapeamento de parâmetros:** `docs/sestsal-mapping-plan.md`
- **Conversor:** `tools/sestsal_converter.py`, `tools/sestsal_oracle.py`
- **Dados de oracle:** `include/test_sestsal_oracle.hpp`
- **Testes:** `tests/cpp/test_sestsal_verification.cpp`
