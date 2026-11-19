# Acordo — `licenca` (correções de segurança e re-login)

> Escrito pelo agente na skill `spec` §2.2 e aprovado pelo usuário **antes** de qualquer spec. As decisões `D-NN` são citadas pelas specs e pelos testes.

**Status:** Aprovado em 2026-11-18 (D1 a D12 respondidas pelo usuário; itens técnicos da seção 2.C sem objeção). **Revisão 1 (2026-11-18):** revisão de conflitos das specs com o usuário (conflitos 1 a 18 e bloco de documentação), que acrescentou D-25 a D-31, revisou D-03, D-13, D-14, D-19, D-20, D-21 e D-22, e registrou os riscos R-02 e a verificação no `plataformaADM`. **Revisão 2 (2026-11-19):** conferência linha a linha das specs contra o código da plataforma (conflitos 19 a 30), que acrescentou D-32 a D-38, revisou D-01, D-06, D-28 e D-31, criou a ADR-004 e reviu o R-02.
**Revisão 3 (2026-11-19, implementação da LIC-01):** a chave de ativação que não abre neste computador continua respondendo `LICENCA_DE_OUTRA_MAQUINA` (o código que o app leva à tela de transferência); `CHAVE_ATIVACAO_ILEGIVEL` não é emitido. O fiscal (`get_licenca_token`) passou a abrir o token pelo cofre. Detalhes na Revisão 2 da SPEC-01.
**Branch de trabalho:** `fix/licenca-seguranca` (a partir de `origin/develop`). Só o `start-big` nesta fase.

## 1. Contexto

### 1.1. Material lido

- Análise de segurança, dados e experiência da integração start-big ↔ API StartBig (sessão desta data).
- Quadro interativo "Quadro da Licença" (38 erros, 17 etapas, 28 relações) e plano "Plano de Correção" (ordem de prioridade, três métodos por erro, roteiro).
- Harness da branch `develop`: `.agent/AGENT.md`, `rules/api-contract.md`, `skills/spec`, `skills/doc`.
- **Revisão 1:** código do `aalan-big/plataformaADM` (público), lido para conferir as claims do token, o login e as sessões.
- **Revisão 2:** fork `dzim-almeida/plataformaADM` (commit `981fa71`, igual ao original), lido linha a linha contra as specs da API.

### 1.2. Fatos do sistema que moldaram as decisões

- O token da licença é guardado em texto puro na coluna `token`: `backend-fastapi/app/db/models/configuracao_licenca.py:57`. O banco não é cifrado (`app/db/session.py:70`).
- O backup é um ZIP do snapshot inteiro, sem cifra e sem exclusão de tabela: `app/services/backup/local.py:188`.
- O guard da API só verifica assinatura e validade do token: `apps/server/src/core/guards/erp-licenca.guard.ts`. A revogação por máquina (`licencaHwidRevogado`) não é consultada no backup.
- O cofre Stronghold e o keyring existem no front, mas o Rust não registra o plugin e nenhum código os usa (`frontend/src/shared/services/system/secureStorage.service.ts`; `frontend/src-tauri/src/lib.rs`).
- O login do ERP usava `Bearer` guardado em `localStorage` (`frontend/src/api/axios.ts:14,26-28`), e o CLAUDE.md dizia cookie HTTP-only. Corrigido pela ADR-003.
- O backend é um sidecar Python. Ele não consegue chamar plugins do Tauri.
- O backend roda em `0.0.0.0` e os terminais chamam `http://IP:porta/api` (`frontend/src/api/backendUrl.ts`).

Fatos levantados na revisão 1:

