# ADR-002 — Login do ERP com Bearer, guardado no cofre local

- **Status:** Aceita em 2026-11-18
- **Módulos afetados:** `acesso`, `core`, `licenca`, front `auth`, `sign-in`, `api`

## 1. Contexto

O `CLAUDE.md` diz que os tokens do ERP ficam em cookie HTTP-only. O código faz diferente: o `access_token` é guardado no `localStorage` (`frontend/src/modules/auth/services/auth.service.ts`) e enviado em `Authorization: Bearer` (`frontend/src/api/axios.ts`). O backend (`app/core/depends.py`) lê só o cabeçalho e não lê cookie.

Qualquer script que rode na página consegue ler o `localStorage`. Uma falha de XSS entregaria o login.

## 2. Decisão

- O login continua com **Bearer**.
- O token deixa de ficar no `localStorage` e passa a ser guardado no **cofre local**, protegido pela DPAPI (ADR-001).
- O CLAUDE.md é corrigido para descrever o que o sistema faz: Bearer, com o token no cofre local.

## 3. Alternativas consideradas

| Alternativa | Por que foi descartada |
|-------------|------------------------|
| Migrar para cookie HTTP-only | O backend roda em outra origem (`127.0.0.1:8080`, enquanto o app roda no `tauri.localhost`). Cookie cruzando origem exige configuração de `SameSite` e de credenciais que complica a comunicação dentro do Tauri. |
| Híbrido: Bearer em memória e renovação no cofre | Mais complexo, com pouco ganho em relação ao cofre sozinho. |

## 4. Consequências

- **Aceitas:**
  - O token continua acessível para o script da página enquanto estiver em memória. O cofre reduz o risco porque o token não fica em armazenamento legível pelo navegador entre sessões. A proteção completa depende também da remoção do `v-html` (ACORDO D-17).
  - O CLAUDE.md muda. Essa alteração é feita depois da aprovação desta ADR, não antes.
- **Efeitos em outros módulos, regras e skills:**
  - O `CLAUDE.md` precisa de uma seção nova sobre autenticação do ERP.
  - O `axios.ts` passa a ler o token do cofre, por meio de uma camada assíncrona. Isso afeta todas as chamadas.

## 5. Como reverter

- Voltar ao `localStorage` é possível, mas é um retrocesso. Migrar para cookie exige uma ADR nova, porque muda a origem e a configuração do backend.
