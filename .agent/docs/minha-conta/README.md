# Minha Conta (`minha-conta`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

A área onde o **usuário logado edita a própria conta**: atualizar dados pessoais, **trocar a senha** e enviar a **foto de perfil**. Abre em um modal (`MinhaContaModal`) a partir do cartão do usuário no `mainLayout`.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/minha-conta/` — `views/MinhaContaView.vue`, `components/MinhaContaModal.vue`, `composables/mutates/` (`useAtualizarContaMutation`, `useAlterarSenhaMutation`, `useUploadFotoPerfilMutation`), `services/minhaConta.service.ts`, `schemas/minhaConta.schema.ts` |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/usuario.py` (`/api/v1/usuarios`): `GET /me`, `PATCH /me`, `PATCH /me/senha`, `POST /imagem` |
| Backend (regras) | `app/services/acesso/usuario.py` · `app/core/security.py` (hash da senha) |
| Backend (banco) | `app/db/models/usuario.py` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **`/me`** | "Eu mesmo": o backend sabe quem é pelo token, então a rota não recebe `id`. |
| **Hash de senha** | A senha nunca é guardada em texto; só o resultado de um cálculo irreversível. |

## 4. Fluxos principais

1. **Editar dados:** formulário validado com Zod → `PATCH /usuarios/me`.
2. **Trocar senha:** senha atual + nova → `PATCH /usuarios/me/senha`.
3. **Foto:** upload de imagem → `POST /usuarios/imagem`.

## 5. Decisões de arquitetura

- Como as rotas usam `/me`, **um usuário só altera a própria conta**; alterar outro usuário é do módulo `employees`.
- Senha, token e hash **nunca** vão para log, resposta ou documentação.

## 6. Integração com outros módulos

- **`auth`:** a sessão e o token vêm de lá; trocar a senha não é login.
- **`mainLayout`:** o `UserCard` abre este modal.
- **`employees`:** cadastro e acesso de outros usuários.

## 7. Referências

- `backend-fastapi/docs/comprovantes-perfil-plano.md` (perfil de comprovante, tema à parte desta tela).
