# 14 — Guia do Desenvolvedor

**Status:** Planejado | **Última atualização:** 2026-06-01

## Fluxo de trabalho

## Política operacional — C++ first, Python postprocess only

Antes de criar qualquer arquivo Python, Codex/Claude deve responder:

1. É pós-processamento de `CSV/JSON` já gerado pelo C++?
2. É relatório/gráfico/auditoria auxiliar fora do runtime?
3. É migração pontual em `tools/`, marcada como não-runtime e acompanhada de
   relatório de mapeamento?

Se a resposta for "não" para essas três perguntas, a tarefa deve ser C++.

O fluxo normal do simulador é:

```text
YAML/JSON → C++ parser → C++ model/runner → C++ writer → CSV/JSON
```

O fluxo Python permitido é:

```text
CSV/JSON → Python plot/report → PNG/HTML
```

Agentes não devem propor Python como pré-processador padrão, gerador de YAML de
produção, substituto de solver, executor de física runtime, calibrador
automático sem fase dedicada ou caminho obrigatório para rodar LOT/APB/sal.

### Adicionar um novo módulo C++

1. Criar `include/<modulo>/<Modulo>.hpp` com interface pública
2. Criar `src/<modulo>/<Modulo>.cpp` com implementação
3. Criar `tests/cpp/test_<modulo>.cpp` com Catch2 (mínimo 3 testes)
4. Adicionar ao `CMakeLists.txt`
5. Verificar com `cmake --build build -j && ctest`
6. Atualizar `docs/07_target_architecture.md`
7. Executar `python tools/generate_docs_index.py`

### Migrar um caso legado

1. Ler o arquivo `.cpp` ou `.json` com `legacy-explorer`
2. Extrair parâmetros com `tools/migrate_*.py`
3. Criar YAML em `cases/`
4. Validar com `lot-sim inspect --case <arquivo.yaml>`
5. Executar com `lot-sim run`
6. Comparar com baseline (se existir)
7. Documentar em `docs/09_migration_plan.md`

### Atualizar docs/index.html

1. Editar o arquivo `.md` relevante em `docs/`
2. Atualizar `tools/docs_status.yaml` se o status mudou
3. Executar `python tools/generate_docs_index.py`
4. Verificar que index.html abre sem erro no browser

### Antes de qualquer PR/commit

1. `cmake --build build -j` — zero erros
2. `ctest --test-dir build --output-on-failure` — 100% verde
3. `pytest tests/python -q` — 100% verde
4. Revisar `docs/08_known_issues.md` — nenhum risco novo sem documentação

## Windows / Visual Studio / CMake 4 — notas de compatibilidade

### CMake 4 e yaml-cpp

CMake 4 removeu a compatibilidade com `cmake_minimum_required(VERSION < 3.5)`. O `CMakeLists.txt`
define `CMAKE_POLICY_VERSION_MINIMUM 3.5` antes de `FetchContent_MakeAvailable(yaml-cpp)`,
o que elimina a necessidade de passar a flag manualmente.

Após a correção, o configure funciona diretamente:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
```

### Visual Studio — gerador multi-config

O Visual Studio é um gerador multi-config: o executável fica em subdiretório por configuração.

```
build\Debug\lot-sim.exe
build\Release\lot-sim.exe
```

O build e os testes devem sempre especificar `--config Debug` (ou Release):

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --config Debug -j
ctest --test-dir build -C Debug --output-on-failure
```

Os testes C++ de CLI localizam `lot-sim.exe` automaticamente via macro
`LSS_LOT_SIM_EXECUTABLE` injetada pelo CMake com `$<TARGET_FILE:lot-sim>`,
que resolve o caminho correto para qualquer gerador (single-config ou multi-config).

### Windows Defender Application Control (WDAC) / Device Guard

Em máquinas com WDAC em modo **enforcement** (`UsermodeCodeIntegrityPolicyEnforcementStatus = 2`),
binários não assinados compilados localmente podem ser bloqueados pelo kernel. Isso afeta
os testes de CLI que invocam `lot-sim.exe` como subprocesso.

**Sintoma:** `lot-sim.exe` bloqueado com mensagem "foi bloqueado pela política do Device Guard".

**Verificação:**

```powershell
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root/Microsoft/Windows/DeviceGuard |
  Select-Object UsermodeCodeIntegrityPolicyEnforcementStatus
# 2 = enforcement (bloqueia), 1 = audit (só loga), 0 = desabilitado
```

**Workaround para desenvolvimento:**
- Desabilitar Smart App Control: Windows Security → App & browser control → Smart App Control → Off
- Ou assinar os binários com um certificado de desenvolvedor
- Ou colocar a política WDAC em modo audit durante o desenvolvimento

**Impacto nos testes:** apenas os 2 testes de CLI (`CLI run succeeds for…`) são afetados;
os 45 demais testes passam normalmente, pois executam a lógica internamente sem spawnar subprocesso.

### Desabilitar apenas testes CLI por subprocesso

Em ambientes Windows com WDAC/Smart App Control bloqueando binários não assinados como
subprocesso, mantenha todos os testes de solver/parser/writer ativos e desabilite somente
os testes que executam `lot-sim.exe` via `std::system`:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DLSS_ENABLE_CLI_SUBPROCESS_TESTS=OFF
cmake --build build --config Debug -j
ctest --test-dir build -C Debug --output-on-failure
```

O padrão permanece `ON`, portanto CI e ambientes sem WDAC continuam exercitando a CLI por
subprocesso:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --config Debug -j
ctest --test-dir build -C Debug --output-on-failure
```

Quando `LSS_ENABLE_CLI_SUBPROCESS_TESTS=OFF`, rode a CLI manualmente para confirmar o
executável:

```powershell
.\build\Debug\lot-sim.exe validate --case cases\validation\lot_pkn_minimal.yaml
.\build\Debug\lot-sim.exe validate --case cases\validation\lot_pkn_with_leakoff.yaml
.\build\Debug\lot-sim.exe validate --case cases\lot_tese_migrated\buz67d_pkn.yaml
.\build\Debug\lot-sim.exe run --case cases\validation\lot_pkn_minimal.yaml --mode lot-pkn --output results\lot_pkn_minimal_wdac_manual
```

## Skills disponíveis

| Skill | Quando usar |
|-------|------------|
| `/formulation-audit` | Antes de implementar qualquer módulo físico |
| `/cpp-refactor` | Para refatoração C++ |
| `/validation-benchmark` | Para criar/executar testes de regressão |
| `/postprocess-report` | Para pós-processamento Python |
| `/docs-html-report` | Para atualizar documentação |
| `/lot-salt-integration` | Para integração LOT+sal |
