# Compras (`compras`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

O módulo **Compras** (`/compras`): o caminho completo do **que precisa ser comprado → pedido ao fornecedor → recebimento → estoque e contas a pagar**. Tem quatro telas: **Necessidades**, **Pedidos**, **Recebimento** e **Relatórios**. É um **módulo contratável** (`COMPRAS`): quem não contratou não vê nada.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/compras/` — `views/ComprasLayout.vue` e uma pasta por tela: `necessidades/`, `pedidos/`, `recebimento/`, `relatorios/`, mais `fornecedores-produto/`, `ordens-servico/` e `shared/` |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/compras.py` (`/api/v1/compras`, 20 rotas, exige o módulo `COMPRAS`) |
| Backend (regras) | `app/services/compras/` (`necessidade(s)`, `pedidos`, `recebimentos`, `parcelas`, `nota_pedido`, `previsoes`, `relatorios`, `fornecedores_produto`, `demanda_os`, `nfe_entrada`, `permissoes`) |
| Backend (banco) | `models/pedido_compra.py`, `recebimento_compra.py`, `compra_log.py`, `produto_fornecedor.py`, `produto_codigo_fornecedor.py`, `nota_entrada.py` |
| Permissão | `compra` (linha "Compras" na tela de Cargos) |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Necessidade** | Item que a loja precisa comprar (estoque baixo, OS, projeto). |
| **Origem da necessidade** | De onde nasceu: estoque mínimo, uma OS (`demanda_os`) ou, no futuro, a marcenaria. |
| **Pedido** | Compra pedida a um fornecedor, com prazo e parcelas. |
| **Recebimento** | Chegada da mercadoria (total ou parcial); dá entrada no estoque. A divergência só **avisa**. |
| **Fornecedor do produto** | Quem vende o produto, com código e preço (aviso de fornecedor mais barato). |

## 4. Fluxos principais

1. **Necessidades → Pedido:** a tela sugere o que comprar; o usuário agrupa por fornecedor e cria o pedido.
2. **Recebimento:** confere o que chegou (pode usar a XML da NF-e) → entrada no estoque → gera contas a pagar em parcelas.
3. **Relatórios:** acompanhamento de pedidos e previsões de chegada.

## 5. Decisões de arquitetura

- **Nega por padrão:** `COMPRAS` está em `MODULOS_NEGADOS_SEM_RESPOSTA` (`app/core/modulos.py`). Licença sem resposta **não** libera (é módulo pago e novo). O backend responde `403` com `MODULO_NAO_CONTRATADO`.
- O menu e as quatro rotas filhas carregam `exigeModulo: MODULOS.COMPRAS` (a trava fica em cada filho).
- Serve **todos os segmentos**; a marcenaria entra como mais uma origem de necessidade, sem o módulo depender dela.
- **Pendência `PEND-003`:** o recebimento de Compras nasce sem categoria e o material pode sair do lucro duas vezes (ver `backend-fastapi/docs/pendencias-sistema.md`).

## 6. Integração com outros módulos

- **`products`:** estoque e fornecedores do produto.
- **`financeiro`:** contas a pagar geradas no recebimento.
- **`order-service` e `marcenaria`:** origens de necessidade; `marcenaria` usa `terceirizados` com o módulo COMPRAS.
- **`license`:** habilita o módulo.

## 7. Referências

- `backend-fastapi/docs/compras-plano.md` (decisões D1–D19 e fases) · `compras-plataforma-web.md` · `pendencias-sistema.md`
