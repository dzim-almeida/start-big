# Spec 04A — Pátio (Backend)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026                                             |
| Camada       | Backend (só leitura e a atualização de OS que já existe)               |
| Dependências | Specs 03A, 10A                                                        |
| Bloqueia     | Spec 04B                                                              |
| Referência   | SPEC-00: U3, O3, O8 · PR1, PR2                                         |

---

## 1. Objetivo

Dar à tela do pátio os veículos do dia, já separados nas colunas **Aguardando / Lavando / Pronto / Entregues hoje**, e mover um veículo de coluna com um clique.

## 2. Rotas (`/api/v1/lava-rapido`, capacidade `operacao_patio`)

| Método | Rota | O quê |
|---|---|---|
| GET | `/patio` | `{aguardando, lavando, pronto, entregues_hoje}` de `CartaoPatio` |
| POST | `/os/{numero}/avancar` | ABERTA → EM_ANDAMENTO → AGUARDANDO_RETIRADA; do Pronto, 422 ("use Receber") |
| POST | `/os/{numero}/voltar` | a casa anterior (engano); no início, 422 |

`CartaoPatio`: número, status, tipo de veículo, placa, modelo, marca, cor, porte, cliente (nome e celular/telefone, para o WhatsApp), serviços (itens de serviço não reprovados), total, lavadores, responsável, avarias marcadas, entrada, previsão, finalização.

## 3. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | O pátio mostra **todas** as OS em aberto (as de hoje e as que ficaram de ontem) e as **finalizadas hoje** (dia da loja, `intervalo_utc`). Canceladas não aparecem | O carro que dormiu no pátio continua no pátio |
| D2 | Ordem de chegada (`data_criacao`); entregues, a mais recente primeiro | Quem entrou primeiro sai primeiro; o atendente procura a última entrega |
| D3 | Avançar/voltar passa pela **atualização de OS de sempre** (`update_ordem_servico`) | Mesmas travas: status do segmento (01A), OS fechada, trilho da fábrica. Nenhuma regra de status nova |
| D4 | Finalizar **não** é um passo do pátio: o cartão Pronto abre o recebimento de sempre | Pagamento, caixa e comissão continuam num lugar só |
| D5 | Sem rota nova de WhatsApp: o cartão traz o contato, e a tela monta o `wa.me` (O8) | Sem API, sem custo |

## 4. Casos de teste

`test/api/v1/test_lava_rapido_patio.py` (6): OS nova em Aguardando com o conteúdo do cartão · avançar até Pronto, 422 no fim, receber → Entregues hoje · voltar e 422 no início · ordem de chegada · cancelada some · 404 fora do segmento.
