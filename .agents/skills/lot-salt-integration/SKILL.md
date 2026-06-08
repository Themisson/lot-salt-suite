---
name: lot-salt-integration
description: Integrate LOT/APB workflows with salt creep interfaces, adapters, bridge diagnostics, wall-stress contracts, and salt coupling modules without copying external saltcreep source code.
---

# SKILL: lot-salt-integration

Integra LOT/APB com modelos de fluência de sal do saltcreep.

## Finalidade

- Criar e manter include/salt/SaltCreepInterface.hpp
- Implementar SaltCreepSaltcreepAdapter para saltcreep
- Implementar SaltCreepSESTSALAdapter para compatibilidade legada
- Criar casos acoplados LOT-sal e APB-sal

## Quando usar

- Para implementar o módulo salt/ (Fase 8)
- Para criar casos de validação de acoplamento
- Para investigar divergência entre SESTSAL legado e saltcreep

## Restrições

- NUNCA copiar código de external/saltcreep/src/ para src/salt/
- Sempre verificar convenção de sinais na fronteira LOT-sal
- Verificar unidades de tensão e deformação na interface
- Criar baseline do sal isolado ANTES do acoplamento

## Protocolo de integração

1. Validar modelo de sal isolado contra saltcreep (erro < 0.1%)
2. Validar LOT isolado contra baseline LOT_Tese
3. Criar caso LOT+sal mínimo (1 camada de halita)
4. Comparar com caso equivalente manual

## Entregáveis

1. include/salt/SaltCreepInterface.hpp
2. include/salt/SaltCreepSaltcreepAdapter.hpp (e .cpp)
3. Caso YAML de validação em cases/validation/
4. Tabela de erro: SESTSAL vs saltcreep para halita/carnalita

## Riscos a evitar

- Tensão compressiva com sinal errado na interface de acoplamento
- Unidades de deformação diferentes entre LOT (m/m) e saltcreep (mm/mm)
- Duplicação silenciosa de parâmetros de sal
