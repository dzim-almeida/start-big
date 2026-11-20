# Licença — Histórico de alterações

> Acumulado, mais recente no topo. Uma entrada por spec concluída (ou por mudança de comportamento na trilha leve). Skill `doc` §7.2.

## 2026-11-20 — SPEC-08 Avisos de licença e de backup

**Módulos afetados:** licenca, cloud, backup (rota), core (permissões e tarefas), front mainLayout e configuracoes

### Adicionado
- `services/cloud/ultimo_ciclo.py`: guarda em memória o código e o horário do último ciclo de envio para a nuvem.
- `GET /api/v1/backup/avisos` (Master): aviso do último ciclo (com `feito_em` no trial) e `PASTA_DADOS_ABERTA`.
- Faixa "O relógio deste computador está atrasado" em todas as telas, sem botão de fechar (D-05).
- "(estimado, sem internet)" ao lado dos dias no badge da licença.
- Quadros de aviso na tela de backup, com "Assinar" no aviso do trial.

### Alterado
- O ciclo de envio bloqueado devolve o `codigoBloqueio` e a data do último full; o loop registra o resultado de cada ciclo.
- `core/permissoes.py` guarda o resultado da verificação da pasta de dados para a tela.

### Decisões
- Faixa em componente próprio, `feito_em` no aviso do trial e `sync.py` devolvendo o motivo (aprovados pelo usuário; Revisão 4 da SPEC-08).

## 2026-11-20 — SPEC-03 Re-login, restauração pelo titular e avisos de troca

**Módulos afetados:** licenca (backend), backup (`restore.py`), acesso (`/auth/reconnect`, `/auth/setup`), sistema (setup), front sign-in e license

### Adicionado
- `POST /api/v1/licenca/restaurar-backup`: o titular que confirma a senha restaura o backup da nuvem; o ciclo vem do full confirmado mais recente do `/status` (D-07, D-36). Códigos `LICENCA_DE_OUTRA_CONTA`, `BACKUP_INEXISTENTE`, `RESTAURACAO_JA_PENDENTE`.
- `POST /api/v1/licenca/reenviar-link`: repassa o reenvio à nuvem, sempre `202`.
- `services/licenca/titular_nuvem.py` (GET/PUT do titular com a rede de segurança do `404`) e `restauracao_titular.py`.
- Front: telas "Sua licença foi encontrada" (com e sem backup), "Restauração preparada" e "Confirme o seu e-mail"; "Reenviar link" no re-login; aviso antes da troca de servidor; `lerErroDaLicenca`, `MENSAGENS_DE_CODIGO` e `mensagemDoCodigo`.

### Alterado
- `/auth/reconnect` devolve `backup` e `titular` quando o banco não tem empresa.
- Setup depois do re-login sem backup: atualiza o titular na nuvem antes de criar a empresa local; documento e tipo de pessoa vêm da nuvem (D-22).
- Cadastro manda `fluxoConfirmacao: true`; o `202` da nuvem vira `409 CONFIRMACAO_NECESSARIA` no setup, sem gravar nada (D-23, D-34).
- O login da conta repassa `AGUARDANDO_CONFIRMACAO_EMAIL`, `MUITAS_TENTATIVAS`, `LICENCA_VENCIDA` e `SEM_LICENCA_ATIVA`.
- Telas do re-login e da transferência mostram a frase fixa do código, nunca o texto do servidor (D-16).

### Decisões
- Cinco lacunas de contrato decididas com o usuário (Revisão 4 da SPEC-03). Quadro 2 sem botão de reinício: o app não tem como religar o serviço do backend.

## 2026-11-20 — SPEC-04 Rede da loja, token do login e superfície do front

**Módulos afetados:** core (backend), acesso e sessão (front), shared (modal de confirmação), configuracoes, enterprise, financeiro, minha-conta, marcenaria, order-service, instalador NSIS, Tauri

### Adicionado
- `core/rede_local.py`: `REDES_DA_LOJA` e o middleware `ExigirRedeDaLoja`, que responde `403 FORA_DA_REDE_DA_LOJA` (formato `error` + `detail`) a quem não é das redes privadas, do `169.254/16` nem do próprio computador (D-21).
- `shared/services/tokenSessao.service.ts`: único dono do token do login, na `sessionStorage`; apaga o token antigo do `localStorage` ao abrir (D-27, ADR-003).
- `shared/types/confirmacao.types.ts`: descrição do modal em trechos (`{ negrito }`), sem HTML.

