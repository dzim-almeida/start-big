# Licença e Assinatura (`license`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

O controle da **licença** do sistema: valida se a máquina pode usar o ERP, mostra as telas de erro de licença, permite **transferir a licença para outra máquina** e **renovar a assinatura** (cobrança gerada pela plataforma web). A licença também diz **quais módulos** a loja contratou (`FINANCEIRO`, `NFE`, `COMPRAS`...).

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/license/` — `routes.ts`, `views/` (`LicenseErrorView`, `TransferirLicencaView`, `RenovarAssinaturaView`), `components/RenovarAssinaturaModal.vue`, `composables/useRenovacaoAssinatura.ts`, `services/` (`renovacao`, `transferencia`) |
| Rotas | `/licenca-erro`, `/licenca/transferir`, `/renovar-assinatura` |
| Verificação global | `frontend/src/router/index.ts` (guard) · `shared/services/licenca.service.ts` · stores `licenca.store.ts` e `modulos.store.ts` |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/licenca.py` (`/api/v1/licenca`): `GET /status`, `POST /desconectar`, `POST /transferir`, `GET /esta-maquina`, `POST /desativar`, `GET /renovacao/periodos`, `POST /renovacao/cobranca`, `GET /renovacao/cobranca/{id}`, `POST /renovacao/revalidar` |
| Backend (regras) | `app/services/licenca/` (`validacao`, `cadastro`, `cripto`, `recusa`, `renovacao`, `sincronizacao`, `terminal`, `transferencia`, `constantes`) · `app/core/modulos.py` (`requer_modulo`) |
| Backend (banco) | `app/db/models/configuracao_licenca.py` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Licença (JWT assinado)** | Token emitido pela plataforma web, com validade (7 dias) e a lista de módulos. |
| **`LICENCA_EXPIRADA`** | Único erro que ainda deixa entrar: a pessoa loga, o sistema fica inativo e só a cobrança funciona. |
| **Licença de outra máquina** | Banco copiado para outro computador; leva a tela de transferência. |
| **`skipLicenseCheck`** | Marca de rota que não verifica licença (login, onboarding, rede, telas de licença). |
| **Módulo contratável** | `FINANCEIRO`, `FINANCEIRO_PRO`, `NFE`, `NFCE`, `NFSE`, `COMPRAS`. |

## 4. Fluxos principais

1. **Verificação:** antes de qualquer rota (exceto as com `skipLicenseCheck`), o guard chama `verificarLicenca()` no máximo a cada **5 minutos**, atualiza `modulos.store` e limpa o estado de bloqueio.
2. **Resposta da verificação:** o router decide o destino pelo status e pelo `codigo` do `403` — `LICENCA_EXPIRADA` → `licencaStore.marcarExpirada()` (entra no estado de bloqueio: o usuário loga e só a cobrança funciona); licença de outra máquina → `/licenca/transferir`; qualquer outro código → `/licenca-erro`; `404` (sem licença) → `/sign-in`. Erro de rede deixa navegar.
3. **Renovar:** escolhe período e método (a lista vem da API em `GET /licenca/renovacao/periodos`) → `POST /licenca/renovacao/cobranca` → acompanha a cobrança → `POST /renovacao/revalidar`.
4. **Transferir:** `GET /licenca/esta-maquina` mostra onde a licença está; `POST /licenca/desativar` libera a máquina antiga (incidente descrito em `docs/licenca-troca-de-servidor.md`).

## 5. Decisões de arquitetura

- **Esconder item de menu é cortesia; o controle real fica no backend** (`requer_modulo`) e no `meta.exigeModulo` das rotas.
- **Módulos que negam por padrão** (`NFE`, `NFCE`, `NFSE`, `COMPRAS`): licença sem resposta **não** libera. Os demais seguem "sem resposta, libera" para não tirar do ar o que o cliente já tinha.
- **As chaves dos módulos são imutáveis** depois do primeiro token emitido (o JWT vive 7 dias): renomear tira o recurso de todos os clientes em campo.
- O backend responde `403` com `MODULO_NAO_CONTRATADO` (e não `404`) para o dono entender que o recurso existe, mas não está contratado.

## 6. Integração com outros módulos

- **`mainLayout`:** o menu esconde o que não está contratado; o `LicencaStatusBadge` mostra a situação.
- **`fiscal`, `financeiro`, `compras`:** habilitados por módulo.
- **`network-config`/`sign-in`/`auth`:** rotas que não verificam a licença.
- **`configuracoes`:** seção "Licença".

## 7. Referências

- `docs/licenca-troca-de-servidor.md` (incidente e correção) · `backend-fastapi/docs/renovacao-assinatura-contrato-web.md`
- `frontend/src/shared/constants/modulos.constants.ts`
