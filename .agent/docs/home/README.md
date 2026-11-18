# Início / Painel (`home`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

A tela inicial (`/`, nome `home`) com o **resumo do dia**. Mostra um painel diferente conforme quem está logado: o **dono/gerente** vê a empresa inteira; o **funcionário** vê o que é dele (fila de trabalho, atividade de hoje, OS atrasadas).

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/home/` (`views/HomeView.vue`) |
| Painéis | `components/dashboard/DashboardMaster.vue` e `DashboardFuncionario.vue` |
| Widgets | `components/dashboard/` (`TendenciaChart`, `RankingFuncionarios`, `FormasPagamentoWidget`, `EstoqueBaixoTable`, `OSPorStatusWidget`, `MinhaFilaTable`, `AtividadeHoje`, banners de OS atrasadas...) |
| Consultas | `composables/queries/` (um arquivo por dado, com vue-query) · `composables/useDashboard.ts` |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/dashboard.py` (prefixo `/api/v1/dashboard`, 17 rotas) |
| Backend (regras) | `backend-fastapi/app/services/dashboard/` (`empresa.py`, `meu_painel.py`, `periodo.py`) · `app/db/crud/dashboard/` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Painel master** | Visão da empresa: vendas, tendência, ranking, estoque baixo, OS por status. |
| **Meu painel** | Visão pessoal do funcionário (rotas `minha-fila`, `minhas-os-atrasadas`, `minha-atividade-hoje`...). |
| **Período** | Janela de datas dos números; calculada em `services/dashboard/periodo.py`. |

## 4. Fluxos principais

1. `HomeView` decide o painel pelo perfil e dispara as consultas dos widgets em paralelo (cada widget tem a sua).
2. Cada widget trata os estados de carregando, vazio e erro sozinho; falha de um não derruba os outros.

## 5. Decisões de arquitetura

- Um **composable de consulta por dado** (`useXxxQuery.ts`), para o cache do vue-query invalidar só o que mudou.
- Os números são calculados no **backend**; o frontend só formata e desenha (gráficos com Chart.js).
- Os **rótulos** dos widgets de OS variam por segmento (ex.: a oficina lê "Veículo" em vez de "Equipamento"), usando `order-service/shared/segmento/` (`useObjetoLabels`, `useRotulosStatusOS`).

## 6. Integração com outros módulos

- Lê dados de **`sales`**, **`order-service`**, **`products`** (estoque baixo) e formas de pagamento.
- Aparece dentro do `mainLayout`; a rota `/vendas` também já apontou para esta view (ver o aviso em `mainLayout`).

## 7. Referências

- `backend-fastapi/app/schemas/dashboard/` (formato das respostas).
