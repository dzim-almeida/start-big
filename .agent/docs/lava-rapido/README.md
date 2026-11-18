# Segmento Lava-Rápido (`lava-rapido`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças. A fonte das decisões é `backend-fastapi/docs/lava-rapido/SPEC-00-DECISOES-LAVA-RAPIDO.md`.

## 1. O que é

O segmento para **lava-rápido e estética automotiva** (carro, moto, caminhão, ônibus). Critério de pronto da fase 1: o primeiro cliente roda **um dia inteiro de pátio** pelo sistema — entrada pela placa, preço pelo **porte**, vistoria com foto, quadro do pátio, aviso de "pronto" e finalização com pagamento — enquanto os segmentos em produção seguem idênticos.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/lava-rapido/` — `comanda/` (entrada e comanda: `EntradaLavagem`, `ComandaModal`), `patio/` (quadro do pátio: `PatioTab`, `CartaoVeiculo`, `LavadoresModal`), `agenda/` (`AgendaTab`, `AgendamentoModal`), `shared/` (seletor de lavadores e divisão de comissão, schemas, utils) |
| Onde aparece | Abas **Pátio** e **Agenda** na tela de Serviços (`order-service`), liberadas pelas capacidades do segmento |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/lava_rapido.py` (`/api/v1/lava-rapido`, 16 rotas, permissão `servico`) |
| Backend (regras) | `app/services/lava_rapido/` (`portes`, `patio`, `agenda`, `lavadores`) · `app/db/crud/lava_rapido/` · `app/schemas/lava_rapido/` |
| Backend (banco) | `app/db/models/lava_rapido/` (`porte.py`, `agendamento.py`) |
| Segmento | `app/core/segmentos/definicoes/lava_rapido.py` |
| Configuração | seção "Lava-rápido" em `configuracoes` (inclui vagas do pátio) |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Veículo** | O "objeto de serviço" da OS (placa, marca, modelo, cor, porte). |
| **Porte** | Categoria do veículo (ex.: Hatch, SUV, Caminhão) que define **preço e duração** do serviço. |
| **Tabela de preço por porte** | Preço e duração por serviço e por porte; sem linha para o porte, vale o preço padrão. |
| **Pátio / quadro do pátio** | Veículos que estão na loja hoje, em colunas por status (na fila, lavando, pronto). |
| **Lavador** | Funcionário responsável pela OS (1 ou 2 por OS, com divisão de comissão). |
| **Vistoria de entrada** | Avarias registradas com foto antes de lavar. |
| **Agenda** | Agendamento do cliente; "Chegou" abre a OS já preenchida. |

## 4. Fluxos principais

1. **Preparação (dono):** ajusta a lista de portes e cadastra serviços com preço e duração por porte.
2. **(Opcional) Agendar:** cliente agendado; no dia, "Chegou" abre a OS.
3. **Entrada:** digita a placa → veículo e dono aparecem (ou cadastro mínimo); escolhe serviços e lavadores; a **previsão** de término aparece.
4. **Vistoria e pátio:** marca avarias e tira fotos (no computador ou no celular por QR); acompanha no quadro do pátio.
5. **Fechar:** finaliza com pagamento como qualquer OS.

## 5. Decisões de arquitetura

- **Os portes são declarados no registry do segmento**, e o preço por porte é uma tabela do serviço — não há `if (segmento)` espalhado.
- O módulo **reaproveita a OS** (`order-service`): comanda, pátio e agenda são "interface própria" em cima da mesma OS.
- Fora da fase 1 (SPEC-00 §7): plano mensal, pacote, cartão fidelidade e convênio de frota.
- **Fiscal:** o enquadramento do serviço (item da LC 116, ISS) deve ser **confirmado com o contador do cliente** antes da primeira NFS-e.

## 6. Integração com outros módulos

- **`order-service`:** hospeda as abas e a OS.
- **`customers`:** dono do veículo; **`employees`:** lavadores e comissão.
- **`fiscal` e `sales`/`financeiro`:** NFS-e e pagamento da OS.
- **`configuracoes`:** vagas do pátio e demais opções.

## 7. Referências

- `backend-fastapi/docs/lava-rapido/` — `PLANO-LAVA-RAPIDO.md`, `SPEC-00` a `SPEC-10B` (backend A / frontend B)
