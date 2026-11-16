# Spec 08A — Agenda (Backend)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026 (adiantada a pedido do usuário)             |
| Camada       | Backend                                                               |
| Dependências | Specs 02A, 03A                                                        |
| Bloqueia     | Spec 08B                                                              |
| Referência   | SPEC-00: O11 · PR1, PR8                                                |

---

## 1. Objetivo

O cliente liga e marca um horário; quando ele chega, a lavagem vira OS. O agendamento vem **antes** da OS (a agenda da marcenaria agenda uma OS que já existe, por isso não serve).

## 2. Tabela `agendamentos` (migração `l4v4ag3nd003`)

`inicio` (UTC), `duracao_minutos`, `cliente_id` (opcional) + `cliente_nome` + `cliente_contato`, `placa`, `veiculo`, `tipo_veiculo`, `porte_id` (SET NULL), `servicos` (JSON: `{servico_id, nome, valor}` — cópia do combinado), `observacao`, `situacao`, `numero_os`, `criado_em`.

## 3. Rotas (`/api/v1/lava-rapido`, capacidade `agenda_servicos`)

| Método | Rota | O quê |
|---|---|---|
| GET | `/agendamentos?inicio=&fim=` | Dias da loja, na ordem da hora (máx. 2 meses) |
| POST | `/agendamentos` | Novo, situação AGENDADO |
| PUT | `/agendamentos/{id}` | Remarcar, alterar, mudar situação (CHEGOU exige `numero_os`) |
| DELETE | `/agendamentos/{id}` | Só cancelado |

## 4. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | Cliente cadastrado **ou** só nome e telefone | Quem liga pela primeira vez não tem cadastro; ele nasce na comanda, quando chega |
| D2 | Serviços e valores são **cópia** do combinado | O preço falado ao telefone não muda se a tabela mudar |
| D3 | CHEGOU exige a OS aberta e não volta atrás | A partir daí quem conta é a OS |
| D4 | Situação em texto (AGENDADO, CHEGOU, NAO_VEIO, CANCELADO), não enum do banco | Acrescentar uma situação não exige migração |
| D5 | Sem limite de vagas por horário nesta versão | O1/O11 previam aviso por nº de boxes; entra quando o cliente pedir (fica registrado) |

## 5. Casos de teste

`test/api/v1/test_lava_rapido_agenda.py` (7): criar e listar no dia · ordem pela hora · remarcar e "não veio" · chegou exige OS e não volta · excluir só cancelado · validações · 404 fora do segmento. `test/db/test_migracao_agenda_lava_rapido.py` (3).
