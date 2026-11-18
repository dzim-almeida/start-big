# Serviços e Ordens de Serviço (`order-service`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

A área **Serviços** (`/servicos`, nome `services`): a **Ordem de Serviço (OS)** com o ciclo completo de um atendimento — entrada do objeto (equipamento, veículo, móvel...), diagnóstico, itens, fotos, execução, pagamento e entrega. As abas mudam conforme o **segmento** da loja: Ordens, Serviços (catálogo), Pátio, Agenda, Orçamentos, Revisões e, na marcenaria, Produção, Instalações e Terceirizados. Lojas do segmento `pdv` não têm essa tela.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/order-service/` — `views/OrdemServicoView.vue` (+ `views/tabs/`), `ordens/` (OS), `servicos/` (catálogo), `revisoes/`, `fabrica/` (separação), `shared/` (`segmento/` rótulos e capacidades) |
| Backend (endpoints) | `ordem_servico.py` (`/api/v1/ordens-servico`, 29 rotas) · `servico.py` (`/servicos`, permissão `servico`) · `checklist_mobile.py` (`/checklist`) |
| Backend (regras) | `app/services/ordem_servico/` (`criacao`, `atualizacao`, `itens`, `status`, `estoque`, `foto`, `objeto`, `nota_fiscal`, `regras`, `regras_tipo`, `ganchos`, `consultas`) · `services/servico/` |
| Backend (banco) | `models/ordem_servico.py`, `ordem_servico_item.py`, `ordem_servico_pagamento.py`, `ordem_servico_foto.py`, `ordem_servico_executor.py`, `ordem_servico_nota_fiscal.py`, `objeto_servico.py`, `servico.py`, `servico_fiscal.py` |
| Registro de segmentos | `backend-fastapi/app/core/segmentos/` (`definicoes/`, `capacidades.py`) |
| Configuração | `models/configuracao_os.py` (seção "Ordens de serviço" em `configuracoes`) |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **OS** | Ordem de Serviço: o registro do atendimento. |
| **Objeto de serviço** | O que está sendo atendido (antes "equipamento"); o rótulo muda por segmento (ex.: "Veículo" na oficina). |
| **Capacidade** | Recurso que o segmento liga ou desliga (ex.: pátio, agenda, orçamento técnico, revisões). A tela pergunta `tem('capacidade')`. |
| **Gancho** | Ponto de extensão onde um segmento acrescenta regra sem mexer no fluxo comum (`ganchos.py`). |
| **Revisão** | Retorno programado ao cliente (aba "Revisões"). |

## 4. Fluxos principais

1. **Abrir OS:** escolhe o cliente e o objeto, define itens e prazo → status inicial.
2. **Atualizar:** itens, fotos de diagnóstico, troca de cliente, mudança de status (regras em `status.py`).
3. **Finalizar:** registra **pagamentos múltiplos**, dá baixa no estoque (`estoque.py`) e pode lançar a nota (`nota_fiscal.py`).
4. **Checklist pelo celular:** `/checklist` (QR no celular para fotos/avarias).

## 5. Decisões de arquitetura

- **Segmento novo só acrescenta declaração no registry** (`core/segmentos/definicoes/`); se exigir tela nova, é falta de metadado. Segmentos hoje com definição: `assistencia`, `oficina`, `serigrafia`, `pdv`, `marcenaria`, `lava_rapido`.
- **Guard `exigeOrdemServico`** no `meta` da rota: esconder o menu não basta; digitar `/servicos` num segmento sem OS é barrado.
- **Comportamento do segmento por capacidade**, não por `if (segmento === ...)` espalhado.
- A refatoração "equipamento → objeto de serviço" tem a migração `965c71a2da9a` (modelo de migração que decide pelo **schema antigo**).

## 6. Integração com outros módulos

- **`customers`, `products`, `employees`:** cliente, peças/produtos e executor da OS.
- **`sales`:** formas de pagamento globais; a OS pode virar venda/recebimento.
- **`fiscal`:** NF-e/NFS-e a partir da OS.
- **`marcenaria` e `lava-rapido`:** as abas específicas vivem nestes módulos, hospedadas aqui.
- **`compras`:** a OS é uma origem de necessidade de compra (`services/compras/demanda_os.py`).

## 7. Referências

- `backend-fastapi/docs/ordem_servico.md` (mapa de arquivos e regras da OS)
- `backend-fastapi/docs/segmento-marcenaria-plano.md` · `docs/marcenaria/` · `docs/lava-rapido/`
