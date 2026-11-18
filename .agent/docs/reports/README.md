# Relatórios (`reports`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

A tela **Relatórios** (`/relatorios`, nome `reports`): painel com seletor de período e seções de análise — faturamento, caixa, comissões, desempenho de OS, ranking, estoque, regras de preço, relatório para o **contador** e **extrato de serviços do funcionário**. Várias seções têm versão para **impressão**.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/reports/` — `views/ReportsDashboard.vue`, `components/` (uma `*Section.vue` por assunto, `PeriodFilter`, `KpiCard`, gráficos, `*Print.vue`), `composables/` (uma consulta por relatório), `report.service.ts`, `schemas/` |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/relatorios.py` (`/api/v1/relatorios`, 10 rotas) |
| Backend (regras) | `app/services/relatorio/` (`faturamento`, `os_performance`, `equipe`, `acesso_comissoes`, `contador`, `estoque`, `regras_preco`) · `app/db/crud/relatorio/` · `app/schemas/relatorio/` |
| Permissão | `view_reports` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Período** | Intervalo de datas escolhido (`usePeriodo`). |
| **KPI** | Número-chave mostrado em cartão (`KpiCard`). |
| **Relatório do contador** | Pacote de dados para a contabilidade (`ContadorSection`). |
| **Acesso a comissões** | Seção protegida (`AcessoComissoesModal`) para ver comissões. |
| **Extrato do funcionário** | Serviços feitos por um funcionário no período (com impressão). |

## 4. Fluxos principais

1. Escolhe o período → cada seção busca o seu relatório (`useXxxQuery`) → exibe KPIs, tabelas e gráficos.
2. Imprime (`*Print.vue`) com layout próprio para papel.
3. Comissão: abre o modal de acesso antes de mostrar os valores.

## 5. Decisões de arquitetura

- **Cálculo no backend**, formato no frontend; chaves de cache centralizadas em `query.keys.ts`.
- Impressão precisa funcionar em **preto e branco** (`npm run check:print-bw`).
- A seção de regras de preço reutiliza `precificacao/regras` do backend.

## 6. Integração com outros módulos

- Lê dados de **`sales`**, **`order-service`**, **`products`**, **`employees`** e **`financeiro`**.
- **`home`** mostra um subconjunto dos mesmos números como painel.

## 7. Referências

- `backend-fastapi/docs/relatorio-extrato-do-funcionario-plano.md`
