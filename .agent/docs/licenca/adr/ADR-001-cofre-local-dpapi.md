# ADR-001 — Segredos locais protegidos pela DPAPI do Windows

- **Status:** Aceita em 2026-11-18
- **Módulos afetados:** `licenca`, `backup`, `acesso` (login do ERP), `core`

## 1. Contexto

O token da licença fica em texto puro no SQLite (`configuracao_licenca.token`). O backup na nuvem leva esse banco inteiro em claro. O projeto já tem um cofre previsto (Stronghold e keyring no front), mas ele não é usado e o Rust não registra o plugin.

O backend é um sidecar Python. Ele não consegue chamar plugins do Tauri. Qualquer solução que dependa do Tauri para entregar a chave ao backend precisaria passar o segredo entre processos.

## 2. Decisão

Os segredos locais passam a ser protegidos pela **DPAPI do Windows**, chamada diretamente pelo Python com `ctypes` (funções `CryptProtectData` e `CryptUnprotectData` da `crypt32`).

- A DPAPI cifra com uma chave ligada ao usuário do Windows. Só o mesmo usuário, na mesma máquina, consegue decifrar.
- O backend guarda o segredo cifrado pela DPAPI e decifra quando precisa. O segredo nunca aparece em texto puro no banco nem no log.
- Nenhuma dependência nova é adicionada. A DPAPI já está no sistema.
- Fora do Windows (desenvolvimento no Linux e testes), há um caminho alternativo que **não grava segredo real**: um cifrador de teste, marcado como tal, usado só quando `sys.platform` não for `win32`.

## 3. Alternativas consideradas

| Alternativa | Por que foi descartada |
|-------------|------------------------|
| Plugin de keyring no Rust (já no `package.json`) | Exige dependência nova no Rust e passar a chave do Tauri ao sidecar, o que cria um segundo caminho para o segredo. |
| Stronghold (já no `package.json`) | Mais pesado. A senha do cofre precisaria ficar no keyring, e o plugin não está registrado. |
| SQLCipher para o banco inteiro | Muda a engine e exige migração do banco de cada loja. Fica como alternativa futura (ver ACORDO, seção 7). |

## 4. Consequências

- **Aceitas:**
  - Os segredos só funcionam no Windows. No Linux, o caminho de teste não protege nada, e isso precisa ficar explícito no código.
  - Se o usuário do Windows for trocado ou o perfil for recriado, o segredo cifrado pela DPAPI não pode ser lido. A licença precisa ser reativada pelo re-login. Isso é aceitável, porque o re-login já é o caminho de recuperação.
  - A chave de ativação continua sendo a base do backup (ACORDO D-03). A DPAPI protege o que fica no computador; a chave de ativação protege o que sai dele.
- **Efeitos em outros módulos, regras e skills:**
  - Nenhuma regra do harness precisa mudar.
  - O CLAUDE.md não muda por esta ADR. Quem muda a parte de autenticação é a ADR-003, e a DPAPI passa a valer só para o token da licença.

## 5. Como reverter

- O segredo cifrado pela DPAPI fica em uma coluna dedicada. Reverter é voltar a guardar o token em texto puro, o que é um retrocesso de segurança. O caminho seguro é trocar o cifrador (por exemplo, para o keyring), não remover a cifra.
- Se a DPAPI deixar de servir, a ADR seguinte registra a substituição.