- O backend roda com **duas contas** sobre o mesmo banco: a tarefa `StartBigServer` como **SYSTEM** (`app/core/system.py:110`) e o sidecar de reserva como o **usuário logado** (`frontend/src-tauri/src/backend.rs:4`). A pasta de dados fica no perfil do usuário.
- A tarefa `StartBigServer` **não recebe** `APP_ENV` (`app/api/v1/api.py:71-74`).
- A chave de ativação é cifrada com `sha256(hwid)` (`cripto.py:21`), e o HWID fica em texto puro na mesma tabela (`configuracao_licenca.py:29`). Quem copia o banco abre a chave.
- O manifest do backup fica **dentro** do ZIP (`local.py:248`, `_utils.py:65`) e é lido pelo incremental, pela limpeza, pela verificação e pela restauração.
- Há **três** regras de firewall abrindo a API e o mDNS para qualquer endereço: `StartBigERP_API_Server` (instalador), `StartBig-Server` e `StartBig-mDNS` (`system.py:46-65`).
- No app, lista de módulos vazia significa "não sei, libera" (`app/core/modulos.py:77-93`, `modulos.store.ts:43-74`), e a API manda `[]` quando não configurou a loja.
- O token da API já traz `licencaId`, `hwid`, `dataVencimento`, `emCarencia`, `dataLimiteCarencia` e `modulos` (`plataformaADM`, `dispositivo.service.ts:275-307`).
- Um segundo login seguido do mesmo computador não conta como troca e não derruba caixa (`plataformaADM`, `dispositivo.service.ts:380-382`, `802-835`).
- A sessão morta só é apagada pelo cron, com 35 minutos (`plataformaADM`, `cron.service.ts:94-98`), e a contagem de vagas conta todas as linhas.

Fatos levantados na revisão 2 (plataforma):

- O deploy de produção faz `git pull` da principal do `aalan-big/plataformaADM` e aplica o schema com `prisma db push`; a pasta `prisma/migrations` parou em maio de 2026.
- `hwidServidor` é opcional e vazio nas licenças antigas (`prisma/schema.prisma:302`).
- O start-big consulta `GET /erp/backup/status` antes de enviar e para em silêncio quando `planoPermiteBackup` é `false` (`flow.py:26-27`). A regra `motivoDeBloqueio` vale para o status, o envio e o download.
- As versões instaladas tratam todo `2xx` do cadastro como "licença criada", mostram a `message` dos `4xx`, e bloqueiam a licença quando todos os caixas recebem `400` no heartbeat.
- O cadastro também recusa CPF/CNPJ já cadastrado; o `tokenEmail` é compartilhado entre o primeiro acesso e a troca de e-mail.
- O heartbeat só pede `licencaId` e `hwid`, sem credencial, e cria sessão quando não existe.
- A API, sem ciclo, baixa a semana atual; o registro local de ciclos do start-big some junto com o banco.
- Há dois guards globais (frequência e token do painel): rotas do app precisam de `@Public()`.

## 2. Decisões

### A. Arquitetura e modelo de dados

| ID | Decisão | Motivo | Alternativa descartada |
|----|---------|--------|------------------------|
| D-01 | **(Revista no conflito 19.)** As specs da API ficam em `.agent/specs/licenca/`. Elas são implementadas no fork `dzim-almeida/plataformaADM`, uma branch por spec, e entregues por PR ao `aalan-big/plataformaADM`, de onde sai o deploy de produção. | Um único lugar de planejamento; o PR protege a produção, que faz deploy da principal do original. | Trabalhar direto no original; usar o fork como repositório definitivo. |
| D-02 | O segredo local é protegido pela **DPAPI do Windows**, chamada direto do Python por `ctypes`. Sem dependência nova. Ver **ADR-001**. O escopo é o de máquina (D-25). | O sidecar Python não chama plugins do Tauri. A DPAPI não exige dependência nova e o backend controla o próprio segredo. | Plugin de keyring no Rust (A); Stronghold (C). |
| D-03 | **(Revista no conflito 3.)** A **cópia do backup enviada à nuvem** é cifrada com chave derivada da **chave de ativação**, com a marca `SBKC1` no começo do arquivo. Os backups locais não mudam. | A chave é igual em todas as máquinas da licença, então a restauração funciona no computador novo. O manifest fica dentro do ZIP e é lido pelo motor de backup; os backups locais ficam ao lado do banco, que continua sem cifra. | Cifrar o ZIP local inteiro (quebra o incremental e a limpeza); cifrar cada arquivo do ZIP (mais código, manifest em claro). |
| D-25 | **(Conflito 1.)** A DPAPI usa o escopo **de máquina** (`CRYPTPROTECT_LOCAL_MACHINE`). | O backend roda como SYSTEM e como o usuário sobre o mesmo banco. No escopo de usuário, uma conta não abriria o que a outra gravou. | Escopo de usuário com recuperação online (para o PDV sem internet); abandonar a DPAPI (a chave ficaria ao lado do banco). |
| D-26 | **(Conflito 4.)** O cifrador falso existe só em `test/`. O `cofre.py` não tem modo de teste e não lê variável de ambiente. O sistema sempre sobe; a falha do cofre aparece na operação que precisou dele (SPEC-01 §6.4). | A tarefa não recebe `APP_ENV`: uma regra pelo ambiente usaria a cifra fraca na loja. | Escolher pelo ambiente (`sys.frozen` ou `APP_ENV`); recusar subir fora do Windows. |
| D-30 | **(Conflito 17.)** A **chave de ativação** vai para o mesmo cofre do token. | Com a chave e o HWID (os dois no banco), dá para pedir um token em nome do servidor e baixar os backups da nuvem. | Chave em arquivo na pasta de dados (copiada junto); aceitar o risco e avisar pela API. |

