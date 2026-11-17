# 09 — Ciclo TDD

**Avalia:** `skills/tdd`

## Objetivo
Verificar se o agente escreve o teste **antes**, vê ele falhar pelo motivo certo, escreve o mínimo para passar, refatora e cobre todos os casos da spec.

## Preparação
- Worktree ou clone a partir do `HEAD`, venv do backend ativa.
- Crie `.agent/specs/active/SPEC-01-UTIL-AVALIACAO.md` (módulo `avaliacao`, como no cenário 05) pedindo `calcular_desconto(valor: Decimal, percentual: Decimal) -> Decimal` em `backend-fastapi/app/core/regras_preco.py`, com a tabela de casos:

  | # | Caso | Esperado |
  |---|------|----------|
  | 1 | `100.00`, `10` | `90.00` |
  | 2 | `100.00`, `0` | `100.00` |
  | 3 | percentual `100` | `0.00` |
  | 4 | percentual negativo ou maior que 100 | `ValueError` |
  | 5 | `33.33`, `10` | `29.997` arredondado a 2 casas em **um** ponto: `30.00` |

## Prompt
> Implementa a SPEC-01 que está em `specs/active`.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Listou os casos da spec antes de começar | |
| 2 | Escreveu **um** teste e o rodou **antes** do código, mostrando que falha | [crítico] |
| 3 | A falha era por asserção (ou esqueleto mínimo criado antes), não por erro de import | |
| 4 | Green com o **mínimo** de código; sem antecipar casos futuros | |
| 5 | Fez refactor com os testes verdes e rodou de novo | |
| 6 | Usou `Decimal` (nunca `float`) e arredondou em um só lugar | [crítico] |
| 7 | Todos os 5 casos têm teste correspondente | |
| 8 | Nos ciclos rodou só o arquivo/caso; a suíte completa rodou **uma vez** no fim | |
| 9 | Usou `python -m pytest` (não o atalho da venv) | |
| 10 | Nenhum teste pulado (`skip`) ou apagado para "ficar verde" | [crítico] |
| 11 | Código e testes com comentários em PT-BR explicando cada parte | |

**Máximo:** 22 pontos.
