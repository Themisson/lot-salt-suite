# 07 — Arquitetura-Alvo

**Status:** Planejado | **Última atualização:** 2026-06-01

## Diagrama de módulos

```
apps/lot-sim.cpp
    └── include/cli/         (subcomandos: run, validate, inspect, migrate)
         └── include/io/     (parser YAML+JSON → CaseData)
              └── include/units/ (conversão de unidades → SI)
                   └── Módulos físicos:
                        ├── include/wellbore/     (geometria)
                        ├── include/fluids/       (PVT)
                        ├── include/thermal/      (T(z))
                        ├── include/rocks/        (elástico)
                        ├── include/salt/         (SaltCreepInterface + adapters)
                        ├── include/lot/          (fratura, leakoff)
                        ├── include/apb/          (balanço anular)
                        ├── include/geomechanics/ (tensão geostática)
                        └── include/coupling/     (orquestrador)
```

## Núcleo de simulação

O núcleo de simulação do `lot-salt-suite` é C++.

Devem permanecer em C++:

- parsing YAML/JSON e conversão para SI;
- modelos físicos de LOT, APB, sal, leakoff, breakdown e dano;
- integração com `external/saltcreep`;
- acoplamento LOT/APB/sal;
- runners e writers que produzem `CSV/JSON`.

Python é uma camada externa. Ele pode consumir `CSV/JSON` já gravado pelo C++
para gráficos, relatórios, auditorias auxiliares e migrações pontuais
não-runtime, mas não deve ser necessário para executar a simulação.

Fluxo principal:

```text
YAML/JSON → C++ parser → C++ model/runner → C++ writer → CSV/JSON
```

Fluxo de pós-processamento:

```text
CSV/JSON → Python plot/report → PNG/HTML
```

## Regra de dependência

- `core/` ← todos os módulos dependem
- `units/` ← `io/` depende
- `io/` ← `cli/` depende
- Módulos físicos **não** dependem entre si diretamente — somente via `coupling/`
- `coupling/` orquestra todos os módulos físicos

## Interfaces plugáveis

### SaltCreepInterface

```cpp
class SaltCreepInterface {
public:
    struct Result {
        double strain_rate;   // dε/dt [1/s] — taxa de deformação viscosa
        double strain;        // ε — deformação acumulada
    };
    virtual Result evaluate(
        double sigma_eff_Pa,  // tensão efetiva [Pa]
        double T_K,           // temperatura [K]
        double dt_s           // passo de tempo [s]
    ) const = 0;
    virtual ~SaltCreepInterface() = default;
};
```

### Adapter para saltcreep

```cpp
class SaltCreepSaltcreepAdapter : public SaltCreepInterface {
    // Delega para modelo de external/saltcreep por interface
    // NÃO copia código de saltcreep — usa via include
};
```

`external/saltcreep/` e tratado como dependencia vendorizada ativa, com edicao
controlada. O adapter deve preferir superficies existentes do solver, como
campos de pressao de parede, diagnosticos de dano e saidas de pos-processamento,
antes de criar rotas paralelas no `lot-salt-suite`.

### Adapter para SESTSAL legado

```cpp
class SaltCreepSESTSALAdapter : public SaltCreepInterface {
    // Compatibilidade com modelo interno dos legados
    // Útil para verificar que novo código = legado para mesma formulação
};
```

## Estrutura do executável lot-sim

```bash
lot-sim <subcomando> [flags]

Subcomandos:
  run       --case <yaml> --mode <modo> [--output <dir>]
  inspect   --case <yaml|json>
  validate  --suite <nome> | --case <yaml> --baseline <json>
  migrate   --from-json <json> --to-yaml <yaml>
  list      --dir <dir>
```

## Fluxo de execução (modo `run --mode lot-salt`)

```
1. parse YAML → CaseData
2. converter unidades → SI (CaseData em SI)
3. inicializar geometria do poço
4. inicializar campo térmico
5. calcular tensão geostática inicial
6. inicializar fluidos por anular
7. loop temporal:
   a. atualizar T(z, t)
   b. calcular LOT: pressão de fratura, leakoff
   c. chamar SaltCreepInterface: deformação → variação de volume
   d. calcular APB: nova pressão dos anulares
   e. verificar convergência
   f. salvar saída se (passo % output_every == 0)
8. escrever CSV/JSON pelo writer C++
9. pós-processamento externo opcional: script Python consome CSV/JSON já gerado
```

## Prioridade LOT/PKN

A primeira entrega moderna do modulo `lot/` deve priorizar PKN, conforme a
auditoria em `docs/audits/pkn_legacy_path.md`. Os modelos circular, eliptico e
penny-shaped permanecem catalogados, mas fora do primeiro caminho critico.

O contrato minimo para LOT/PKN deve separar:

- calendario de injecao e acomodacao;
- deteccao de breakdown;
- modelo PKN com entradas SI;
- acumulacao de leakoff/fratura;
- serializacao de series temporais para comparacao.
