---
name: spec
description: Planeja um módulo ou uma série nova e escreve as specs do StartBig, do pedido do usuário ao acordo de decisões numeradas, ADR quando uma premissa muda, specs no modelo padrão, índice e roteiro. Inclui o checklist que valida cada spec contra o código e as regras antes de entregá-la. Use ao planejar uma funcionalidade nova ou revisar uma spec.
---

# Skill `spec` — do pedido às specs

> Caminhos com `@/` são relativos a `.agent/`.

## 0. Princípios

- A spec diz **o que** fazer, com as decisões já fechadas. Quem implementa não deveria precisar escolher nada.
- **O agente propõe, o usuário decide.** Toda escolha vem com uma recomendação e o motivo. Pergunta em lote pequeno, nunca uma lista de vinte.
- **Uma spec por vez:** escreva, entregue, espere a aprovação e só então escreva a próxima. A aprovação de uma spec pode mudar as seguintes.
- Planejar não é implementar. Nenhum código de produção nesta skill. Um teste descartável no scratchpad para conferir o comportamento de uma biblioteca é permitido (§4).
- A spec é em PT-BR, **e os exemplos de código também** (`AGENT.md` §7), **sempre comentados** para quem está começando.
- Por que esta skill existe: boa parte das correções de spec vem de erro evitável (arquivo esquecido, conflito com regra, caminho errado, limitação de biblioteca). O checklist da §4 existe para barrar isso **antes** da implementação.

## 1. Entradas

Leia antes de propor qualquer coisa:

| Fonte | Para quê |
|-------|----------|
| O pedido do usuário (e anexos: PDF, imagem, protótipo) | Objetivo, usuários e o que fica fora |
| `@/docs/{módulo}/README.md` | Visão do módulo, quando houver. É do time: o agente só **propõe** mudanças nele |
| `@/docs/{outro}/SUMMARY.md` dos módulos tocados | O que já existe e o contrato que outros módulos consomem |
| `@/rules/` | Arquitetura, contrato da API, convenções. A spec não pode contrariá-las sem decisão explícita |
| `CLAUDE.md` | Portas, sidecar, banco, papel da máquina |
| Código atual | Os arquivos que a spec vai alterar, abertos de verdade, não supostos |

Sem pedido claro: pergunte o objetivo, os usuários e o que fica fora. Não invente escopo.

## 2. Fluxo

### 2.1. Levantar os fatos do sistema

Antes de decidir, descubra no **código**: quais models, services, endpoints e telas já existem para o assunto; quais permissões o cargo usa; que módulos já tratam algo parecido. Anote com `arquivo:linha`.

### 2.2. Acordo de decisões

Para uma série (várias specs) ou decisões não triviais, escreva `@/docs/{módulo}/ACORDO.md`:

```markdown
# Acordo — <módulo>

## 1. Contexto
### 1.1. Material lido
### 1.2. Fatos do sistema que moldaram as decisões
## 2. Decisões            (numeradas e agrupadas: arquitetura, segurança, regras de negócio, contrato da API, frontend)
## 3. Consequências       (o que cada decisão muda em telas, fluxos e dados)
## 4. Endpoints e códigos de erro
## 5. Mapeamento das specs (ordem, arquivo, camada, conteúdo, depende de)
## 6. Pontos pendentes
## 7. Fora do escopo (registrado)
```

Cada decisão: `D-NN`, a escolha, o motivo e a alternativa descartada. O usuário aprova o acordo **antes** de qualquer spec.

### 2.3. ADR, quando uma premissa muda

Se uma decisão contraria o `AGENT.md`, uma regra, o `CLAUDE.md` ou o comportamento de um módulo já implementado, escreva `@/docs/{módulo}/adr/ADR-NNN-TITULO.md` com contexto, decisão, consequências, alternativas descartadas e como reverter. Aprovada a ADR, proponha na mesma tarefa a atualização do `AGENT.md` ou da regra afetada.

### 2.4. Dividir em specs

- Uma spec por **camada** (backend e frontend separados) e por **entrega testável**.
- Componente base novo vai para uma spec própria de UI (`@/specs/components/`), não para a spec da tela.
- Mudança no contrato de outro módulo é spec **desse** módulo.
- Spec que altera model leva migração explícita (skill `migration`).
- Ordene pelas dependências. Nome: `SPEC-NN-TEMA-MODULO.md`.

### 2.5. Escrever cada spec

Use o modelo da §3, rode o checklist da §4 e entregue ao usuário com as perguntas que sobraram. Só depois da aprovação passe à próxima.

### 2.6. Índice, docs e registro do módulo

- `@/specs/{módulo}/README.md`: mapa (spec, arquivo, camada, situação, entrega), dependências (diagrama `mermaid`), endpoints com a seção de cada spec e referências. Modelo: `@/specs/_modelo/README.md`.
- Módulo novo: linha em `@/specs/README.md`; pasta `@/docs/{módulo}/` a partir de `@/docs/_modelo/` (com `README.md` e `learn/`, contrato de `@/docs/README.md`).