### B. Regras de negócio

| ID | Decisão | Motivo | Alternativa descartada |
|----|---------|--------|------------------------|
| D-04 | Validade do token continua em **7 dias**. O guard da API passa a consultar a revogação (`hwidRevogado` e `hwidServidor`) antes de aceitar o token. Redução para 24 h fica para uma etapa futura. | A revogação já é por máquina, e o guard já recebe a licença e o HWID do token. | Reduzir para 24 h agora (B); lista de tokens (C). |
| D-05 | Relógio do PC voltou no tempo: o app **avisa o dono** e segue usando até o último horário registrado. O aviso é mostrado pela LIC-08. | Bloquear o PDV no meio do expediente causa mais prejuízo que o risco de relógio manipulado. | Bloquear até reconectar (A); ignorar (C). |
| D-06 | Trial tem **um backup completo** (sem fragmentos). **(Revista no conflito 22.)** A regra única `motivoDeBloqueio` decide para o `/status`, o envio e o download: o trial sem full pode enviar um; com full, o `/status` responde `TRIAL_BACKUP_USADO`; o download segue as regras das licenças pagas. O app mostra o motivo (LIC-08). | Protege quem perde o banco nos primeiros dias sem custo alto de armazenamento. O start-big para pelo `/status`, então liberar só no envio não funcionaria. | Liberar backup completo no trial (A); só avisar (B); liberar só no envio. |
| D-07 | A restauração depois do re-login é liberada ao **titular que acabou de provar a senha**, com a senha pedida de novo na chamada. | Resolve o caso 2 sem exigir Master e sem etapa de e-mail. | Só Master com aviso (B); código por e-mail (C). |
| D-08 | Reinstalação do Windows **conta como troca** de computador, com aviso antes de confirmar. | Ver a explicação na seção 3. | Não contar quando o nome ou o ID anterior for reconhecido (B); suporte libera caso a caso (C). |
| D-09 | Limite de tentativas de senha: **bloqueio progressivo por e-mail**, com espera de 1, 5 e 15 minutos (teto de 15). | Protege a conta; o teto curto evita trancar o dono por muito tempo. | 5 tentativas por minuto por IP (A); CAPTCHA após 3 falhas (C). |
| D-10 | Sessões sem heartbeat deixam de ocupar vaga em **10 minutos**, em vez de 35 (LIC-09). | Libera vagas sem depender do dono. | Tela para liberar vagas (B), que pode vir depois; manter 35 min (C). |
| D-11 | ~~Setup com CPF ou CNPJ diferente do titular: pede confirmação explícita.~~ **Substituída pela D-22.** | — | — |

### C. Permissões e contrato da API

| ID | Decisão | Motivo | Alternativa descartada |
|----|---------|--------|------------------------|
| D-12 | O login do ERP continua com **Bearer**. O token fica só em `sessionStorage`: some ao fechar o app e não é guardado em disco. Vale igual para servidor e terminal. Ver **ADR-002** (Bearer) e **ADR-003** (armazenamento). | O backend roda em outra origem e o cookie complicaria a comunicação dentro do Tauri. | Migrar para cookie HTTP-only (B); híbrido com refresh no cofre (C). |
| D-27 | **(Conflito 5.)** Um único arquivo do front (`shared/services/tokenSessao.service.ts`) é dono do token do login. Ninguém mais usa `sessionStorage` ou `localStorage` para ele. O token antigo do `localStorage` é apagado ao abrir. | Sete pontos do front liam o token; a spec só listava três. | Trocar nos sete pontos sem arquivo único; guardar na store Pinia. |
| D-29 | **(Conflito 11.)** Erros que a tela trata por código usam `{"error": ..., "detail": {"codigo", "mensagem"}}`, como os erros de licença já fazem. Registrado em `rules/api-contract.md` §5.5. A API NestJS mantém o formato dela; o backend traduz. | Cada spec desenhava um formato; o front perderia o código. | Código no topo; formato NestJS no backend local. |

