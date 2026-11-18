# Segmento Marcenaria (`marcenaria`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças. A fonte das decisões de negócio é `backend-fastapi/docs/marcenaria/SPEC-00-DECISOES-MARCENARIA.md`.

## 1. O que é

O segmento para **fábricas de móveis planejados e marcenarias**. Acompanha um projeto desde o **orçamento técnico por ambiente e móvel** até a **entrega e o termo de aceite**: aprovação (total ou parcial) que cria a OS, separação de material do estoque, terceirizados, produção por etapas, etiquetas de volume, instalação/entrega e faturamento. Objetivo da fase 1: a fábrica piloto leva um projeto real do orçamento ao termo de entrega **sem planilha**, e os segmentos já em produção seguem idênticos.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/marcenaria/` — `orcamentos/` (editor e lista, a maior parte do módulo), `os/`, `separacao/`, `terceirizados/`, `producao/`, `entrega/`, `faturamento/`, `etiquetas/`, `shared/` |
| Rotas | `/orcamentos` (redireciona para a aba "Orçamentos" de Serviços), `/orcamentos/novo`, `/orcamentos/:id` (editor em tela cheia); as abas **Produção**, **Instalações** e **Terceirizados** ficam em Serviços (`order-service`) |
| Backend (endpoints) | Prefixo `/api/v1/marcenaria/orcamentos`: `marcenaria_orcamento.py` (22 rotas) e `marcenaria_orcamento_itens.py` (15). Prefixo `/api/v1/marcenaria`: `marcenaria_separacao.py` (8), `marcenaria_terceirizado.py` (8; usa o módulo `COMPRAS` quando contratado), `marcenaria_producao.py` (8), `marcenaria_entrega.py` (13), `marcenaria_faturamento.py` (6). Prefixo `/api/v1/fabrica`: `fabrica.py` (20) |
| Backend (regras) | `app/services/marcenaria/` (`orcamento*`, `calculo`, `aprovacao`, `aditivo`, `entrega`, `agenda`, `faturamento/`, `insumos_os`, `leitor`...) · `app/services/fabrica/` (cálculo, insumo, separação, terceiros) |
| Backend (banco) | `app/db/models/marcenaria/` (`orcamento`, `ambiente`, `etapa`, `entrega`, `faturamento`, `evento`) · `fabrica_orcamento.py` · `configuracao_marcenaria.py` |
| Segmento | `app/core/segmentos/definicoes/marcenaria.py` |
| Configuração | seção "Marcenaria" em `configuracoes` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Ambiente / móvel** | Estrutura do orçamento: um projeto tem ambientes (cozinha, quarto) com móveis dentro. |
| **Visão do cliente** | Versão do orçamento que **não** mostra custo, margem nem RT. |
| **RT** | Reserva técnica (comissão do arquiteto que indicou o projeto); vira conta a pagar. |
| **Aprovação parcial / aditivo** | Aprovar só parte do orçamento e acrescentar itens depois. |
| **Insumo / peça embutida** | Material do estoque que entra no móvel; sai do estoque na **separação**. |
| **Terceirizado** | Móvel/serviço feito por fora, pedido pelo módulo Compras. |
| **Etapa de produção** | Passos por móvel (corte, montagem interna, montagem externa...). |
| **Termo de entrega** | Documento assinado na instalação, por ambiente, com pendências. |

## 4. Fluxos principais

1. Cadastra o cliente (com consulta de CNPJ) e, se houver, o arquiteto.
2. Monta o orçamento (rascunho salva sozinho), vê custo/margem (só quem tem permissão) e gera a **proposta em PDF**.
3. **Aprova** → o sistema cria a OS com os móveis e os insumos.
4. **Separa** o material (com leitor) → o que falta vira necessidade de compra.
5. **Produz** por etapas, imprime **etiquetas dos volumes**, **instala/entrega** e registra pendências.
6. **Finaliza** a OS com os pagamentos de sempre; o RT vira conta a pagar.

## 5. Decisões de arquitetura

- **Segmento novo só acrescenta declaração no registry**; a marcenaria usa as **capacidades** do `order-service`, sem `if` de segmento espalhado.
- **A "fábrica" antiga foi aposentada** (SPEC-00, FB1): a separação da marcenaria é a aba da Spec 10B; o motor de cálculo é a Spec 05.
- **Compras é o motor de compra:** falta de material e terceirizados passam pelo módulo `compras` quando ele está contratado (o pedido de terceirizado funciona "com ou sem o Compras", ver comentário em `api.py`).
- **Fora do segmento marcenaria as rotas respondem `404`:** o router da fábrica só responde no segmento Marcenaria, e as de orçamento exigem a capacidade `orcamento_tecnico`.
- O plano antigo `segmento-marcenaria-plano.md` está **substituído** pela SPEC-00 — não implementar a partir dele.
- **Pendências:** `PEND-001` (CNPJ alfanumérico), `PEND-002` (comissão da OS ignora o desconto da OS) e `PEND-003` (Compras): ver `backend-fastapi/docs/pendencias-sistema.md`.

## 6. Integração com outros módulos

- **`order-service`:** hospeda as abas e a OS criada na aprovação.
- **`compras`, `products`, `fiscal`, `financeiro`:** compra de material/terceirizados, estoque e etiquetas, nota fiscal e resultado do mês.
- **`customers`:** cliente PF/PJ do projeto.

## 7. Referências

- **Telas de design** (PNG/SVG: checklist da OS, orçamento e engenharia, separação de almoxarifado, termo de entrega, visão geral da OS): [`design/`](./design/).

- `backend-fastapi/docs/marcenaria/` — `PLANO-MARCENARIA.md`, `SPEC-00` a `SPEC-12` (backend A / frontend B)
- `backend-fastapi/docs/marcenaria-fabrica-plano.md` · `marcenaria-faturamento-plano.md` · `segmento-marcenaria-plano.md` (histórico) · `etiquetas-plano.md`
