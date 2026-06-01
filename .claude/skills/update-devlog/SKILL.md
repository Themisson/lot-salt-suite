# SKILL: update-devlog

Atualiza `docs/dev-log.md` com o estado atual do projeto e o último commit.

## Quando usar

- Após qualquer commit ou push feito **fora** do Claude Code (terminal, IDE)
- Quando o saltcreep for atualizado e copiado para `external/saltcreep/`
- Para forçar atualização do bloco "Estado atual" sem novo commit
- No início de uma nova sessão se o dev-log estiver desatualizado

## Comandos disponíveis

```bash
# Entrada completa (commit + estado) — uso padrão
python tools/update_devlog.py

# Apenas atualizar bloco "Estado atual" (sem nova entrada)
python tools/update_devlog.py --status

# Ver o que seria gerado sem salvar
python tools/update_devlog.py --dry-run
```

## O que o script faz automaticamente

1. Lê o último commit via `git log -1`
2. Detecta arquivos alterados (`git diff --name-only HEAD~1`)
3. Se arquivos em `external/saltcreep/` foram alterados → adiciona seção "Saltcreep Update"
4. Se arquivos em `tests/baselines/` foram alterados → marca baseline atualizado
5. Atualiza contagem de testes C++ e Python
6. Prepende nova entrada em `docs/dev-log.md`
7. Commita o dev-log com marcador `[skip-devlog]` para evitar loop infinito

## Proteção anti-loop

Commits com `[skip-devlog]` no subject são ignorados pelo script.
O hook do Claude Code também verifica isso antes de executar.

## Restrições

- Não modifica código-fonte
- Não altera baselines
- Nunca remove entradas antigas do dev-log
