# Seleção de modelo e economia de tokens

Modelos disponíveis no Claude Code (maio/2026):
| Modelo | Preço API (input/output, $/Mtok) | Quando usar |
|---|---|---|
| Haiku 4.5 | $1 / $5 | Buscas, leitura ruidosa, exploração de legado, sumarização |
| Sonnet 4.6 | $3 / $15 | **Padrão.** Implementação rotineira, refactor, testes |
| Opus 4.7  | $5 / $25 (tokenizer novo usa até 35% + tokens) | Arquitetura, integrador implícito, raciocínio difícil |

Output custa ~5× o input em todos. Cache de prompt corta input em cache em até 90%.

## Política deste projeto (já refletida em settings.json e nos subagentes)
- **Default do agente principal: Sonnet 4.6.** A maior parte do trabalho rotineiro (escrever um
  ConstitutiveModel, um elemento, um teste) é exatamente o terreno em que Sonnet entrega o melhor
  custo/qualidade.
- **Suba para Opus 4.7 só nos momentos arquiteturais:** desenhar o integrador implícito adaptativo,
  o acoplamento primária↔secundária↔terciária, decisões de design que afetam o motor inteiro.
  Use `/model opus` para entrar e `/model sonnet` para voltar.
- **Subagentes em Sonnet ou Haiku** (já está assim no front-matter de `verifier` e `legacy-explorer`):
  - `verifier` em Sonnet — precisa interpretar saída de teste e diagnosticar.
  - `legacy-explorer` em Sonnet — extrai formulação de Matlab/C++; precisa de capacidade real.
  - Se um dia criar um agente só para "ler logs e resumir", use Haiku.

## Como selecionar o modelo (4 formas, em ordem de granularidade)
1. **Por sessão, no prompt:** `/model` abre o seletor; `/model sonnet` ou `/model opus` troca direto.
2. **Padrão do projeto:** `.claude/settings.json` campo `"model"` (já configurado).
3. **Padrão global pessoal:** `~/.claude/settings.json` (sobrescreve por usuário).
4. **Por subagente:** linha `model:` no front-matter do arquivo em `.claude/agents/*.md`.
5. **Por invocação CLI:** `claude --model sonnet` ao abrir.

Verifique o modelo atual com `/model` (sem argumento) e o gasto com `/usage` (mais completo que
`/cost`; mostra também o breakdown por skill, subagente e MCP).

## Plano de assinatura vs API — qual é o seu caso?
- **Pro/Max (claude.ai)**: NÃO existe gasto por token visível para você. Existe janela de 5h rolante
  + cota semanal, COMPARTILHADAS entre claude.ai + Claude Code + Desktop. Opus consome a cota muito
  mais rápido que Sonnet. Estratégia: ficar em Sonnet por padrão, escalar para Opus só pontualmente.
- **API (pay-as-you-go)**: você paga por token. Todas as otimizações abaixo se aplicam diretamente.

Independente do modo, as práticas de economia abaixo valem.

## 12 práticas que cortam tokens (em ordem de retorno sobre esforço)

### 1. Plan mode antes de tarefa nova (Shift+Tab ×2)
Plan mode é read-only: o agente pesquisa e propõe SEM executar ferramentas de edição. Você revisa o
plano (barato) antes de aprovar a execução (cara). Corrigir um plano custa 1, corrigir um diff
inflado custa 10.

### 2. `@arquivo` em vez de deixar o agente procurar
`@main/elements/Element.hpp` injeta o arquivo direto. Sem `@`, o agente usa Glob+Grep+Read em loop
até achar — tokens jogados fora. Funciona com PDFs também.

### 3. `/clear` entre tarefas não relacionadas; `/compact` em sessões longas
Cada turno reenvia TODO o contexto acumulado para o modelo. Uma sessão de 2h sem `/clear` está
pagando pela conversa inteira em cada mensagem. `/compact` resume o histórico em poucos tokens.

