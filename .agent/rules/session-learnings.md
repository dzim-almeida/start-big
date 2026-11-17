# Regra — Registro de aprendizados da sessão

**Status:** obrigatória · **Quando:** ao final de toda sessão de implementação, e na hora em que um aprendizado importante acontecer (não deixe para o fim se a sessão puder ser interrompida).

O objetivo é que a **próxima sessão não repita o mesmo erro nem refaça a mesma investigação**. A skill `doc` obriga a leitura do índice de `learn/` (`learn/README.md`) no início de toda tarefa, e a dos aprendizados que a tarefa toca. Por isso, cada entrada precisa valer o custo de ser lida, e a linha dela no índice precisa dizer quando abri-la.

---

## 1. Onde registrar

| Aprendizado vale para... | Pasta |
|--------------------------|-------|
| Um módulo | `@/docs/{módulo}/learn/` (ex.: `@/docs/customers/learn/`) |
| Vários módulos ou o projeto todo (ferramentas, Windows, Tauri, venv, testes) | `@/docs/_shared/learn/` |

Se `@/docs/{módulo}/learn/` não existir, crie a pasta (com o `README.md` de índice, modelo em `@/docs/_modelo/learn/README.md`).

---

## 2. O que é "importante" (critério de entrada)

Registre **somente** se responder "sim" a pelo menos uma pergunta **e** não for possível deduzir o conteúdo lendo o código, a spec ou o `CLAUDE.md`:

- Custou tempo relevante para descobrir (erro enganoso, bug de ambiente, comportamento inesperado de biblioteca)?
- Uma decisão foi tomada com o usuário e não está na spec (ou contraria a spec)?
- Existe uma armadilha que a próxima sessão provavelmente cairia de novo?
- Um padrão foi validado com o usuário e deve ser repetido?

**Não registre:**
- O que já está na spec, nas regras, no `CLAUDE.md` ou no código (ex.: "o dev usa a porta 8000").
- Histórico do que foi feito (isso vai para o `CHANGELOG.md` do módulo).
- Passos óbvios, opiniões sem confirmação ou suposições não testadas.
- Segredos, caminhos de banco de cliente, tokens, CPF/CNPJ ou dados pessoais.

Na dúvida entre registrar ou não: **não registre**. Uma pasta `learn/` enxuta é lida com atenção. Uma pasta inchada é ignorada.

---

## 3. Formato

Um arquivo por aprendizado: `AAAA-MM-DD-slug-curto.md` (ex.: `2026-11-17-sqlite-alter-table-em-lote.md`).

```markdown
# <Título em uma linha, afirmativo>

- **Data:** AAAA-MM-DD
- **Módulo:** customers | _shared
- **Spec relacionada:** SPEC-XX (se houver)
- **Tipo:** armadilha | decisão | padrão validado | ambiente

## Contexto
O que estava sendo feito quando isso apareceu (2–3 linhas).

## Aprendizado
O fato, a regra ou a decisão. Direto ao ponto.

## Como aplicar
O que a próxima sessão deve fazer (ou evitar) na prática.
```

Tamanho alvo: menos de 20 linhas. Escreva para quem está começando: explique o termo técnico na primeira vez que ele aparece.

**Índice obrigatório.** Todo aprendizado novo ganha uma linha em `learn/README.md` da mesma pasta (crie o índice, se não existir, no formato de `@/docs/_shared/learn/README.md`): título com link, **área** (backend, frontend, testes, Tauri, Windows, ambiente do agente...) e **quando abrir** (a situação concreta em que ele importa). Aprendizado fora do índice não é lido.

---

## 4. Manutenção

- Antes de criar, **procure** em `learn/` por um aprendizado parecido. Se existir, atualize esse arquivo em vez de duplicar.
- Se um aprendizado ficar errado ou obsoleto (ex.: a biblioteca corrigiu o bug), **atualize ou apague** o arquivo e mencione isso no resumo final ao usuário.
- Se um aprendizado virar regra permanente, proponha ao usuário movê-lo para `@/rules/`, para a skill do assunto (ex.: armadilhas de teste na `tdd` §5) ou para o `CLAUDE.md`. Aprovado: apague o arquivo, tire a linha do índice, registre o destino na tabela "Promovidos" do índice e corrija as referências ao arquivo (`grep -rn "<nome-do-arquivo>" .agent`).
- Ao atualizar ou apagar um aprendizado, atualize também a linha dele no índice.

---

## 5. Encerramento da sessão

No resumo final ao usuário, liste os aprendizados criados, atualizados ou removidos (caminho + título). Se nenhum, diga "Nenhum aprendizado novo".
