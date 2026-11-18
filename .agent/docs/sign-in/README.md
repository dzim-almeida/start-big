# Primeiro acesso (`sign-in`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

É o **assistente de configuração inicial** (onboarding), na rota `/sign-in`. Na primeira vez que o sistema é aberto, ele cria a **empresa**, o **segmento de negócio**, o **responsável** (primeiro usuário) e o acesso dele. Também oferece o caminho "reconectar" para uma instalação que já existe (`ReconnectStep`).

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/sign-in/` |
| Passos do assistente | `components/steps/` (`ApresentacaoStep`, `EscolhaActionStep`, `SegmentoStep`, `LojaStep`, `ResponsavelStep`, `AcessoStep`, `ResumoStep`, `ReconnectStep`) |
| Estado do formulário | `composables/` (`useSetup`, `useSignIn`, `useLojaForm`, `useResponsavelForm`, `useAcessoForm`, `useCepLookup`) |
| Lista de segmentos | `frontend/src/shared/constants/segmentos.ts` (fonte única no frontend) |
| Backend | `backend-fastapi/app/api/v1/endpoints/auth.py` (`POST /auth/setup`, `POST /auth/reconnect`) · `endpoints/empresa.py` (`POST /empresas/imagem`) |
| Backend (regras) | `backend-fastapi/app/services/sistema/setup.py` e `segmentos.py` · `app/schemas/acesso/auth.py` (`SEGMENTOS_VALIDOS`) |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Segmento** | O ramo do cliente (`assistencia_tecnica`, `oficina_mecanica`, `lava_rapido`, `serigrafia`, `pdv`, `marcenaria`, `eletricista`, `outros`). Define quais telas e recursos aparecem. |
| **`pdv`** | Segmento sem Ordem de Serviço (loja que só vende no balcão). |
| **Onboarding** | A configuração inicial feita uma única vez. |

## 4. Fluxos principais

1. **Escolha inicial:** a tela mostra `EscolhaActionStep` (criar instalação nova ou reconectar).
2. **Instalação nova (passos 0 a 5 em `SignInView.vue`):** Apresentação → Segmento → Loja (dados da empresa, CEP) → Responsável → Acesso (e-mail e senha) → Resumo → envio ao backend.
3. **Reconectar:** `ReconnectStep` liga esta máquina a uma instalação que já existe e segue para o login.
4. **Proteção da rota:** o `beforeEnter` de `/sign-in` chama `verificarLicenca()`; se a licença é válida, o sistema já foi inicializado e o app redireciona para o login (`auth.user`). Se der 404, 403 ou erro de rede, entende que ainda não foi inicializado e libera o assistente.

## 5. Decisões de arquitetura

- **A lista de segmentos tem dois lados que precisam andar juntos:** `shared/constants/segmentos.ts` (frontend) e `SEGMENTOS_VALIDOS` em `app/schemas/acesso/auth.py` (backend; o comentário no arquivo do frontend ainda cita o caminho antigo `app/schemas/auth.py`). O TypeScript não enxerga o backend: ao criar um segmento, mexa nos dois (o próprio arquivo avisa).
- **Segmento novo só acrescenta declaração no registry** do backend (`app/core/segmentos/definicoes/`); se exigir tela nova, é falta de metadado (princípio descrito em `backend-fastapi/docs/segmento-marcenaria-plano.md`).
- Aviso: `sign-in` roda com `skipLicenseCheck`, porque a máquina ainda não tem licença.

## 6. Integração com outros módulos

- **`auth`:** é para onde o fluxo termina.
- **`enterprise`:** usa os mesmos dados da empresa (CNPJ, endereço) e o mesmo `cnpj.service`/`cep.service` de `shared/services`.
- **`license`:** a rota `/sign-in` depende da verificação de licença para saber se o sistema já foi inicializado (item 4 dos fluxos).
- **Pendência conhecida (`PEND-001`):** CNPJ alfanumérico não é aceito no cadastro da empresa (ver `backend-fastapi/docs/pendencias-sistema.md`).

## 7. Referências

- `backend-fastapi/docs/pendencias-sistema.md`
- `CLAUDE.md` — seção "Papel da máquina" (o assistente de rede é o módulo `network-config`).
