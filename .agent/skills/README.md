# `skills/` — Procedimentos do agente

Cada skill é um **passo a passo** para um tipo de tarefa. O agente carrega a skill quando a tarefa bate com o gatilho dela (tabela abaixo e campo `description` do frontmatter).

## Organização

```
skills/{skill-name}/SKILL.md
```

Cada `SKILL.md` começa com frontmatter:

```yaml
---
name: <skill-name>            # igual ao nome da pasta
description: <o que faz e QUANDO usar, em uma ou duas frases>
---
```

Arquivos de apoio (modelos, scripts, exemplos) ficam na mesma pasta da skill.

## Skills disponíveis

| Skill | Quando usar |
|-------|-------------|
| [`doc`](./doc/SKILL.md) | Início e fim de toda tarefa da **trilha completa** (`AGENT.md` §3.1): módulo → docs → spec → ativar → concluir → documentar |
| [`tdd`](./tdd/SKILL.md) | Qualquer código novo ou mudança de comportamento |
| [`migration`](./migration/SKILL.md) | Criar ou alterar models; gerar, revisar e aplicar migrações Alembic (SQLite) |
| [`design`](./design/SKILL.md) | Telas e componentes visuais a partir de um protótipo ou imagem de referência, com tokens do tema e componentes `Base*` |
| [`verify`](./verify/SKILL.md) | Verificação ponta a ponta local (backend, frontend, login, fluxos no navegador ou na janela Tauri, evidência) quando um critério de aceite pedir, ao fim de uma série e a pedido |
| [`code-quality`](./code-quality/SKILL.md) | Checklist de DRY, YAGNI e Clean Code (frontend e backend). Complementa a `code-review`: use junto quando a revisão for sobre qualidade de código |
| [`code-review`](./code-review/SKILL.md) | Antes de concluir uma spec, na versão curta da trilha leve e quando o usuário pedir revisão |
| [`spec`](./spec/SKILL.md) | Planejar um módulo ou série e escrever specs no modelo padrão, com checklist de validação |
| [`handbook`](./handbook/SKILL.md) | Documentar um módulo implementado para pessoas em três artefatos (Visão Geral, Especificação de Negócio, Documentação Técnica). Modelos em `handbook/templates/` |

## Contrato

- Skill descreve **como** fazer. **O que** fazer vem da spec, e **onde** colocar vem das `rules/`. Skill não redefine regra.
- Passos numerados, comandos copiáveis e checklist de saída verificável.
- Referencie a spec pela seção (`Spec 02 §6.3`) em vez de copiar o conteúdo dela.
- Skill nova ou alterada → registrar no `AGENT.md` §4 e criar ou ajustar um cenário em `evals/`.
- Exemplos de código nas skills levam comentário explicando o que cada linha importante faz (o usuário é programador iniciante).
- Estas skills vivem em `.agent/` (neutro em relação à ferramenta). O Claude Code as encontra pelo índice do `AGENT.md`, não pela descoberta automática de `.claude/skills/`.