### Alterado
- CORS com a lista fechada `ORIGENS_PERMITIDAS` (`core/config.py`), métodos e cabeçalhos explícitos (inclui `X-Terminal-HWID`) (D-18).
- Firewall: `StartBig-Server` e `StartBig-mDNS` criadas pelo backend com `remoteip` da lista; o instalador recria a `StartBigERP_API_Server` com `remoteip` e restringe as duas do backend com `set rule` (D-21).
- `BaseConfirmModal` sem `v-html`; os 13 chamadores que mandavam HTML usam trechos ou o slot (D-17). Saiu o `textoSeguro.ts` da marcenaria.
- Permissões do Tauri: só `core:default`, `opener:default`, `opener:allow-open-path`, `dialog:allow-save` e `fs:allow-write-file` (D-20).

### Corrigido
- Contas a pagar e a receber punham a descrição digitada no modal sem escapar (XSS).

### Decisões
- Descrição em trechos nos 11 chamadores fora da lista e `set rule` no instalador (aprovados pelo usuário; Revisão 2 da SPEC-04).

## 2026-11-20 — SPEC-06 API: conta e cadastro (plataforma)

**Módulos afetados:** API StartBig e painel web (fork `dzim-almeida/plataformaADM`, branch `fix/licenca-seguranca`, commit `9b7ba47`)

### Adicionado
- `GET /erp/auto-cadastro/confirmar` e a página `confirmar-cadastro`: a licença de teste nasce na confirmação do e-mail (D-24).
- `POST /erp/auth/reenviar-link`: sempre `202`, um envio por minuto, link escolhido pelo estado da conta (D-31, R-01).
- `GET` e `PUT /erp/usuario/titular`, com o documento travado (D-22, D-28).
- Campos novos e opcionais em `Cliente` (confirmação, bloqueio de login, `tokenSenha` em hash, último envio de link).

### Alterado
- Cadastro pelo app: resposta única, `202` (app novo) ou `409 CONFIRMACAO_NECESSARIA` (versões instaladas); nunca cria licença nem manda a chave (D-23, D-31, D-34).
- Login: bloqueio progressivo (1, 5, 15 min), `CREDENCIAIS_INVALIDAS` também para conta sem senha, `AGUARDANDO_CONFIRMACAO_EMAIL` para conta sem licença com confirmação pendente (D-09, D-32).
- Primeiro acesso procura só pelo hash em `tokenSenha` (D-35).

### Decisões
- A contratação paga do site continua criando conta e licença na hora, sem confirmação (aprovado pelo usuário; ACORDO §7).

## 2026-11-19 — SPEC-09 API: vagas e heartbeat (plataforma)

**Módulos afetados:** API StartBig (fork `dzim-almeida/plataformaADM`, branch `fix/licenca-seguranca`, commit `003c167`)

### Alterado
- Sessão sem heartbeat há mais de 10 minutos não ocupa vaga, e o cron usa o mesmo prazo (D-10).
- Vaga ocupada com a licença trancada (`ocuparVagaSeCouber`, D-38).
- Troca de servidor apaga as sessões da loja antiga, menos a do servidor novo (F17).
- Heartbeat autenticado pelo token, com transição: sem token só renova e responde `404 SESSAO_INEXISTENTE` (D-37, ADR-004).

### Adicionado
- `scripts/testar-corrida-vagas.ts` para conferir a corrida num PostgreSQL de desenvolvimento.

## 2026-11-19 — SPEC-05 API: revogação, backup do servidor atual e trial (plataforma)

**Módulos afetados:** API StartBig (fork `dzim-almeida/plataformaADM`, branch `fix/licenca-seguranca`, commit `b735773`)

