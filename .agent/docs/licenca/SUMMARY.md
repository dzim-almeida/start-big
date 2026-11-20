# Licença — Resumo da implementação

_Última atualização: 2026-11-20 (SPEC-08, fim da série no start-big)_

A série de segurança e re-login da licença está implementada nos dois repositórios: LIC-01, 02, 03, 04 e 08 no start-big (branch `fix/licenca-seguranca`), e LIC-05, 06 e 09 no fork da plataforma (`dzim-almeida/plataformaADM`, branch `fix/licenca-seguranca`). A LIC-07 (TLS na rede da loja) está reservada e não tem spec.

## O que está pronto

| Área | Entrega | Spec |
|------|---------|------|
| Backend | Token e chave de ativação no cofre DPAPI (escopo de máquina); cópia do backup para a nuvem cifrada (`SBKC1`) | 01 |
| Backend | Vencimento, carência e prazos offline vindos do token assinado; relógio que recua gera aviso; dias da API; heartbeat com token | 02 |
| Backend | `POST /api/v1/licenca/restaurar-backup` (titular, ciclo pelo `/status`) e `POST /api/v1/licenca/reenviar-link` | 03 |
| Backend | `/auth/reconnect` com `backup` e `titular`; setup atualiza o titular na nuvem antes da empresa local; cadastro com confirmação (`409 CONFIRMACAO_NECESSARIA`) | 03 |
| Backend | CORS com lista fechada; middleware da rede da loja (`403 FORA_DA_REDE_DA_LOJA`); firewall com `remoteip` | 04 |
| Backend | `GET /api/v1/backup/avisos` (último ciclo de envio e pasta de dados aberta) | 08 |
| Frontend | Telas do re-login (licença encontrada, restauração preparada, confirme o e-mail), documento travado, aviso antes da troca de servidor, mensagens por código | 03 |
| Frontend | Token do login só em `sessionStorage` (`tokenSessao.service`); modal de confirmação sem `v-html` (descrição em trechos) | 04 |
| Frontend | Faixa do relógio atrasado, "(estimado, sem internet)" no badge, avisos na tela de backup | 08 |
| Tauri e instalador | Permissões exatas do front; regras de firewall só da rede da loja | 04 |
| API (plataforma) | Revogação no guard, backup só do servidor atual, trial com um backup, `402` no conectar | 05 |
| API (plataforma) | Cadastro com confirmação de e-mail, bloqueio progressivo, reenviar link, rotas do titular | 06 |
| API (plataforma) | Sessões de 10 minutos, vaga com a licença trancada, heartbeat autenticado | 09 |

## Arquivos principais

- `backend-fastapi/app/services/licenca/segredos_licenca.py` e `cofre.py` — único ponto que lê e grava token e chave (DPAPI).
- `backend-fastapi/app/services/licenca/validacao.py`, `relogio.py`, `sincronizacao.py` — validação online e offline, relógio e heartbeat.
- `backend-fastapi/app/services/licenca/transferencia.py` — login da conta, re-login e troca de servidor.
- `backend-fastapi/app/services/licenca/restauracao_titular.py` e `titular_nuvem.py` — restauração pelo titular e dados do titular na nuvem.
- `backend-fastapi/app/services/cloud/cifra_backup.py` e `ultimo_ciclo.py` — cifra da cópia na nuvem e resultado do último envio.
- `backend-fastapi/app/core/rede_local.py` e `core/permissoes.py` — rede da loja e verificação da pasta de dados.
- `frontend/src/shared/services/tokenSessao.service.ts` — dono único do token do login.
- `frontend/src/shared/services/licenca.service.ts` — `lerErroDaLicenca`, `MENSAGENS_DE_CODIGO`, `mensagemDoCodigo`.
- `frontend/src/modules/sign-in/` — re-login, restauração e confirmação de e-mail.

## Como usar / integrar

- **Mostrar um erro de licença:** `mensagemDoCodigo(lerErroDaLicenca(erro).codigo)`. Nunca o texto do servidor (D-16). Código novo entra em `MENSAGENS_DE_CODIGO` (o teste CT-17 da LIC-03 confere a lista).
- **Destacar texto num modal de confirmação:** `descricao: ['Excluir ', { negrito: nome }, '?']` ou o slot `#description`. Nunca HTML.
- **Token do login:** só pelo `tokenSessao.service` (`guardarToken`, `lerToken`, `apagarToken`).
- **Token e chave da licença:** só por `segredos_licenca` (o fiscal e a nuvem também).
- **Teste de rota que vem "de fora":** `TestClient(app, client=("8.8.8.8", 50000))`; o padrão do `conftest.py` é `127.0.0.1`.

## Pendências conhecidas

- **Sidecar e app:** regerar o sidecar (`npm run build:sidecar`) e recompilar o app (permissões do Tauri e instalador, LIC-04) antes de um instalador.
- **Verificação no Windows (não feita nesta série, sessões em Linux):** DPAPI e `Get-Acl` (LIC-01), origem da janela Tauri, permissões e firewall depois de instalar por cima (LIC-04), as telas do re-login e dos avisos no app. Os oito fluxos da verificação de integração (roteiro, passo 11) continuam abertos.
- **Formato do `historicoEventos`** do `/erp/backup/status` não foi conferido contra a API: a leitura aceita maiúsculas e minúsculas e alguns nomes de campo de data. Conferir no passo 11 (fluxo 5 e 8).
- **Botão "Reiniciar o sistema"** da restauração preparada não existe: o app não tem comando que religue o serviço do backend. A tela orienta reiniciar o computador.
- **`restaurar-backup` com o sistema em uso:** a rota segue a spec (senha da conta + licença da máquina) e não exige banco vazio. Avaliar restringir ao banco sem empresa.
- **Regra de ping** (`StartBigERP_Ping_Server`) continua aberta para qualquer endereço (fora da LIC-04).
- **ACORDO §7:** caminhos de transição da ADR-004, e-mails do painel do administrador e contratação paga sem confirmação seguem registrados como pendências da plataforma.
- **LIC-07 (TLS)**: spec ainda não escrita.