### 4. Subagentes para trabalho "barulhento"
`verifier` e `legacy-explorer` rodam em janela ISOLADA. Logs de teste, leituras grandes de legado e
buscas voltam para o agente principal só como resumo. Sem eles, esse barulho fica no contexto
principal e é cobrado em cada turno subsequente. **Observação:** subagentes paralelos custam tokens
adicionais (cada um mantém contexto próprio); não abuse — use só quando o isolamento compensa o overhead.

### 5. CLAUDE.md curto e enxuto (sempre carregado → sempre cobrado)
O CLAUDE.md deste projeto tem ~130 linhas. Toda linha lá é paga em CADA turno de CADA sessão. Por
isso a bibliografia bruta vai para `docs/references/` e só conteúdo distilado vai para `docs/*.md`,
carregado sob demanda. Cache de prompt ajuda bastante aqui: o CLAUDE.md, que não muda, costuma cair
no cache (90% de desconto no input cacheado).

### 6. Um pedido grande > vários pequenos
"Implemente X, escreva o teste, rode o verifier" em uma mensagem reenvia o contexto uma vez. Quebrar
em três mensagens reenvia três vezes. Mas: pedidos grandes precisam estar BEM especificados — daí o
valor do plan mode no passo 1.

### 7. Limite `--max-turns` em automações
Se rodar Claude Code em CI ou em loop, `--max-turns N` evita o agente entrar em ciclo de
auto-correção tentando passar um teste que tem bug.

### 8. Diff focado em vez de "limpe o arquivo todo"
Peça mudanças cirúrgicas (`str_replace` em vez de regenerar). Reescrever um arquivo de 500 linhas
para mudar 3 ainda dá ~500 linhas de output — pago a $25/Mtok no Opus.

### 9. Extended thinking só quando vale
Pensamento estendido (a versão "raciocínio profundo") consome tokens de thinking que entram na
conta. Vale para a Etapa 0 (arquitetura) e o integrador implícito; não vale para escrever um teste
unitário. No Claude Code, comandos como `/effort low|medium|high` controlam esse esforço — use low
em tarefas mecânicas.

### 10. Não rode `/init` com CLAUDE.md já pronto
`/init` lê o repo inteiro para GERAR o CLAUDE.md. Caro e desnecessário no seu caso (você já tem o
seu). Já avisado no CLAUDE.md.

### 11. Desligue MCP/skills não usadas
Cada servidor MCP conectado aumenta o system prompt. Se não vai usar agora, desabilite.

### 12. Verifique o gasto periodicamente
`/usage` mostra o breakdown da sessão e da semana (se em plano de assinatura). É barato e dá hábito
de hipótese-verifica-ajusta.

## Fluxo típico de uma sessão neste projeto
```
abrir:       claude            # Sonnet por default (via settings.json)
1ª ação:     Shift+Tab×2       # entrar em plan mode
prompt:      "Em plan mode: ..."
revisar plano, sair do plan (Shift+Tab até Normal)
trabalhar:   ficar em Sonnet enquanto for implementação
escalada:    /model opus       # SÓ se bater num ponto arquitetural duro
                              # ex.: desenhar o esquema de Crank-Nicolson coupling
voltar:      /model sonnet     # assim que sair da decisão difícil
verificar:   chamar @verifier   # subagente roda em Sonnet, contexto isolado
fim:         /usage             # checar gasto, /clear antes da próxima tarefa
```

## Quando o ganho de Opus compensa
Use Opus quando o erro custaria muito mais tempo de retrabalho do que o token a mais. Casos típicos
neste projeto: arquitetura inicial (Etapa 0), integrador implícito adaptativo, decisões de
acoplamento, e debug de teste que falha por motivo não óbvio. Para escrever uma subclasse de
`ConstitutiveModel` cuja equação já está em `docs/`, Sonnet é igual ou melhor (mais rápido, menos
verboso, mais barato).
