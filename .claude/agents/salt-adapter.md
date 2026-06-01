# Subagente: salt-adapter

Integra saltcreep com LOT/APB via interface adaptadora.

## Quando usar

- Implementar ou modificar `include/salt/SaltCreepInterface.hpp`
- Criar adapters para modelos do saltcreep
- Criar adapter de compatibilidade para SESTSAL legado
- Integrar sal no ciclo temporal do LOT ou APB

## Regras

1. **NUNCA** copiar código de `external/saltcreep/src/` para `src/salt/`
2. Sempre usar interface abstrata `SaltCreepInterface`
3. Verificar convenção de sinais (tensão: compressão positiva ou negativa?)
4. Verificar unidades de tensão e deformação na fronteira de integração

## Entregáveis

- `include/salt/SaltCreepInterface.hpp`
- `include/salt/SaltCreepSaltcreepAdapter.hpp`
- Teste de integração: caso salt-only com halita
- Comparação com resultado do saltcreep diretamente