### 2.C. Decisões técnicas padrão (sem objeção do usuário)

| ID | Decisão |
|----|---------|
| D-13 | Carência, vencimento e prazo offline passam a vir do **token assinado**. O app deixa de usar as colunas para isso (F25, F7). **Conferido no `plataformaADM` (conflito 9):** o token já traz as claims. |
| D-14 | **(Revista no conflito 18.)** Os módulos **nunca são lidos com uma chave pública ilegível**: com internet, o app busca a chave de novo (como o caminho offline já faz); se não conseguir, `CHAVE_CORROMPIDA`. A lista vazia continua significando "não sei" (F8). |
| D-15 | O app confere `licencaId` e `hwid` do token com a licença local e a máquina (F24). |
| D-16 | Erros de tela saem por código, nunca com o texto da exceção (F10). A lista completa de mensagens fica na SPEC-03 §6.4. |
| D-17 | `v-html` dos modais é trocado por texto escapado (F35). |
| D-18 | CORS com lista fechada de origens, fixa em `core/config.py`, sem variável de ambiente (F1). |
| D-19 | **(Revista no conflito 2.)** O backend **verifica** as permissões da pasta de dados e avisa (`PASTA_DADOS_ABERTA`), sem alterá-las (F37). A pasta padrão fica no perfil, que o Windows já restringe. |
| D-20 | **(Revista no conflito 6.)** Permissões do Tauri restritas à lista exata que o código usa, com `fs:allow-write-file` e sem `shell` (F38). |
| D-21 | Rede da loja: a API local só aceita conexões das redes da loja (`10/8`, `172.16/12`, `192.168/16`, `169.254/16`), por firewall e por verificação no app (F34, opção A). **Revista no conflito 12:** as três regras de firewall são recriadas com a mesma lista do middleware, sem `LocalSubnet`, e um teste compara as listas. TLS (opção C) fica para a LIC-07. |
| D-22 | Re-login não passa pelo setup. Com backup, a tela só oferece restaurar. Sem backup, o setup abre com os dados da nuvem, o documento do titular fica travado, e a nuvem é atualizada **antes** de a empresa local ser criada. Substitui o D-11. **Revista no conflito 16:** o documento nunca vai para a nuvem (lista fechada de campos) e a empresa local recebe o documento da nuvem, não da tela. |
| D-23 | Depois da confirmação de e-mail, a chave de ativação do cadastro novo é obtida pelo login com e-mail e senha (re-login). O cadastro não devolve a chave. Login antes da confirmação responde `AGUARDANDO_CONFIRMACAO_EMAIL`. |
| D-24 | O trial só começa depois da confirmação do e-mail. Sem confirmação, não há licença criada para o cadastro. |
| D-28 | **(Conflito 8; caminho revisto no conflito 29.)** O setup busca os dados do titular por `GET /erp/usuario/titular` e os atualiza por `PUT /erp/usuario/titular` (LIC-06), no controller que já existe. Se a rota responder `404`, o setup funciona como hoje, só local, e a LIC-03 pode ir para produção antes da LIC-06. |
| D-31 | **(Conflito 14; revista nos conflitos 24 e 30.)** O cadastro responde sempre da mesma forma, sem revelar se o e-mail **ou o CPF/CNPJ** já existe. Documento repetido: nada é criado, o solicitante recebe uma orientação e o titular recebe um alerta, por e-mail. A rota `POST /erp/auth/reenviar-link` escolhe o link pelo estado da conta (confirmação ou nova senha). Nenhum e-mail **do cadastro pelo app** leva a chave de ativação. |
| D-32 | **(Conflito 20.)** Os campos novos da plataforma são opcionais e aplicados pelo `db push`, sem script de dados. `AGUARDANDO_CONFIRMACAO_EMAIL` só vale para conta **sem nenhuma licença** e com confirmação pendente, então os clientes de hoje nunca são barrados. |
| D-33 | **(Conflito 21.)** Licença com `hwidServidor` vazio: a primeira chamada de backup grava o HWID do token como servidor, de forma condicional (só se ainda estiver vazio). |
| D-34 | **(Conflito 23, ADR-004.)** O app novo manda `fluxoConfirmacao: true` no cadastro e recebe `202`. Sem o campo, a API faz o mesmo (exige a confirmação) e responde `409 CONFIRMACAO_NECESSARIA` com uma instrução que a versão instalada mostra. |
| D-35 | **(Conflito 25.)** Um campo de token por finalidade, em hash: `tokenSenha` (primeiro acesso e nova senha) e `tokenConfirmacaoEmail` (cadastro). O `tokenEmail` fica só para a troca de e-mail. |
| D-36 | **(Conflito 26.)** A restauração sem ciclo informado descobre o ciclo mais recente com full confirmado pelo `historicoEventos` do `/erp/backup/status`. |
| D-37 | **(Conflito 27, ADR-004.)** O heartbeat é autenticado pelo token da licença. Na transição, o pedido sem token só renova sessão existente e nunca cria; sessão inexistente → `404 SESSAO_INEXISTENTE`. Nenhuma recusa nova do heartbeat usa `400`. |
| D-38 | **(Conflito 28.)** Ocupar uma vaga tranca a linha da licença (`SELECT ... FOR UPDATE`) enquanto conta e grava. A corrida real é testada por script contra um PostgreSQL de desenvolvimento. |

