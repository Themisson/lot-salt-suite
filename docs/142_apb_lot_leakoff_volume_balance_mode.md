# APB/LOT leakoff volume balance mode

## Resumo executivo

Foram formalizados dois modos de acoplamento do leakoff:

```text
legacy_nodal_force
volume_balance
```

`volume_balance` aplica explicitamente:

```text
dV_coupled = dV + dV_leakoff
```

## Convencao de sinal

O contrato documenta que `dV_leakoff_m3` positivo ou negativo deve seguir a
convencao do chamador. Nos testes, leakoff que retira volume hidraulico e
representado por contribuicao negativa, reduzindo o volume efetivo que pressuriza
o anular.

## Compatibilidade

`legacy_nodal_force` preserva `dV` sem somar o termo de leakoff, representando o
modo legado para comparacao. O PKN padrao nao foi alterado.
