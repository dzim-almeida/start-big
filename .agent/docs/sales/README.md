# Vendas, Caixa e Orçamentos (`sales`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

O **PDV** (ponto de venda) e o balcão: a tela **Vendas** (`/vendas`, nome `sales`) tem duas abas, **Vendas** e **Orçamentos**. Inclui o modal de venda (itens, cliente, pagamentos), leitor de código de barras, atalhos de teclado, impressão do comprovante e o **controle de caixa** (abrir, sangria, suprimento e fechar o turno).

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/sales/` — `SalesView.vue` (abas), `components/` (`SaleModal/`, `OrcamentoModal/`, `SaleTable`, `OrcamentoTable`, `print/`), `composables/` (`flows/`, `form/`, `mutates/`, `queries/`, `useSaleShortcuts.ts`) |
| Caixa | `sales/caixa/` (`components`, `composables`, `services`, `schemas`) |
| Estado de balcão | `shared/stores/balcao.store.ts` · impressão `shared/services/impressao.service.ts`, `escpos.ts` |
| Backend (endpoints) | `venda.py` (`/api/v1/vendas`, 19 rotas) · `sessao_caixa.py` (`/caixa`: `atual`, `abrir`, `suprimento`, `sangria`, `fechar`) · `orcamento.py` (`/orcamentos`) · `terminal.py` (`/terminais`) · `forma_pagamento.py` (`/formas-pagamento`) |
| Backend (regras) | `app/services/venda/` (`cadastro`, `itens`, `calculo`, `finalizacao`, `fila`, `atacado`, `status`, `nota_fiscal`, `guarda_fiscal`, `correcao_fiscal`) · `services/sessao_caixa/` · `services/orcamento/` · `services/terminal/estacoes.py` |
| Backend (banco) | `models/venda.py`, `venda_produto.py`, `venda_pagamento.py`, `venda_nota_fiscal.py`, `contador_venda.py`, `sessao_caixa.py`, `terminal.py`, `terminal_conectado.py`, `orcamento.py`, `orcamento_produto.py`, `forma_pagamento.py` |
| Configuração | `models/configuracao_vendas.py` (seção "Regras de vendas" em `configuracoes`) |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Sessão de caixa** | Turno de caixa: abre com valor inicial, recebe sangrias/suprimentos e fecha com conferência. |
| **Fila do caixa** | Modo opcional (`usar_fila_do_caixa`): o atendente monta a venda e o caixa recebe. |
| **Terminal / estação** | Cada máquina cadastrada em `/terminais` (identificada pelo `hwid`). |
| **Venda atacado** | Preço por quantidade/embalagem (`services/venda/atacado.py`). |
| **Guarda fiscal** | Trava que impede emitir/alterar venda quando as regras fiscais não permitem. |
| **Orçamento** | Proposta de venda que vira venda (`services/orcamento/conversao.py`). |

## 4. Fluxos principais

1. **Venda no balcão:** bipa/busca o produto → informa cliente (opcional) → soma pagamentos (dinheiro, Pix, cartão...) → finaliza → baixa estoque e imprime.
2. **Caixa:** `POST /caixa/abrir` → vendas → `sangria`/`suprimento` → `fechar` (conferência).
3. **Orçamento → venda:** cria o orçamento, converte quando o cliente aprova.
4. **Nota fiscal:** quando a loja é fiscal, a venda segue para o módulo `fiscal` (NFC-e/NF-e).

## 5. Decisões de arquitetura

- **PDV é modo, não segmento:** o módulo de vendas atende todos os segmentos; o segmento `pdv` apenas não tem Ordem de Serviço.
- **O caixa e a fila são opcionais** e controlados por configuração (`controlar_caixa`, `exigir_caixa_aberto`, `usar_fila_do_caixa`).
- **Scripts de guarda no build:** `npm run check:balcao`, `check:pix` e `check:print-bw` rodam no `npm run build` e protegem regras do balcão, do Pix e da impressão em preto e branco.
- Dinheiro sempre em `Decimal`; quantidade fracionada tem regra própria (`precificacao/quantidade.py`).

## 6. Integração com outros módulos

- **`products`:** produto, preço, estoque e embalagem.
- **`customers`:** cliente da venda.
- **`fiscal`:** emissão de NFC-e/NF-e e correção fiscal.
- **`financeiro`:** o resultado do mês e as movimentações usam as vendas (confira em `services/financeiro/` como a ligação é feita).
- **`reports` e `home`:** faturamento, caixa e ranking.
- **`order-service`:** o pagamento da OS usa as formas de pagamento globais.

## 7. Referências

- `backend-fastapi/docs/pdv-caixa-plano.md` · `pdv-fila-do-caixa-plano.md` · `pdv-profissional-plano.md` · `pdv-fiscal-e-nao-fiscal-plano.md` · `pdv-onde-paramos.md` · `venda-fracionada-plano.md` · `comprovantes-perfil-plano.md`
- `backend-fastapi/docs/sales/` (specs de vendas)