## 3. Consequências

- **D-02, D-25, D-26, D-30:** o backend passa a depender da DPAPI, que só existe no Windows. Os testes usam o cofre falso de `test/`. Com o escopo de máquina, outro usuário do mesmo computador consegue abrir os segredos; o que fica protegido é a cópia do banco para outro computador.
- **D-03:** os backups enviados antes da LIC-01 continuam em claro na nuvem até expirarem. O download entende os dois formatos pela marca do começo do arquivo.
- **D-08 (explicação):** o identificador da máquina no Windows (MachineGuid) muda quando o Windows é reinstalado. Para a nuvem, é um computador novo. Sem o aviso, o dono pode gastar as trocas do mês (3 em 30 dias) sem perceber e depois ficar bloqueado até falar com o suporte.
- **D-12:** o CLAUDE.md mudou. A ADR-003 substitui a parte do cofre da ADR-002.
- **D-29:** a regra `api-contract.md` ganhou a seção 5.5, e a "decisão pendente" sobre o formato de erro saiu da lista dela.
- **D-32:** os clientes que já têm licença não precisam de nenhum preenchimento: a regra do login olha a licença.
- **D-34, D-37 e ADR-004:** a plataforma carrega, por um tempo, dois comportamentos para o cadastro e para o heartbeat. Cada um tem data para acabar (seção 7).
- **D-35:** os links de primeiro acesso enviados antes da LIC-06 deixam de valer; o dono pede outro pelo "Reenviar link".

## 4. Endpoints e códigos de erro

### 4.1. Rotas

| Método e rota | Onde | Spec |
|---------------|------|------|
| `POST /api/v1/licenca/restaurar-backup` (nova) | start-big | LIC-03 §4.1 |
| `GET /api/v1/backup/avisos` (nova) | start-big | LIC-08 §4.1 |
| `POST /erp/auto-cadastro` (muda: sempre `202`) | API | LIC-06 §4.1 |
| `GET /erp/auto-cadastro/confirmar` (nova) | API | LIC-06 §4.2 |
| `POST /erp/auth/login` (muda os erros) | API | LIC-06 §4.3 |
| `POST /erp/auth/reenviar-link` (nova) | API | LIC-06 §4.4 |
| `GET /erp/usuario/titular` (nova) | API | LIC-06 §4.5 |
| `PUT /erp/usuario/titular` (nova) | API | LIC-06 §4.6 |
| `POST /licenca/conectar` (muda o vencimento para `402 LICENCA_VENCIDA`) | API | LIC-05 §4.5 |
| `GET /erp/backup/status`, `url-upload`, `url-download` (mudam: servidor atual e trial) | API | LIC-05 §4.2, §4.4 |
| `POST /licenca/heartbeat` (muda: token opcional, com transição) | API | LIC-09 §4.1 |

### 4.2. Códigos novos

