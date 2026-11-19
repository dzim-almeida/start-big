# Licença (`licenca`)

Visão geral do módulo de licença do StartBig: como o computador se liga à conta da loja na API, o que é guardado localmente e o que sai da máquina. O estado detalhado e as decisões ficam em outros arquivos desta pasta.

## O que o módulo faz

- **Cadastro:** cria a conta e a licença de teste (trial) na API.
- **Login da licença:** a cada abertura do sistema, confere a licença com a API. Sem internet, usa o token guardado e valida offline.
- **Re-login:** liga uma conta já existente a um computador novo ou a um banco vazio.
- **Troca de servidor:** passa a licença de um computador para outro.

## Onde ficam os dados

| Dado | Onde fica hoje | Destino previsto |
|------|----------------|------------------|
| Chave de ativação | SQLite, cifrada com o HWID (que fica na mesma tabela) | Cofre local com DPAPI, escopo de máquina (ADR-001, D-30) |
| Chave pública | SQLite, cifrada com o HWID | Mantido (é pública) |
| Token da licença | SQLite, em texto puro | Cofre local com DPAPI, escopo de máquina (ADR-001, D-25) |
| Token do login do ERP | `sessionStorage`, só enquanto o app está aberto | Mantido (ADR-003) |
| Backup na nuvem | ZIP sem cifra, com o banco inteiro | Cópia enviada cifrada com a chave de ativação, sem o token (ACORDO D-03) |
| Backups locais | ZIP sem cifra, ao lado do banco | Mantido, sem o token no snapshot (D-03 revista) |

## Principais arquivos

- `backend-fastapi/app/services/licenca/`: cadastro, validação, renovação, transferência, terminal e sincronização.
- `backend-fastapi/app/api/v1/endpoints/licenca.py` e `auth.py`: rotas de licença e de re-login.
- `frontend/src/modules/license/` e `frontend/src/modules/sign-in/`: telas de licença e de primeiro acesso.
- `frontend/src/shared/services/licenca.service.ts`: chamadas do front à licença.

## Decisões e documentos

- `ACORDO.md`: decisões D-01 a D-38, riscos aceitos R-01 e R-02, endpoints, códigos e o mapeamento das specs.
- `adr/ADR-001-cofre-local-dpapi.md`: token e chave de ativação protegidos pela DPAPI do Windows, no escopo de máquina.
- `adr/ADR-002-login-bearer-cofre.md`: login com Bearer. A parte do cofre foi substituída.
- `adr/ADR-003-token-login-session-storage.md`: token do login só em `sessionStorage`, para servidor e terminal.
- `adr/ADR-004-compatibilidade-api-app-instalado.md`: uma mudança de contrato da API nunca deixa uma versão instalada do app sem saída, nem abre uma porta para fugir da proteção nova.
- `learn/`: aprendizados do módulo (por exemplo, as respostas da API que o app instalado trata como bloqueio).

## Situação

Correções de segurança e de re-login planejadas, ainda não implementadas. As specs LIC-01 a LIC-09 (a LIC-07, TLS, está reservada) passaram por uma revisão de conflitos com o usuário em 2026-11-18. A primeira é a LIC-01 (cofre e backup cifrado), que aguarda aprovação. Em 2026-11-19, as specs da API (LIC-05, 06 e 09) foram conferidas linha a linha contra o código da plataforma. Elas são implementadas no fork `dzim-almeida/plataformaADM` e entregues por PR ao `aalan-big/plataformaADM`.