### 2.7. Roteiro, quando a série cruza módulos

`@/specs/{módulo}/ROTEIRO-IMPLEMENTACAO.md`:

- tabela de passos (spec, módulo da skill `doc`, camada, depende de, skills);
- por passo: pontos de atenção, perguntas que precisam de resposta antes de implementar e "**Pronto quando:** N casos passam e ...";
- **verificação final ponta a ponta:** fluxos e resultado esperado, executados com a skill `verify`;
- branches e entrega (`AGENT.md` §7: uma branch por série).

## 3. Modelo da spec

```markdown
# <Módulo> NN — <Título>

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend (FastAPI) · ou Frontend (Vue 3 + TypeScript) |
| Dependências | <specs> |
| Bloqueia     | <specs> |
| Referência   | [acordo](...) decisões N, M; [ADR-NNN](...); design/protótipo <arquivo> |

## 1. Objetivo
## 2. Escopo
**Dentro do escopo** · **Fora do escopo** (com onde ficou registrado)
## 3. Arquivos afetados
| Arquivo | Ação (criar · alterar · remover) | O quê |
## 4. Contrato da API          (backend: rotas, corpos, respostas, erros por ação)
   ou Contrato consumido       (frontend: endpoints e códigos de erro que a tela trata)
## 5. Schemas
## 6. Especificação técnica    (uma subseção por arquivo ou função, com o trecho esperado, comentado)
## 7. Decisões desta spec      (numeradas, com o motivo)
## 8. Ajustes em outras specs  (notas de revisão a aplicar, se houver)
## 9. Critérios de aceite      (checkbox, cada um verificável por teste, comando ou inspeção)
## 10. Casos de teste          (por arquivo de teste, numerados)
```

Spec de frontend acrescenta, antes do contrato: **Inventário do design** (o que a referência mostra e o que é sobra), **Estrutura de arquivos**, **Rota e navegação**; e, depois dos schemas: **Dados** (service, consultas), **Componentes**, **Ações e erros** (status da API → mensagem na tela).

- **Status:** `Backlog` → `Em andamento (desde AAAA-MM-DD)` → `Concluída (AAAA-MM-DD) — revisão N` (skill `doc`).
- **Revisões** entram no topo, abaixo do cabeçalho: `> **Revisão N (AAAA-MM-DD) — <tema> (<origem>):** ...`. Spec aprovada nunca é editada em silêncio (`@/specs/README.md`).

## 4. Checklist antes de entregar a spec

- [ ] **Arquivos afetados conferidos no código.** Abra cada arquivo. Para cada símbolo renomeado ou alterado, `grep` em `app/`, `test/`, `alembic/env.py`, `run.spec` e `frontend/src/` atrás de quem mais o usa.
- [ ] **Testes existentes que a mudança quebra** listados, com o que fazer com cada um.
- [ ] **Exemplos de código em PT-BR e comentados** (o usuário é iniciante).
- [ ] **Aderência às regras:** camadas (`backend-architecture`, `frontend-architecture`), isolamento por `empresa_id`, `api-contract` (rotas, status, paginação, erros) e padrões de teste da skill `tdd`.
- [ ] **Comportamento de biblioteca conferido** quando a spec depende dele. Na dúvida, um teste descartável no scratchpad.
- [ ] **Links e caminhos existem** (`ls` em cada um).
- [ ] **Migração prevista** quando há model novo/alterado, decidindo pelo schema antigo (`migration` §1.5).
- [ ] **Sidecar:** a spec de backend lembra de regerar o sidecar na entrega.
- [ ] **Nada "a critério da implementação".** Toda escolha tem recomendação fechada ou vira pergunta ao usuário antes da entrega.
- [ ] **Textos de tela exatos** (da referência ou aprovados) e **exemplos fictícios**, nunca dados de uma pessoa ou cliente real.
- [ ] **Critérios de aceite verificáveis nesta máquina** (Windows, backend 8000, Vite 1420). Fluxo que só se vê no navegador fica marcado para a skill `verify`.
- [ ] **Casos de teste numerados**, cobrindo erros, limites, permissão, isolamento por empresa (todo recurso de negócio) e concorrência quando há regra de corrida (ex.: dois caixas, estoque).
- [ ] **Dependências e "Bloqueia"** coerentes com o índice e com o acordo.
- [ ] **Regras fiscais ou financeiras** citam a fonte (legislação, documento do usuário) em vez de suposição.

## 5. Saída para o usuário

```markdown
### Spec <id> — pronta para revisão
- Arquivo: <caminho>
- Decisões do acordo cobertas: <números>
- Perguntas antes da aprovação: <lista, cada uma com a recomendação>
- Checklist §4: ok · ou <item> pendente porque <motivo>
- Próxima spec da série: <id>
```
