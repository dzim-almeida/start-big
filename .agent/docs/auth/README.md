# Autenticação (`auth`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças. Estado das entregas: `SUMMARY.md` (ainda não criado).

## 1. O que é

É a tela de **login** e o fluxo que prova quem é o usuário. Depois do login, o frontend guarda o token (uma "chave" que o backend entrega) e o envia em todas as chamadas à API. Também cuida do **logout** e da **sessão expirada** (quando o backend responde `401`).

O login é **por terminal**: junto com e-mail e senha, o frontend envia o `hwid` (identificação da máquina), porque a licença e os terminais são amarrados à máquina (ver `license`).

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/auth/` (`views/LoginView.vue`, `composables/useLogin.ts`, `services/auth.service.ts`, `schemas/login.schema.ts`) |
| Estado global da sessão | `frontend/src/shared/stores/auth.store.ts` |
| Cliente HTTP (token e `401`) | `frontend/src/api/axios.ts` |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/auth.py` (prefixo `/api/v1/auth`) |
| Backend (regras) | `backend-fastapi/app/services/acesso/auth.py` · `usuario.py` |
| Backend (segurança) | `backend-fastapi/app/core/security.py` (hash de senha e JWT) · `core/depends.py` (`get_current_active_user`, `check_permission`) |
| Backend (banco) | `app/db/models/usuario.py` · `token.py` · `app/db/crud/acesso/` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **JWT** | Token assinado que o backend emite no login e que identifica o usuário e a empresa. |
| **Token Bearer** | O jeito de enviar o JWT: cabeçalho `Authorization: Bearer <token>`. O `api/axios.ts` faz isso sozinho. |
| **`hwid`** | Identificador da máquina; enviado no login e no logout. |
| **Blocklist** | Lista de tokens já encerrados (logout), para não serem aceitos de novo. |
| **Rota `auth.user`** | Nome da rota de `/login`. Para ela o app redireciona quando a sessão cai. |

## 4. Fluxos principais

1. **Login:** `LoginView` valida o formulário (Zod) → `useLogin` chama `POST /api/v1/auth/login` → o token vai para a store e o app entra na área autenticada.
2. **Sessão expirada:** qualquer resposta `401` faz o interceptor chamar `logoutUser()`, mostrar o aviso "Sessão Expirada" (só se havia token) e voltar para `auth.user`.
3. **Logout:** `POST /api/v1/auth/logout` com o `hwid`; o token entra na blocklist.
4. **Outros endpoints do prefixo `/auth`:** `GET /status`, `POST /reconnect` e `POST /setup` (usados pelo onboarding, módulo `sign-in`).

## 5. Decisões de arquitetura

- **Permissão e empresa vêm do token.** O `check_permission` (em `core/depends.py`) rejeita usuário sem `empresa_id` e relê o usuário no banco a cada chamada (um usuário desativado perde acesso mesmo com token válido).
- **Onde o token fica:** o `api/axios.ts` lê o token do `localStorage` (chave `access_token`). O `CLAUDE.md` fala em cookies HTTP-only; **o código atual usa `localStorage` + cabeçalho Bearer**. Confirmar com o time qual é a decisão vigente antes de mexer em autenticação (trilha completa).
- A rota `/login` não tem `meta` próprio: a verificação de licença roda antes (ver `license`).

## 6. Integração com outros módulos

- **`sign-in`:** cria a empresa e o primeiro usuário (`/auth/setup`); `auth` só entra depois.
- **`license`:** o guard do router verifica a licença antes de qualquer checagem de login.
- **`mainLayout`:** toda rota autenticada exige `requiresAuth`; o `UserCard` e o `useCheckPermission` leem a sessão da store.
- **`minha-conta` e `employees`:** manipulam o usuário (`/usuarios`), mas não o login.

## 7. Referências

- `CLAUDE.md` — seção "Auth flow".
- `frontend/src/router/index.ts` — guard global (licença → login → módulo).
