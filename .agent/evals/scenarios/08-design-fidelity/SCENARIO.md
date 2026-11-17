# 08 — Fidelidade ao design

**Avalia:** `skills/design`

## Objetivo
Verificar se o agente parte da referência, monta o inventário, usa tokens e `Base*` em vez de valores soltos, confere os estados, roda os `check:*` e entrega o relatório de fidelidade, declarando "não verificado" o que não conseguiu ver.

## Preparação
- Worktree ou clone a partir do `HEAD`, com `npm i` em `frontend/`.
- Coloque em `.agent/docs/avaliacao/design/` uma imagem simples de referência (ex.: um cartão com título, três linhas de texto, um selo colorido "Ativo" e dois botões "Cancelar" e "Salvar").
- Se o ambiente não tiver navegador, o agente deve declarar a verificação visual como **não verificada**.

## Prompt
> Cria o componente de cartão da imagem em `.agent/docs/avaliacao/design/cartao.png` dentro de `frontend/src/shared/components/ui/`, igual ao desenho.

## Resposta padrão (se o agente perguntar de onde vêm os dados)
> Props simples: título, linhas, status e dois eventos (cancelar, salvar).

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Abriu a imagem de referência e **listou o inventário** (regiões, elementos, estados) antes de codar | |
| 2 | Reaproveitou `BaseButton` (e `BaseStatusPill`, se servir) em vez de `<button>`/`<span>` crus | |
| 3 | Sem cor hexadecimal, `px` mágico ou `style=""` solto: usou tokens/classes do tema | [crítico] |
| 4 | Textos exatamente como na imagem (acentuação, maiúsculas) | |
| 5 | Criou a story (`*.stories.ts`) do componente novo | |
| 6 | Rodou `npm run check:tokens` (e `check:paleta` se mexeu em cor) e `npx vue-tsc --noEmit` | |
| 7 | Registrou as divergências (token mais próximo, variação sem suporte) em vez de inventar valor | |
| 8 | Entregou o relatório "Fidelidade" no formato da skill; o que não pôde ver aparece como "não verificado" | |
| 9 | Não afirmou "fiel ao desenho" sem ter comparado a tela | [crítico] |
| 10 | Comentários em PT-BR explicando o template e o `<script setup>` | |

**Máximo:** 20 pontos.
