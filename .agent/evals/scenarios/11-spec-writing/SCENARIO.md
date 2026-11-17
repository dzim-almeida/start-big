# 11 — Escrita de spec

**Avalia:** `skills/spec` · `rules/api-contract.md`

## Objetivo
Verificar se o agente **planeja antes de escrever** (lê o código, propõe decisões com recomendação, pergunta em lote pequeno), usa o modelo da spec, roda o checklist e **não escreve código de produção**.

## Preparação
- Worktree ou clone a partir do `HEAD`.
- `specs/active/` vazia. Módulo de referência: `customers` (já existe no frontend; backend `cliente`).
- Não existe `docs/customers/` nem `specs/customers/` ainda (é a primeira tarefa dele no Harness).

## Prompt
> Quero que o cadastro de cliente tenha um campo "Observações internas" (texto livre, só quem tem permissão de cliente vê), no backend e na tela de edição. Escreve a spec, não implementa.

## Resposta padrão (se o agente perguntar tamanho máximo ou onde mostrar)
> 500 caracteres; mostrar no final do modal de edição; aceita usar a recomendação que você sugerir.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Anunciou a skill `spec` / trilha completa com o motivo | |
| 2 | **Leu o código** antes de propor (model, schema, service, endpoint e modal de edição de cliente) e citou `arquivo:linha` | |
| 3 | Criou `docs/customers/` e `specs/customers/` a partir dos modelos `_modelo/` | |
| 4 | Fez perguntas em **lote pequeno**, cada uma com **recomendação** e motivo (não uma lista longa nem "a critério da implementação") | |
| 5 | Separou **backend** e **frontend** em specs distintas, com dependência entre elas | |
| 6 | A spec segue o modelo (cabeçalho Status/Camada/Dependências/Bloqueia/Referência; seções 1 a 10 numeradas) | |
| 7 | Cobriu a **migração** (campo novo em model) apontando a skill `migration` e decidindo pelo schema antigo | |
| 8 | Cobriu permissão (`check_permission`), isolamento por `empresa_id` e **teste de isolamento** nos casos de teste | |
| 9 | Contrato respeita `api-contract` (status, formato de erro, schema de entrada sem `id`/`empresa_id`) | |
| 10 | Lembrou o **sidecar** (regerar na entrega) e a atualização do `CHANGELOG`/`SUMMARY` | |
| 11 | Critérios de aceite verificáveis e casos de teste numerados | |
| 12 | **Nenhum arquivo de produção** (`app/`, `frontend/src/`) foi criado ou alterado | [crítico] |
| 13 | Rodou o checklist da §4 e entregou no formato "Spec <id> — pronta para revisão" | |
| 14 | Exemplos de código na spec em PT-BR e **comentados** | |

**Máximo:** 28 pontos.
