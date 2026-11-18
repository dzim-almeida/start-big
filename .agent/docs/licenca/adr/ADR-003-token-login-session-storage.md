# ADR-003 — Token do login do ERP fica só na sessão da janela (sessionStorage)

- **Status:** Aceita em 2026-11-18
- **Substitui:** a parte da ADR-002 que trata do armazenamento do token do login (ela continua valendo para o uso do Bearer)
- **Módulos afetados:** `acesso`, `core`, front `auth`, `sign-in`, `api`, `licenca`

## 1. Contexto

Há dois tokens diferentes na integração, e a ADR-002 misturava os dois:

| | Token do login do ERP | Token da licença |
|---|---|---|
| Quem emite | Backend do app (`/api/v1/auth/login`) | API da StartBig (`/licenca/conectar`) |
| Assinatura | HS256, com `SECRET_KEY` do próprio backend | RS256, com chave pública da API |
| Onde fica | Front do app | Coluna `token` no SQLite |

A ADR-002 decidiu guardar o login no cofre local protegido pela DPAPI. Essa decisão não se sustenta para o login por dois motivos:

- O login é emitido pelo backend da loja e precisa chegar ao front de **terminais** também. Os terminais não têm backend local, então a DPAPI deles não existe.
- Guardar o login em disco permite que ele sobreviva a um fechamento do app, o que o dono não pediu. A regra de uso é: o sistema pede login toda vez que é aberto.

## 2. Decisão

- O token do login do ERP é guardado em **`sessionStorage`**, e não em `localStorage` nem em disco.
- Com isso ele continua disponível durante o uso, inclusive depois de recarregar a página, e some quando a janela do app fecha. Na próxima abertura, o sistema pede login.
- Vale igual para servidor e terminal. Não há rota de backend para guardar o login.
- O token continua indo no cabeçalho `Authorization: Bearer` (a parte da ADR-002 que se mantém).
- O cofre DPAPI (ADR-001) continua valendo para o **token da licença**, que fica no banco (SPEC-01). Não se aplica ao login.

## 3. Alternativas consideradas

| Alternativa | Por que foi descartada |
|-------------|------------------------|
| Cofre DPAPI no servidor, com rotas `/sessao/token-erp` (ADR-002 original) | Não existe para terminais, e exige rotas novas só para isso. |
| Token só em memória (variável JavaScript) | Some ao recarregar a página, o que quebra o uso normal. |
| Manter `localStorage` | Persiste entre aberturas, contra a regra de pedir login a cada abertura. |
| Cookie HTTP-only | Já descartado na ADR-002 (origem diferente entre front e backend). |

## 4. Consequências

- **Aceitas:**
  - Enquanto a janela está aberta, o token continua legível por script da página. Por isso a remoção do `v-html` (ACORDO D-17) continua necessária.
  - Recarregar a página mantém a sessão. Fechar a janela encerra.
  - Não há mais rotas `/api/v1/sessao/token-erp`. A SPEC-04 é atualizada.
- **Efeitos em outros módulos, regras e skills:**
  - `CLAUDE.md`, seção "Auth flow": deve dizer `sessionStorage`, e não `localStorage`.
  - A ADR-002 perde a parte do cofre para o login. O restante continua.

## 5. Como reverter

- Trocar para `localStorage` é simples, mas faz o login persistir entre aberturas, o que contraria a regra de uso. Se essa regra mudar, uma ADR nova registra a mudança.
- Voltar ao cofre exige as rotas da SPEC-04 original, que foram retiradas.
