---
name: doc
description: Fluxo obrigatório para começar e terminar as tarefas da trilha completa do StartBig (AGENT.md §3.1). Localiza o módulo em .agent/docs, lê aprendizados, escolhe e ativa a spec em .agent/specs, e ao final move a spec para completed e atualiza SUMMARY.md e CHANGELOG.md do módulo. Use no início de toda tarefa da trilha completa e ao concluir qualquer spec. Tarefas da trilha leve seguem o AGENT.md §3.2.
---

# Skill `doc` — ciclo de vida da tarefa, das specs e da documentação

> Caminhos com `@/` são relativos a `.agent/`.
>
> Esta skill é a **trilha completa** (`@/AGENT.md` §3.1). Correções pontuais, ajustes e perguntas seguem a trilha leve (§3.2) e não passam por aqui.

## Visão geral

```
intenção do usuário
   │
   ▼
[1] identificar módulo ──► [2] ler @/docs/{módulo} ──► [3] escolher spec em @/specs/{módulo}
                                                              │
                                                              ▼
[7] documentar ◄── [6] concluir spec ◄── [5] implementar ◄── [4] ativar spec (@/specs/active)
```

---

## 1. Identificar o módulo

- Mapeie a intenção para um módulo (tabela do `@/AGENT.md` §1): `customers`, `sales`, `fiscal`, `order-service`...
- Se a tarefa tocar mais de um módulo, o módulo **principal** é o da spec. Os outros entram como "módulos afetados" no CHANGELOG.
- Se não der para decidir com segurança, **pergunte** antes de ler specs.
- Se o módulo ainda não existir em `@/docs/` nem em `@/specs/`, é a **primeira tarefa dele no Harness**: crie as pastas a partir de `@/docs/_modelo/` e `@/specs/_modelo/`, e pergunte se o usuário quer escrever uma spec primeiro (skill `spec`) ou seguir sem spec (e registre a decisão).

## 2. Carregar o contexto do módulo (`@/docs/{módulo}/`)

Leia, nesta ordem:

1. `SUMMARY.md` — o que já está implementado (se existir).
2. `README.md` — visão geral e decisões de arquitetura do módulo. Liste os cabeçalhos (`grep -n "^#" README.md`) e leia só as seções que a tarefa toca. Leitura inteira só na primeira tarefa de um módulo novo. Pasta `archive/` só quando a tarefa pede o histórico de uma decisão.
3. `CHANGELOG.md` — as 3–5 entradas mais recentes (se existir).
4. Os índices `learn/README.md` do módulo e de `@/docs/_shared/learn/`, **inteiros**, e depois **todo** aprendizado cuja coluna "Quando abrir" bate com a tarefa. Eles registram armadilhas já conhecidas: ignorá-los é repetir erro. Na dúvida se um aprendizado se aplica, abra. Pasta `learn/` sem índice: leia todos os arquivos dela e proponha criar o índice (`@/rules/session-learnings.md` §3).
5. `CLAUDE.md` da raiz — só as seções que a tarefa toca (portas, sidecar, banco, papel da máquina).

## 3. Escolher a spec (`@/specs/{módulo}/`)

1. **Olhe `@/specs/active/` primeiro**, listando a pasta de forma explícita (ex.: `ls .agent/specs/active`). Um Glob amplo em `specs/**` não conta. Diga ao usuário o resultado antes de escolher a spec: "`specs/active/` está vazia" ou "`specs/active/` tem a SPEC-XX". Se houver uma spec lá:
   - Se for a da tarefa, retome-a (leia a seção "Progresso" que você mesmo deixou, ver passo 5).
   - Se for outra, **pare e pergunte** ao usuário: concluir a ativa, pausar (voltar para o backlog) ou manter as duas. A regra padrão é **uma spec ativa por vez**.
2. Abra `@/specs/{módulo}/README.md` (índice). Use as tabelas de roteamento para achar a spec e a seção certas, e a seção "Dependências e ordem de implementação".
3. Confira se as dependências da spec escolhida estão em `@/specs/{módulo}/completed/`. Se não estiverem, avise o usuário antes de continuar.
4. Leia a spec **inteira**, incluindo "Critérios de aceite" e "Casos de teste".

## 4. Ativar a spec

1. Mova o arquivo:
   ```bash
   git mv .agent/specs/{módulo}/SPEC-XX-....md .agent/specs/active/
   ```
   (Use `mv` se o arquivo ainda não estiver versionado.)
2. No cabeçalho da spec, atualize o campo `Status` para `Em andamento (desde AAAA-MM-DD)`.
3. **Atualize os links** que apontam para o arquivo no índice `@/specs/{módulo}/README.md` (e em outras specs, se houver) para `../active/SPEC-XX-....md`. Confira com:
   ```bash
   grep -rn "SPEC-XX" .agent/specs .agent/docs
   ```

## 5. Implementar

- Siga `@/rules/frontend-architecture.md` e/ou `@/rules/backend-architecture.md`, e `@/rules/api-contract.md` se houver endpoint.
- Carregue as skills conforme a necessidade:
  - `tdd` — sempre que houver comportamento novo;
  - `migration` — se a spec criar ou alterar models;
  - `design` — se a spec tiver tela ou componente visual;
  - `verify` — se um critério de aceite pedir verificação no navegador; numa série, também ao concluir a última spec (verificação final do roteiro).
