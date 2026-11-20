# Índice — aprendizados compartilhados (`_shared`)

Leia este índice no início de toda tarefa (skill `doc` §2) e abra só os aprendizados cuja área bate com a tarefa. Regra de manutenção: `@/rules/session-learnings.md` §4.

> Aqui entram só aprendizados que **não** estão no `CLAUDE.md`, nas regras nem no código. Portas, sidecar, venv movida, nome do banco e papel da máquina já estão no `CLAUDE.md`.

| Aprendizado | Área | Quando abrir |
|-------------|------|--------------|
| [Middleware que filtra por IP recusa o TestClient inteiro](./2026-11-20-middleware-de-ip-e-o-testclient.md) | Testes do backend | Ao escrever teste de rota que precisa vir de outro endereço, ou se a suíte inteira der `403 FORA_DA_REDE_DA_LOJA` |
| [A suíte do backend divide a pasta de dados real e leva mais de 1 hora em série](./2026-11-19-suite-backend-lenta-e-pasta-de-dados-compartilhada.md) | Testes, ambiente do agente | Antes de rodar a suíte completa do backend, em paralelo ou numa cópia do código |
| [O backend da loja roda com duas contas do Windows](./2026-11-18-backend-roda-com-duas-contas-windows.md) | Backend, Windows, segurança | Ao mexer em cifra, permissões de arquivo, pastas do usuário ou "modo produção" no backend |

## Promovidos

Aprendizados que viraram padrão e saíram da pasta. Registre aqui o destino (`AAAA-MM-DD`: tema → onde está agora).

| Tema | Onde está |
|------|-----------|
| _(nenhum)_ | — |
