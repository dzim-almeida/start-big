# Gestão de Equipe (`employees`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

A tela **Gestão de Equipe** (`/equipes`, nome `employees`): cadastro de **funcionários** (dados pessoais, endereço, dados bancários, comissão, observações) e de **cargos**. O cargo carrega as **permissões** (o que cada pessoa pode ver e fazer no sistema).

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/employees/` (`views/EmployeesView.vue`) |
| Funcionários | `components/EmployeeTable.vue`, `EmployeeModal.vue`, `components/form/*Section.vue` · `composables/useEmployee*.ts` · `services/employee.service.ts` · `schemas/employee.schema.ts` |
| Cargos | `components/PositionsPanel.vue`, `PositionCard.vue`, `PositionModal.vue` · `composables/usePosition*.ts` · `services/position.service.ts` |
| Chaves de permissão | `frontend/src/shared/constants/permissions.constants.ts` |
| Backend (endpoints) | `endpoints/funcionario.py` (`/api/v1/funcionarios`, permissão `funcionario`) · `endpoints/cargo.py` (`/api/v1/cargos`, permissão `cargo`) · `endpoints/usuario.py` |
| Backend (regras) | `app/services/funcionario/` (`cadastro.py`, `cargo.py`, `acesso.py`) · `app/schemas/funcionario/` · `app/db/crud/funcionario/` |
| Backend (banco) | `app/db/models/funcionario.py` · `cargo.py` · `usuario.py` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Funcionário** | Pessoa da equipe; pode ter (ou não) um usuário de acesso ao sistema. |
| **Cargo** | Grupo de permissões (ex.: caixas de "Compras", "Etiquetas", "Financeiro"). |
| **Permissão** | Chave de texto (`produto`, `cliente`, `view_financeiro`, `compra`...) que o backend confere em `check_permission`. |
| **Comissão** | Regra de ganho do funcionário; alimenta os relatórios (`reports`). |

## 4. Fluxos principais

1. **Cadastrar funcionário:** modal com seções (dados, endereço, bancários, comissão, observações) → `POST /funcionarios/`.
2. **Dar acesso:** `services/funcionario/acesso.py` concede login (cria o usuário) a quem **já é** funcionário.
3. **Criar cargo:** marcar as permissões no `PositionModal` → `POST /cargos/`. Quem tem o cargo passa a ver as telas e rotas liberadas por ele.

## 5. Decisões de arquitetura

- **Permissão é checada no backend** (`check_permission`) e **espelhada no menu** do frontend (`useCheckPermission`); esconder o botão não substitui a checagem do servidor.
- Funcionário e cargo são sempre da **empresa do token** (`empresa_id`).
- Uma permissão nova precisa entrar nos dois lados: `permissions.constants.ts` e o `check_permission` da rota (e na tela de cargos, para poder ser marcada).

## 6. Integração com outros módulos

- **`auth`/`minha-conta`:** o usuário vinculado ao funcionário faz login e edita a própria conta.
- **`reports`:** extrato e comissão do funcionário.
- **`order-service` e `sales`:** funcionário é o responsável/executor/vendedor.
- **`mainLayout`:** o menu lê as permissões do cargo.

## 7. Referências

- `backend-fastapi/docs/relatorio-extrato-do-funcionario-plano.md`
