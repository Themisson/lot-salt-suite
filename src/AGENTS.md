# AGENTS.md — src/

Implementações C++20 do projeto lot-salt-suite.

## Estrutura esperada

`
src/
├── core/        # Tipos base
├── io/          # Parser YAML/JSON, escritor
├── units/       # Conversão de unidades
├── wellbore/    # Geometria de poço
├── fluids/      # Propriedades PVT
├── thermal/     # Perfil térmico
├── rocks/       # Modelos de rocha
├── salt/        # Adapters para sal
├── lot/         # Módulo LOT
├── apb/         # Módulo APB
├── geomechanics/# Tensão geostática
├── coupling/    # Acoplamento
├── validation/  # Métricas de erro
└── cli/         # Subcomandos CLI
`

## Regras

1. Todo .cpp em `src/` espelha um .hpp em `include/`
2. Sem lógica de negócio em `apps/lot-sim.cpp`
3. Sem parâmetros físicos hard-coded: usar structs de caso carregadas do YAML
4. Unidades sempre SI internamente
5. Não incluir headers de `legance/` ou `external/saltcreep/include/apb_code/`

## Subagente recomendado

`cpp-pro` para implementação, `cpp-refactor` para refatoração.
