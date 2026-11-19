# Licença — Histórico de alterações

> Acumulado, mais recente no topo. Uma entrada por spec concluída (ou por mudança de comportamento na trilha leve). Skill `doc` §7.2.

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
