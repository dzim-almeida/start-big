# Spec 04B — Pátio (Frontend)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026 (aguardando o usuário olhar as telas)       |
| Camada       | Frontend ⚠️ página de Serviços, abertura de OS                         |
| Dependências | Specs 04A, 03B                                                        |
| Referência   | SPEC-00 Revisão 4: U1, U3, U6 · O8                                     |

---

## 1. Objetivo

A tela inicial do lava-rápido: **Aguardando · Lavando · Pronto**, com as entregas do dia recolhidas embaixo.

## 2. Tela (`modules/lava-rapido/patio/`)

- **Indicadores:** no pátio, lavando agora, prontos esperando (em alerta quando há), recebido hoje.
- **Cartão do veículo:** placa (o código `VEI-…` aparece discreto), modelo e cor, porte, há quanto tempo está no pátio, "Pronto às" (vermelho se atrasou), serviços e total, cliente, lavadores (clique troca), avarias marcadas.
- **Ação por coluna:** Aguardando → **Começar a lavar**; Lavando → **Pronto**; Pronto → **WhatsApp** (`wa.me`, mensagem pronta) e **Receber**. Seta para voltar uma coluna (engano). **Ver detalhes** abre a OS de sempre.
- **Receber** abre a OS já no recebimento (opção nova `receber` em `openExistingOS`; o modal a lê e limpa).
- Recarrega a cada 15 s, ao voltar para a janela e quando o modal de OS fecha.

## 3. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | Aba **Pátio** primeiro em Serviços, pela capacidade `operacao_patio` | U1 |
| D2 | Os títulos das colunas vêm de `useRotulosStatusOS` (contrato) | Um lugar só para os textos de status |
| D3 | `openExistingOS(..., { receber: true })` é **opcional**; sem ela, nada muda em nenhuma tela | PR1 |
| D4 | WhatsApp só aparece com celular/telefone com DDD | Botão que não funciona é pior que nenhum |

## 4. Limitações

- Sem arrastar e soltar: um clique por coluna (mais rápido no toque).
- Impressão pelo "Ver detalhes".
