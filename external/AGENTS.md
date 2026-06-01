# AGENTS.md — external/

## PROIBIDO MODIFICAR OU DUPLICAR

`external/saltcreep/` é a referência técnica moderna para modelos de sal.

## Uso autorizado

- Leitura para entender interfaces e padrões arquiteturais
- Referência para `include/salt/SaltCreepInterface.hpp`
- Referência para padrões de YAML, factory, e docs/index.html

## Uso proibido

- Editar qualquer arquivo em external/saltcreep/
- Copiar código de external/saltcreep/src/ para src/salt/
- Duplicar modelos constitutivos do saltcreep no projeto novo

## Integração correta

Use `SaltCreepSaltcreepAdapter` em `include/salt/`
que referencia os modelos do saltcreep por interface.
Ver skill `lot-salt-integration` para protocolo completo.
