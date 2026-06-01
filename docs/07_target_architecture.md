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
8. pós-processamento: invocar script Python se configurado
```
