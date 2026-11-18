# Clientes (`customers`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

O **cadastro de clientes** da loja (rota `/clientes`, nome `customers`): lista com busca e filtro de ativos, e um formulário para cadastrar e editar clientes **Pessoa Física (PF)** e **Pessoa Jurídica (PJ)**, com endereços e observações.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/customers/` (`views/CustomersView.vue`, `components/CustomerTable.vue`, `components/modal/CustomerFormModal.vue` e `modal/form/*Section.vue`) |
| Formulário PF/PJ | `composables/modal/form/useCustomerPF.form.ts` e `useCustomerPJ.form.ts` · consulta à Receita: `composables/modal/context/consultaReceita.ts` |
| Consultas e gravações | `composables/request/` (`useCustomerGet.queries`, `useCustomerCreate.mutate`, `useCustomerUpdate.mutate`) · `services/customer{Get,Create,Update}.service.ts` |
| Schema compartilhado | `frontend/src/shared/schemas/customer/customer.schema.ts` (usado também por `sales` e `order-service`) |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/cliente.py` (`/api/v1/clientes`, 9 rotas; permissão `cliente`) |
| Backend (regras) | `app/services/cliente/` (`cadastro.py`, `historico.py`) · `app/schemas/cliente/` · `app/db/crud/cliente/` |
| Backend (banco) | `app/db/models/cliente.py` · `endereco.py` (endereço em `/api/v1/enderecos`) |
| Configuração | `app/db/models/configuracao_clientes.py` (seção "Cadastro de clientes" em `configuracoes`) |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **PF / PJ** | Pessoa Física (CPF) e Pessoa Jurídica (CNPJ). Cada um tem rota de criação própria (`/clientes/cliente_pf` e `/clientes/cliente_pj`). |
| **Consulta de CNPJ** | Preenche dados da empresa a partir do CNPJ (`shared/services/cnpj.service.ts`). |
| **Histórico** | Registro do que o cliente já comprou/contratou (`services/cliente/historico.py`). |

## 4. Fluxos principais

1. **Listar:** `CustomersView` → `useCustomers` → `GET /clientes/` paginado (`buscar`, `only_active`, `page`, `limit`).
2. **Criar/editar:** o modal escolhe PF ou PJ, valida com Zod e envia; o endereço vai junto no payload.
3. **Buscar no balcão:** `sales` e `order-service` reutilizam o schema e a busca de cliente (`shared/services/cliente.service.ts`).

## 5. Decisões de arquitetura

- **Isolamento por empresa:** todo cliente pertence a uma `empresa_id` vinda do token.
- O módulo é um bom **modelo de padrão** do frontend: services separados por operação, composables por consulta/gravação, schemas Zod.
- **Pendência `PEND-001`:** CNPJ alfanumérico (emitido desde julho/2026) não é aceito na máscara, na validação (`cpf-cnpj-validator`) nem no backend (`validar_cnpj`). Ver `backend-fastapi/docs/pendencias-sistema.md`.

## 6. Integração com outros módulos

- **`sales`, `order-service`, `fiscal`:** escolhem o cliente (e usam CPF/CNPJ no documento fiscal).
- **`marcenaria`:** orçamento e projeto são ligados a cliente PF ou PJ (`SPEC-02-CNPJ-CLIENTE-MARCENARIA`).
- **`configuracoes`:** regras do cadastro (campos obrigatórios etc.).

## 7. Referências

- `backend-fastapi/docs/pendencias-sistema.md` (PEND-001).
- `frontend/src/shared/schemas/customer/`.
