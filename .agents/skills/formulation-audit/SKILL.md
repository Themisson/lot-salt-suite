---
name: formulation-audit
description: Audit mathematical, physical, dimensional, sign-convention, and SI-unit consistency across lot-salt-suite LOT, APB, salt creep, migration, and coupling formulations.
---

# SKILL: formulation-audit

Audita formulações matemáticas, físicas e dimensionais no projeto lot-salt-suite.

## Finalidade

Verificar se implementações C++ e Python estão consistentes com:
- formulação LOT (docs/02_lot_formulation.md)
- formulação APB (docs/03_apb_formulation.md)
- modelos de sal (docs/04_salt_creep_models.md)
- convenções de sinais documentadas
- sistema de unidades (SI internamente)

## Quando usar

- Antes de qualquer merge de módulo físico
- Ao migrar um caso legado (verificar parâmetros extraídos)
- Após refatoração (verificar que formulação não mudou)
- Para investigar divergência de resultados entre legado e novo

## Restrições

- Não modificar código — apenas reportar divergências
- Não alterar docs sem aprovação
- Não comparar resultados sem baseline disponível

## Entregáveis

1. Lista de equações auditadas com status (correto/divergente/incerto)
2. Parâmetros físicos críticos com unidades verificadas
3. Convenções de sinais identificadas por módulo
4. Lista de riscos encontrados (para docs/08_known_issues.md)

## Riscos a evitar

- Confundir tensão efetiva com tensão total
- Misturar unidades PPG com kg/m³ sem conversão
- Assumir convenção de sinal sem verificar no código legado
