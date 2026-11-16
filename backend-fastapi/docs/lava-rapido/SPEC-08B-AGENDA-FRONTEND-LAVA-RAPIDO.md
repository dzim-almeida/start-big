# Spec 08B — Agenda (Frontend)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026 (adiantada a pedido do usuário)             |
| Camada       | Frontend ⚠️ página de Serviços                                         |
| Dependências | Specs 08A, 03B                                                        |
| Referência   | SPEC-00: O11, U1                                                       |

---

## Tela (`modules/lava-rapido/agenda/`)

- Aba **Agenda** em Serviços, logo depois do Pátio (capacidade `agenda_servicos`).
- **Semana** (segunda a domingo) com o número de agendados por dia; setas, "Hoje" e **Novo agendamento**.
- **Dia escolhido**: hora, duração, cliente, placa e veículo, serviços e total combinado, observação, situação.
- Ações do agendado: **Chegou** (abre a comanda já preenchida; criada a OS, o agendamento fica "Chegou · OS-…"), **WhatsApp** (confirmação pronta), Editar, Não veio, Cancelar. Não veio/Cancelado: Reagendar; cancelado pode ser excluído.
- **Modal** novo/editar: dia, hora, duração (soma dos serviços do porte, editável), cliente do cadastro ou só nome e telefone, tipo, porte, placa, veículo, serviços com o preço do porte, observação.

## Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | "Chegou" reaproveita a **comanda** (prop `agendamento`): placa (que acha o veículo), cliente, tipo, porte, serviços e observação já vêm; cliente sem cadastro abre o "cadastrar cliente novo" preenchido | Um caminho só para a lavagem entrar no pátio |
| D2 | Uma query por **semana** (a faixa e o dia saem dela); recarrega a cada 60 s | Poucas chamadas; a faixa de contagem sempre bate com o dia |
| D3 | Hora digitada é **local**; vai em UTC (`toISOString`) e volta lida como UTC | Mesma regra de datas da casa |
| D4 | Na aba Agenda o botão do topo some; "Novo agendamento" fica dentro da aba | O botão do topo falaria em "Nova entrada" ou "Novo Serviço" |

## Casos de teste

`agenda/__tests__/useAgenda.spec.ts` (3): semana de segunda a domingo, domingo, UTC sem "Z". `OrdemServicoView.abas.spec.ts`: Agenda depois do Pátio, sem o botão do topo.
