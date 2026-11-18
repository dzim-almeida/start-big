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
| Chave de ativação e chave pública | SQLite, cifrados com o HWID | Mantido |
| Token da licença | SQLite, em texto puro | Cofre local com DPAPI (ADR-001) |
| Token do login do ERP | `sessionStorage`, só enquanto o app está aberto | Mantido (ADR-003) |
| Backup na nuvem | ZIP sem cifra, com o banco inteiro | ZIP cifrado com a chave de ativação (ACORDO D-03) |

## Principais arquivos

- `backend-fastapi/app/services/licenca/`: cadastro, validação, renovação, transferência, terminal e sincronização.
- `backend-fastapi/app/api/v1/endpoints/licenca.py` e `auth.py`: rotas de licença e de re-login.
- `frontend/src/modules/license/` e `frontend/src/modules/sign-in/`: telas de licença e de primeiro acesso.
- `frontend/src/shared/services/licenca.service.ts`: chamadas do front à licença.

## Decisões e documentos

- `ACORDO.md`: decisões D-01 a D-20 e o mapeamento das specs.
- `adr/ADR-001-cofre-local-dpapi.md`: segredos locais protegidos pela DPAPI do Windows.
- `adr/ADR-002-login-bearer-cofre.md`: login com Bearer. A parte do cofre foi substituída.
- `adr/ADR-003-token-login-session-storage.md`: token do login só em `sessionStorage`, para servidor e terminal.

## Situação

Correções de segurança e de re-login planejadas, ainda não implementadas. A primeira spec é a SPEC-01 (cofre e backup cifrado), que aguarda aprovação. Os itens que mexem na API ficam para depois do acesso ao repositório `plataformaADM`.