- **Divergência da spec** (algo impossível, ambíguo ou errado): pare e pergunte **antes** de editar, nunca depois. Também é divergência:
  - precisar criar ou alterar **código de produção** fora de "Arquivos afetados": outro módulo, `core/` ou `shared/`, contrato da API (rota, status, formato de erro, campo), model ou migração, dependência, autenticação, permissões, isolamento por empresa, regra fiscal ou financeira;
  - a spec conflitar com uma regra de `@/rules/` ou do `AGENT.md`.

  Não resolva o conflito sozinho, mesmo que a resposta pareça óbvia. Depois da decisão, registre na própria spec como nota de revisão (`> **Revisão N (AAAA-MM-DD):** ...`) e, se atender ao critério, em `learn/`.
- **Arquivos de apoio fora da lista** seguem sem parar: testes, fixtures e helpers de teste; índices e re-exports do mesmo módulo; tipos e constantes usados só pelos arquivos da spec, no mesmo módulo; docs do módulo e da própria spec. Registre cada um na seção "Progresso" (`Fora da lista: <arquivo> — <motivo>`), leve para a nota de revisão ao concluir e cite no resumo final.
- **Sessão longa ou interrompida:** mantenha no fim da spec ativa uma seção temporária:
  ```markdown
  ## Progresso (temporário — remover ao concluir)
  - [x] Item feito
  - [ ] Próximo passo
  - Bloqueios: ...
  ```

## 6. Concluir a spec

Uma spec só é concluída quando **todos** estes itens forem verdadeiros:

- [ ] Todos os "Critérios de aceite" marcados, cada um verificado de fato (teste, comando ou inspeção).
- [ ] Todos os "Casos de teste" da spec implementados e passando, com a verificação completa rodada **uma vez** depois da última mudança de código (skill `tdd` §6).
- [ ] Verificação ponta a ponta (skill `verify`) feita e relatada, quando um critério de aceite pedir o navegador. Numa série, os outros fluxos com tela entram na verificação final do roteiro, que roda ao concluir a última spec.
- [ ] Skill `code-review` executada sobre o diff, sem achados bloqueantes abertos.
- [ ] Seção "Progresso" temporária removida.
- [ ] Mexeu em `backend-fastapi/app/`? Usuário avisado de que o sidecar precisa ser regerado.

Então:

1. Atualize o `Status` para `Concluída (AAAA-MM-DD)`.
2. Mova para `completed/` e ajuste os links (mesmo procedimento do passo 4):
   ```bash
   git mv .agent/specs/active/SPEC-XX-....md .agent/specs/{módulo}/completed/
   ```
   No índice, o link passa a ser `./completed/SPEC-XX-....md`. **Atenção:** a spec fica um nível mais funda; links dela para `docs/` e `rules/` precisam de `../../../` (confira com `grep -n "](\.\./" <spec>`).

Se um critério não puder ser cumprido, a spec **não** é concluída: continua em `active/` e o bloqueio é informado ao usuário. Mesmo assim, antes de encerrar a sessão, rode a skill `code-review` sobre o diff e entregue a saída **no formato dela**, para o usuário decidir sobre o bloqueio com o código já revisado.

## 7. Documentar o módulo (`@/docs/{módulo}/`)

Ao concluir cada spec, acrescente a entrada no `CHANGELOG.md` (ela entra no commit da spec). O `SUMMARY.md` é reescrito ao concluir uma spec avulsa ou a **última** spec de uma série: nas specs do meio da série, não mexa nele. Crie os dois a partir dos modelos de `@/docs/_modelo/`, se não existirem. **Não altere o `README.md` do módulo** (ele é mantido pelo time). Se algo nele ficou desatualizado, proponha a mudança ao usuário.

### 7.1. `SUMMARY.md` — o estado atual do módulo (reescrito, não acumulado)

```markdown
# <Módulo> — Resumo da implementação

_Última atualização: AAAA-MM-DD (SPEC-XX)_

## O que está pronto
| Área | Entrega | Spec |
|------|---------|------|
| Backend | POST /clientes/ | 04 |

## Arquivos principais
- `backend-fastapi/app/services/cliente/cadastro.py` — regras de cadastro
- ...

## Como usar / integrar
Pontos de entrada que outros módulos ou telas consomem (endpoints, stores, composables).

## Pendências conhecidas
- Itens adiados, dívidas técnicas e decisões em aberto.
```

### 7.2. `CHANGELOG.md` — histórico (acumulado, mais recente no topo)

```markdown
# <Módulo> — Histórico de alterações

## AAAA-MM-DD — SPEC-XX <título curto>
**Módulos afetados:** customers (, sales...)
### Adicionado
- ...
### Alterado
- ...
### Corrigido
- ...
### Decisões
- Desvio da spec X porque Y (aprovado pelo usuário).
```

### 7.3. Aprendizados

Aplique `@/rules/session-learnings.md`.

### 7.4. Handbook do módulo (sugestão)

Ao concluir uma spec avulsa ou a **última** spec de uma série que mudou o comportamento do módulo, **sugira** ao usuário rodar a skill `handbook` para criar ou atualizar os três artefatos do módulo. A skill não roda sem o pedido dele e não é condição para concluir a spec.

## 8. Resumo final ao usuário

Em linguagem simples (o usuário é iniciante):

- Spec trabalhada e status final (ativa / concluída).
- O que foi verificado e como (comandos executados e resultado).
- Documentação atualizada (caminhos).
- Aprendizados registrados.
- Próxima spec sugerida pela ordem de dependência.
- No fim de uma série ou de uma spec avulsa: a sugestão do handbook (§7.4).
