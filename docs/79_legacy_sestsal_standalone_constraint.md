# Fase 11.10F-aux — restrição standalone do SESTSAL legado

## Resumo executivo

A Fase 11.10F-aux registra uma restrição técnica do SESTSAL legado: ele não
deve ser usado como motor standalone de validação. A função de fluência calcula
o tensor desviador, normaliza por `norm_sigd` e não possui guarda explícita
para o estado hidrostático puro, no qual `norm_sigd == 0`.

Classificação:

```text
cause = LEGACY_SESTSAL_REQUIRES_APB1DA_COUPLING
gate = DO_NOT_USE_SESTSAL_STANDALONE_AS_VALIDATION_REFERENCE
secondary_cause = ELASTIC_DISPLACEMENT_REFERENCE_MISMATCH
secondary_gate = ALIGN_TOTAL_VS_PERTURBATION_DISPLACEMENT_BEFORE_COMPARISON
```

Esta auditoria é somente leitura. Nenhum arquivo em `legacy/`, `legance/` ou
`external/saltcreep/` foi alterado.

## Evidência em material.cpp

Arquivos auditados:

```text
legance/LOT_Tese/src/sestsal/material.cpp
legance/LOT_APB_v5/src/sestsal/material.cpp
```

Ambas as versões contêm a mesma estrutura essencial:

```text
norm_sigd = sqrt(sigd(0)^2 + sigd(1)^2 + sigd(2)^2)
dev = 1 / norm_sigd * sigd
sigde = sqrt(1.5) * norm_sigd
b = sqrt(1.5) * deviatoricStrainRate(sigde, T) * dev
```

Para estado hidrostático puro:

```text
sigma_rr = sigma_theta = sigma_zz
sigd = {0, 0, 0}
norm_sigd = 0
dev = sigd / norm_sigd
```

Esse caminho pode produzir `NaN` se chamado isoladamente, pois a normalização
ocorre antes de qualquer guarda de `norm_sigd`.

## Uso esperado no legado

O uso original esperado não é chamar `Material::creepFunction(...)` como
validador standalone. No LOT_Tese, a rota acoplada passa por:

```text
APB1da::getNodalDisplacement(...)
  -> APBSalt1D::setInnerPressure(pi + dP)
  -> APBSalt1D::setInnerTemperature(Ti + dT)
  -> APBSalt1D::solveThermalViscoStep(dt)
```

Esse fluxo fornece carregamento, pressão, temperatura e estado incremental por
meio do wrapper APB/sal. Portanto, uma chamada hidrostática pura e isolada não
representa o uso operacional que o legado exercia.

## Classificação de testes standalone

Testes que tentem usar `legacy/sestsal` ou `legance/*/sestsal` isoladamente
como referência de validação devem ser classificados como:

```text
UNSUPPORTED_STANDALONE_VALIDATION_REFERENCE
```

Eles podem ser úteis para reproduzir a restrição, mas não devem reprovar o
moderno nem servir como baseline físico.

## Deslocamento total versus perturbacional

Outra restrição registrada é a comparação entre deslocamento total legado e
deslocamento perturbacional moderno. O legado acoplado carrega histórico,
pressão, temperatura, geostática e estado incremental. Um resultado moderno que
represente apenas perturbação elástica/diagnóstica não é diretamente comparável
sem alinhar:

- referencial inicial;
- sinal;
- componente total versus incremental;
- tempo de acomodação;
- pressão e temperatura aplicadas no mesmo passo;
- ponto físico de amostragem.

Até esse alinhamento existir, a comparação fica bloqueada:

```text
ALIGN_TOTAL_VS_PERTURBATION_DISPLACEMENT_BEFORE_COMPARISON
```

## Ferramenta de auditoria

A fase adiciona:

```text
tools/audit_legacy_sestsal_standalone_constraint.py
```

A ferramenta verifica:

- presença de divisão por `norm_sigd`;
- ausência de guarda explícita para `norm_sigd == 0`;
- norma desviadora nula em estado hidrostático puro;
- evidência de uso acoplado via `APB1da`;
- bloqueio de validação standalone;
- bloqueio de comparação total versus perturbacional.

## Implicação prática

Este achado deve ser registrado agora, mas não deve travar a Fase 11.10F
principal do writer PennyShaped. A restrição pertence à trilha sal/APB e serve
para impedir que testes standalone de SESTSAL sejam usados como referência
numérica indevida.
