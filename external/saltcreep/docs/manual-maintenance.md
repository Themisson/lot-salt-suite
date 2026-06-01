# Manutenção do manual HTML (docs/index.html)

O manual técnico é um único arquivo HTML5 autocontido em `docs/index.html`. Ele DEVE ser
atualizado sempre que o código muda. No Claude Code, use o subagente `docs-sync`. No Codex
(ou manualmente), siga este guia.

## Filosofia
O manual é a face pública do projeto e a referência de onboarding. Documentação desatualizada é
pior que nenhuma — então a regra é: **toda etapa que adiciona/altera uma classe pública, um
elemento, um modelo, uma envoltória, ou o schema YAML, atualiza o manual no MESMO ciclo de
trabalho**, antes do commit final.

## Estrutura do arquivo
O HTML tem três partes: `<style>` (CSS, topo), o corpo (`<aside>` sidebar + `<main>` conteúdo),
e `<script>` (JS, fim). Você quase sempre edita só o corpo.

Seções do corpo (cada uma é `<section id="...">`):
| id | conteúdo | quando atualizar |
|---|---|---|
| `#overview` | visão geral | mudança de escopo/objetivo |
| `#architecture` | 3 interfaces, pipeline, layout | nova interface ou mudança estrutural |
| `#physics` | invariantes | novo invariante físico |
| `#interfaces` | cards das 3 interfaces | mudança de contrato |
| `#elements` | tabela + cards de elementos | NOVO ELEMENTO |
| `#constitutive` | cards de modelos | NOVO MODELO ou ENVOLTÓRIA |
| `#thermal` | cards de campos térmicos | NOVO CAMPO TÉRMICO |
| `#solver` | cards do motor | nova classe de infraestrutura |
| `#io` | CaseParser, saltpost | mudança de I/O |
| `#input` | exemplo YAML anotado | MUDANÇA DE SCHEMA |
| `#builder` | construtor interativo | MUDANÇA DE SCHEMA (form + JS) |
| `#build` `#run` | compilação/execução | novo comando ou dependência |
| `#post` | saltpost | nova funcionalidade de pós |
| `#verify` | protocolo + contagem | NOVA CONTAGEM DE TESTES |

## Tarefas comuns

### 1. Adicionar um elemento novo (ex.: AQ9)
Dois lugares na seção `#elements`:
- **Tabela:** adicione `<tr>` com nome, nós, ordem, integração, taxa de convergência (busque a
  taxa real em `docs/elements.md`).
- **Card:** adicione um `<div class="card">` com tag `elem`, seguindo o padrão dos outros.

### 2. Adicionar um modelo constitutivo (ex.: Wang 2004)
Na seção `#constitutive`, novo card com tag `const`:
- "Física" com a equação (entidades HTML: `ε̇` = `&epsilon;&#775;` ou use o texto `ε̇` direto
  que já funciona no arquivo; `σ` = `σ`; `√` = `√`).
- "Implementação" com a flag YAML que o ativa e detalhes.

### 3. Adicionar envoltória de dilatância (ex.: Ratigan)
Na seção `#constitutive`, dentro/perto do card MottaV1, ou subseção própria se houver várias.
Atualize também o `<select>` do construtor em `#builder` se a envoltória for selecionável.

### 4. Atualizar contagem de testes
Quatro lugares (busque o número exato no dev-log):
- `<span class="ver">v1.0 · XX testes C++ · Y testes Py</span>` (sidebar)
- `<div class="n coppc">72</div>` (stat na hero — o último stat)
- Seção `#verify`, nota "Estado atual": "XX testes C++ + Y testes Python"
- Footer: `<span class="mono">XX testes C++ · Y testes Python</span>`

### 5. Mudar o schema YAML
Dois lugares:
- Seção `#input`: o `<pre>` com o exemplo anotado completo.
- Seção `#builder`: o formulário (`builder-form`) e a função JS `genYAML()` que monta o YAML.
  Se adicionar um campo, adicione o input no form, o id no array `ids`, e a linha no template
  de `genYAML()`.

## Padrão de card (copiar exatamente)
```html
<div class="card" data-name="NomeClasse termos de busca">
  <div class="card-head">
    <span class="ctag TIPO">rótulo</span><span class="cname">NomeClasse</span>
    <span class="file">caminho/arquivo</span><span class="chev">▶</span>
  </div>
  <div class="card-body">
    <p class="role">O que faz</p>
    <p>...</p>
    <p class="role">Implementação</p>
    <p>...</p>
  </div>
</div>
```
- `data-name` alimenta busca futura; inclua palavras-chave.
- Tipos de tag (classe CSS + cor): `iface` (teal), `elem` (cobre), `const` (roxo),
  `therm` (laranja), `solver` (verde), `io` (cinza).
- Primeiro card de uma seção pode ter classe `card open` para já vir expandido.

## Highlight de código
Dentro de `<pre><code>`, use spans:
- `<span class="tok-k">` keyword/bool (laranja)
- `<span class="tok-t">` tipo/classe (verde-água)
- `<span class="tok-c">` comentário (cinza itálico)
- `<span class="tok-s">` string (dourado)
- `<span class="tok-n">` número (vermelho-suave)
- `<span class="tok-f">` função (azul)

Inline: `<code class="ic">texto</code>`.

## Validação antes de fechar
1. Tags balanceadas: cada `<div class="card">` tem seu `</div>` (são 2 divs internas + 1 externa).
2. A seção nova aparece na sidebar `<nav>`? Se criou uma seção nova, adicione o link.
3. Símbolos matemáticos renderizam (teste abrir no navegador se possível).
4. O construtor interativo ainda gera YAML válido (se mexeu no `#builder`).

## NÃO fazer
- Não adicionar dependências externas (o manual é offline-first; só fontes do Google).
- Não usar localStorage/sessionStorage (não funciona em alguns contextos).
- Não inventar números — taxa, contagem, parâmetros vêm do código/docs.
- Não quebrar a responsividade (não adicionar larguras fixas grandes).
