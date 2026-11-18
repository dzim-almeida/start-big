# O backend da loja roda com duas contas do Windows sobre o mesmo banco

- **Data:** 2026-11-18
- **Módulo:** _shared
- **Spec relacionada:** LIC-01 (revisão de conflitos, conflitos 1, 2 e 4)
- **Tipo:** armadilha

## Contexto

Na revisão das specs de segurança da licença, a SPEC-01 propunha a DPAPI "de usuário" e um `icacls` com `getpass.getuser()`. Os dois quebrariam a loja, e nada no texto da spec deixava isso visível.

## Aprendizado

No servidor da loja, o mesmo banco (`data_dir`, no `%LOCALAPPDATA%` do usuário) é aberto por **duas contas**:

- a tarefa `StartBigServer`, como **SYSTEM** (`app/core/system.py:110`), que é o caminho normal;
- o sidecar de reserva, como o **usuário logado** (`frontend/src-tauri/src/backend.rs:4`), quando a tarefa não sobe.

E a tarefa **não recebe variáveis de ambiente** (`app/api/v1/api.py:71-74`): `APP_ENV` não chega a ela, então o servidor da loja parece "desenvolvimento" para quem olhar essa variável.

## Como aplicar

Antes de propor algo que dependa da conta ou do ambiente, pergunte "funciona igual como SYSTEM e como o usuário, e sem `APP_ENV`?". Em especial:

- cifra ligada ao usuário (DPAPI de usuário, keyring do usuário): use o escopo de máquina;
- permissões de arquivo (`icacls`) com o nome de quem está rodando: tranca a outra conta para fora;
- `%APPDATA%`, `%LOCALAPPDATA%` ou `getpass.getuser()` lidos dentro do backend: dão pastas e nomes diferentes nas duas contas (por isso existe o `--data-dir`);
- "modo de produção" decidido por `APP_ENV`: use `sys.frozen` junto, ou não dependa do ambiente.