### Alterado
- `ErpLicencaGuard` recusa token de máquina revogada (`401 LICENCA_HWID_REVOGADO`); helper `lerTokenDaLicenca`.
- Backup (`status`, `url-upload`, `url-download`) só do servidor atual: `BACKUP_MAQUINA_REVOGADA`, `BACKUP_HWID_AUSENTE`; licença antiga grava o primeiro servidor (D-33).
- Trial com um full: `TRIAL_BACKUP_USADO` no `/status` e `BACKUP_TRIAL_LIMITE` no envio; download como o das pagas (D-06). O código `TRIAL` saiu.
- `/licenca/conectar` vencida: `402 LICENCA_VENCIDA` (F27).

## 2026-11-19 — SPEC-02 Token offline, relógio e heartbeat com token

**Módulos afetados:** licenca (backend), db (migração)

### Adicionado
- `services/licenca/relogio.py`: guarda o maior horário visto e avisa quando o relógio recua mais de 5 min (D-05). Coluna `configuracoes_licenca.ultimo_horario_visto` com a migração `l1c02r3l0g10`.
- `GET /licenca/status` ganha `aviso` (`relogio_recuou`) e `estimativa` (dias calculados aqui).
- Heartbeat manda `Authorization: Bearer <token da licença>` (D-37) e reconecta o caixa no `404 SESSAO_INEXISTENTE`, sem removê-lo nem bloquear a licença.

### Alterado
- Validação offline lê vencimento, carência, validade offline e próxima validação das claims do token assinado (D-13), e confere `licencaId` e `hwid` do token (D-15, `TOKEN_DE_OUTRA_LICENCA`).
- Caminho com internet: chave pública ilegível é buscada de novo antes de ler os módulos; sem ela, `CHAVE_CORROMPIDA` (D-14).
- Dias restantes vêm de `diasRestantes` da API quando ela manda (F26).
- Recusa `LICENCA_TRANSFERIDA` chega ao front com esse código (F27).
- Renovação em segundo plano grava as colunas de carência (F25).

### Decisões
- Reconexão do caixa feita pelo mesmo `POST /licenca/conectar`, direto do heartbeat, porque `conectar_terminal` é idempotente (Revisão 3 da SPEC-02).

## 2026-11-19 — SPEC-01 Cofre local (token e chave) e backup cifrado na nuvem

**Módulos afetados:** licenca, backup, cloud, core, fiscal (só `get_licenca_token`)

### Adicionado
- `services/licenca/cofre.py`: DPAPI do Windows no escopo de máquina, por `ctypes`, sem dependência nova (ADR-001).
- `services/licenca/segredos_licenca.py`: único ponto que lê e grava o token e a chave de ativação (prefixo `dpapi:v1:`), a migração do startup e os erros da §6.4 (`COFRE_INDISPONIVEL`, `TOKEN_ILEGIVEL`).
- `services/cloud/cifra_backup.py`: cópia do backup para a nuvem cifrada com AES-256-GCM, chave derivada da chave de ativação (HKDF), marca `SBKC1`.
- `core/permissoes.py`: confere a pasta de dados e registra `PASTA_DADOS_ABERTA` no log, sem alterar permissões.
- Cofre falso só em `test/apoio/cofre_falso.py`, ligado por fixture `autouse` no `test/conftest.py`.

### Alterado
- Cadastro, transferência, validação, terminal, heartbeat/renovação e renovação paga gravam e leem token e chave pelo cofre.
- Startup (`core/tarefas.py`) migra os segredos antigos para o cofre (idempotente, nunca derruba o boot) e verifica a pasta de dados.
- Envio para a nuvem manda a cópia cifrada (`tamanhoBytes` é o da cópia); sem a chave, o envio é adiado e nada sai em claro.
- Download decifra os arquivos `SBKC1` antes de salvar; chave errada → `422 BACKUP_CHAVE_INVALIDA` e nada é salvo. ZIP antigo (`PK`) segue como antes.
- Snapshot do backup sai com o token vazio; o banco da loja não é tocado.
- `get_licenca_token` (fiscal) abre o token pelo cofre.

### Decisões
- A chave que não abre responde `LICENCA_DE_OUTRA_MAQUINA` e não `CHAVE_ATIVACAO_ILEGIVEL`, para manter a tela de transferência (aprovado pelo usuário).
- `get_licenca_token` chama `segredos_licenca` (exceção documentada à regra de camadas, aprovada pelo usuário).
- Snapshot com `token = ''` em vez de `NULL`, porque a coluna é `NOT NULL`.