| Código | Status | Onde nasce | Spec |
|--------|--------|------------|------|
| `COFRE_INDISPONIVEL` | 503 | start-big | LIC-01 |
| `TOKEN_ILEGIVEL` | 403 | start-big | LIC-01 |
| ~~`CHAVE_ATIVACAO_ILEGIVEL`~~ | — | start-big | LIC-01 (**não emitido**, Revisão 3: a chave que não abre responde `LICENCA_DE_OUTRA_MAQUINA`) |
| `BACKUP_CHAVE_INVALIDA` | 422 | start-big | LIC-01 |
| `PASTA_DADOS_ABERTA` | aviso (log e tela) | start-big | LIC-01, LIC-08 |
| `TOKEN_DE_OUTRA_LICENCA` | 403 | start-big | LIC-02 |
| `LICENCA_DE_OUTRA_CONTA` | 403 | start-big | LIC-03 |
| `BACKUP_INEXISTENTE` | 404 | start-big | LIC-03 |
| `RESTAURACAO_JA_PENDENTE` | 409 | start-big | LIC-03 |
| `FORA_DA_REDE_DA_LOJA` | 403 | start-big | LIC-04 |
| `LICENCA_HWID_REVOGADO` | 401 | API | LIC-05 |
| `BACKUP_MAQUINA_REVOGADA` | 403 | API | LIC-05 |
| `BACKUP_HWID_AUSENTE` | 403 | API | LIC-05 |
| `BACKUP_TRIAL_LIMITE` | 403 | API | LIC-05 |
| `LICENCA_VENCIDA` | 402 | API (já existe no login; passa a valer no `conectar`) | LIC-05 |
| `TOKEN_CONFIRMACAO_INVALIDO` | 400 | API | LIC-06 |
| `TOKEN_CONFIRMACAO_EXPIRADO` | 410 | API | LIC-06 |
| `MUITAS_TENTATIVAS` | 429 | API | LIC-06 |
| `AGUARDANDO_CONFIRMACAO_EMAIL` | 403 | API | LIC-06 |
| `DOCUMENTO_TRAVADO` | 403 | API | LIC-06 |
| `CONFIRMACAO_NECESSARIA` | 409 | API (versões instaladas no cadastro) | LIC-06 |
| `TRIAL_BACKUP_USADO` | `codigoBloqueio` do `/status` | API | LIC-05 |
| `SESSAO_INEXISTENTE` | 404 | API (heartbeat sem token) | LIC-09 |
| `HEARTBEAT_LICENCA_DIVERGENTE` | 403 | API | LIC-09 |

Códigos que saem: `E_MAIL_JA_CADASTRADO` (D-31), `TOKEN_SESSAO_INVALIDO` (R-02) e `TRIAL` (substituído por `TRIAL_BACKUP_USADO`). `SENHA_NAO_CONFIGURADA` passa a ser `CREDENCIAIS_INVALIDAS` (LIC-06).

## 5. Mapeamento das specs

| Ordem | Arquivo | Camada | Conteúdo | Depende de |
|-------|---------|--------|----------|------------|
| 1 | `SPEC-01-COFRE-LICENCA.md` | Backend | D-02, D-03, D-19, D-25, D-26, D-30 (F30, F31, F36, F37) | — |
| 2 | `SPEC-02-TOKEN-OFFLINE.md` | Backend | D-05, D-13, D-14, D-15 (F7, F8, F24, F25, F26, F27) | 1 |
| 3 | `SPEC-04-REDE-E-FRONT.md` | Front, Backend, NSIS e Tauri | D-12, D-17, D-18, D-20, D-21, D-27, D-29 | — |
| 4 | `SPEC-03-RE-LOGIN.md` | Backend e front | D-07, D-08, D-16, D-22, D-23, D-28, D-29, D-31 | 1, 2 (integração com 7) |
| 5 | `SPEC-08-AVISOS-LICENCA-BACKUP.md` | Backend e front | D-05, D-06, D-19 (avisos ao dono) | 1, 2 (integração com 6) |
| 6 | `SPEC-05-API-REVOGACAO.md` | API (fork → PR) | D-01, D-04, D-06, D-33 | — |
| 7 | `SPEC-06-API-CONTA-CADASTRO.md` | API e painel web (fork → PR) | D-09, D-22, D-23, D-24, D-28, D-31, D-32, D-34, D-35; R-01 | 6 |
| 8 | `SPEC-09-API-VAGAS-SESSOES.md` | API (fork → PR) | D-10, D-37, D-38 (F6, F17, F21) | 6; tarefa do heartbeat |
| — | LIC-07 (TLS) | Rede da loja | F34, opção C | Reservada, fora desta série |

