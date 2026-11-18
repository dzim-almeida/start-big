# Gestão Financeira (`financeiro`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

A área **Gestão Financeira** (`/financeiro/*`) com oito telas: **Visão Geral** (resultado do mês e movimento do caixa, é a porta de entrada), **Análise**, **Contas a Pagar**, **Contas a Receber**, **Fluxo de Caixa**, **Conciliação**, **Extrato** e **Plano de Contas**.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/financeiro/` — `views/FinanceiroLayout.vue`, `views/VisaoGeralView.vue` e uma pasta por tela (`analise/`, `contas-pagar/`, `contas-receber/`, `fluxo-caixa/`, `conciliacao/`, `extrato/`, `plano-contas/`) + `shared/` |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/financeiro.py` (`/api/v1/financeiro`, 32 rotas) |
| Backend (regras) | `app/services/financeiro/` (`resumo`, `contas_pagar`, `contas_pagar_baixa`, `contas_receber`, `fluxo_caixa`, `conciliacao`, `extrato`, `analise`, `plano_contas`, `contas_bancarias`, `promessas`, `saldo`, `comum`) · `app/schemas/financeiro/` · `app/db/crud/financeiro/` |
| Backend (banco) | `models/conta_pagar.py`, `conta_receber.py`, `conta_bancaria.py`, `plano_conta.py`, `movimentacao_financeira.py`, `historico_financeiro.py` |
| Permissões | `view_financeiro` (consultar) · `manage_financeiro` (lançar, dar baixa, estornar) |
| Configuração | seção "Gestão financeira" em `configuracoes` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Conta a pagar / a receber** | Obrigação com data de vencimento; recebe **baixa** quando é paga/recebida. |
| **Plano de contas** | Categorias para classificar entradas e saídas. |
| **Fluxo de caixa** | Projeção do que entra e sai por data. |
| **Conciliação** | Conferir o extrato do banco com os lançamentos do sistema. |
| **Promessa** | Compromisso de pagamento do cliente (cobrança). |
| **`FINANCEIRO` × `FINANCEIRO_PRO`** | Dois módulos contratáveis (ver abaixo). |

## 4. Fluxos principais

1. **Visão Geral:** resultado do mês e movimento do caixa (`services/financeiro/resumo.py`).
2. **Contas a pagar:** lançar → dar baixa (`contas_pagar_baixa.py`) → estornar se preciso.
3. **Contas a receber:** lançar, cobrar (com `promessas` de pagamento) e dar baixa (`services/financeiro/contas_receber.py`).
4. **Fluxo de caixa e conciliação:** projeção e conferência com o extrato bancário.

## 5. Decisões de arquitetura

- **Dois módulos contratáveis:** `FINANCEIRO` (visão geral, contas a pagar, contas a receber, extrato, plano de contas) e `FINANCEIRO_PRO` (**Análise**, **Fluxo de Caixa**, **Conciliação**). O módulo básico é liberado a todos os planos hoje, mas fica travado de propósito: conceder a mais um plano é um clique na licença, tirar a trava exigiria novo instalador.
- **Duas permissões separadas** (ver e gerenciar): dar acesso à cobrança não pode abrir a folha de pagamento (contas a pagar).
- A trava de módulo fica em **cada rota filha** (`exigeModulo`) e no backend (`requer_modulo`).
- Dinheiro em `Decimal`; datas de vencimento tratadas no backend.

## 6. Integração com outros módulos

- **`sales` e `order-service`:** são origem de recebimentos (confira em `services/financeiro/` e nos models de venda/OS como a ligação é feita antes de documentar em detalhe).
- **`compras` e `products`:** recebimento e entrada por XML geram contas a pagar.
- **`reports` e `home`:** consomem os resultados.
- **`license`:** habilita `FINANCEIRO`/`FINANCEIRO_PRO`.

## 7. Referências

- `frontend/src/shared/constants/modulos.constants.ts` · `permissions.constants.ts`
- `backend-fastapi/docs/pendencias-sistema.md` (PEND-003 toca o financeiro)
