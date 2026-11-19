# Licença — Histórico de alterações

> Acumulado, mais recente no topo. Uma entrada por spec concluída (ou por mudança de comportamento na trilha leve). Skill `doc` §7.2.

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