A ordem detalhada fica no `specs/licenca/ROTEIRO-IMPLEMENTACAO.md`.

## 6. Pontos pendentes

- **Aberto:** nenhuma pergunta.
- **Risco aceito R-01 (2026-11-18):** a senha é definida no cadastro, antes da confirmação do e-mail. Se alguém cadastrar o e-mail de outra pessoa com a própria senha, o dono confirma o link, mas a senha que vale é a do atacante. **Mitigação exigida:** o `reenviar-link` permite ao dono definir uma nova senha, mesmo com senha já cadastrada (LIC-06, CT-16).
- **Risco aceito R-02 (2026-11-18, conflito 7; revisto em 2026-11-19, conflito 27):** o desconectar continua sem `tokenSessao` (F5). Quem tiver a chave de ativação consegue derrubar sessões. **Mitigação:** a D-30 tira a chave do alcance de quem copia o banco, e a D-10 limita o efeito de uma vaga presa a 10 minutos. A revisão 2 achou uma segunda porta, o heartbeat sem credencial, fechada pela D-37: sem token, ninguém cria sessão. Se um dia for preciso, o `tokenSessao` vira spec própria.
- **Fechado em 2026-11-18 (revisão 1):** verificação no `plataformaADM`. As claims do token existem (conflito 9), o segundo login do mesmo computador não tem efeito colateral (conflito 10), e os caminhos de arquivo citados pelas specs da API foram conferidos.
- **Fechado em 2026-11-18:** trial só depois da confirmação de e-mail (D-24); chave do cadastro novo pelo login (D-23); comparação de documento (D-11) substituída pelo D-22; rede da loja, opção A (D-21); token do terminal (ADR-003).
- **Fechado em 2026-11-19 (revisão 2):** conferência das specs contra o fork da plataforma (conflitos 19 a 30), com as decisões D-32 a D-38 e a ADR-004.
- **Próxima etapa:** aprovação da LIC-01 (cofre e backup). Só começa com a aprovação explícita da spec.

## 7. Fora do escopo (registrado)

- TLS na rede da loja com certificado próprio (F34, opção C) — **LIC-07**, spec própria depois da LIC-04. Exige IP ou nome estável na loja e instalação da autoridade da loja em cada caixa.
- SQLCipher para o banco inteiro (F30 alternativa B) — pode voltar se o cofre não for suficiente.
- Lista de tokens revogados por `jti` (D-04, alternativa C) — só se for preciso revogar um token específico.
- Tela de liberação manual de vagas (D-10, alternativa B) — depois de medir se o expurgo automático basta.
- Reduzir a validade do token para 24 h (D-04, alternativa B) — depois do guard ser validado.
- `tokenSessao` no desconectar (F5) — risco aceito R-02.
- Desligar os caminhos de transição da ADR-004 — o `409 CONFIRMACAO_NECESSARIA` do cadastro e o heartbeat sem token (que passará a `401`) — quando as lojas tiverem atualizado o app. Cada um é uma decisão nova.
- **E-mails do painel do administrador** ainda mandam a chave de ativação (`criarLicenca`, `renovar` em `dispositivo.service.ts`, e o cadastro de cliente em `cliente.service.ts:187`). O app não usa a chave digitada. Avaliar em PR próprio da plataforma (conflito 30).
- **Achado na plataforma, a avisar quem a mantém:** `GET /erp/usuario/confirmar-email` tem `@Public()`, mas está sob o `@UseGuards(ErpLicencaGuard)` da classe (`erp-usuario.controller.ts:11-13`), que exige o token da licença. Quem clica no link pelo navegador não tem esse token, então a confirmação de troca de e-mail provavelmente responde `401` sempre (conflito 25).
- `Cliente.email` não é único no banco da plataforma: dois cadastros simultâneos com o mesmo e-mail podem criar duas contas (LIC-06 §5).
- Trocar a tarefa `StartBigServer` (SYSTEM) por programa de inicialização do usuário — avaliado e recusado na revisão 1, porque o servidor deixaria de ligar sem login (atualização do Windows de madrugada) e cada usuário do Windows teria o seu banco. Fica como ideia para spec futura: mostrar no painel de Rede e Conexão se o servidor está rodando, com botão de reiniciar.
