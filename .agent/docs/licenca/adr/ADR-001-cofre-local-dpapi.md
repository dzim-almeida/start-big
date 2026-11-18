# ADR-001 — Segredos locais protegidos pela DPAPI do Windows

- **Status:** Aceita em 2026-11-18. **Revisada em 2026-11-18** (revisão de conflitos, ACORDO D-25, D-26 e D-30).
- **Módulos afetados:** `licenca`, `backup`, `core`

> **Revisão 1 (2026-11-18):** três mudanças, decididas com o usuário na revisão de conflitos das specs.
> - **Escopo de máquina (D-25, conflito 1).** A versão original usava a DPAPI "de usuário". O backend roda como SYSTEM (tarefa `StartBigServer`) e como o usuário logado (sidecar de reserva), sobre o mesmo banco, e no escopo de usuário uma conta não abriria o que a outra gravou.
> - **Token e chave de ativação (D-30, conflito 17).** O cofre passa a guardar também a chave de ativação, que hoje abre com o HWID gravado na mesma tabela.
> - **Cofre falso só nos testes (D-26, conflito 4).** Não há "modo de teste" no código do app. A tarefa não recebe `APP_ENV`, então uma regra pelo ambiente usaria a cifra fraca na loja.

## 1. Contexto

O token da licença fica em texto puro no SQLite (`configuracao_licenca.token`). A chave de ativação fica cifrada com um resumo do HWID, e o HWID fica em texto puro na mesma tabela: quem copia o banco abre a chave. Com a chave e o HWID, dá para pedir à API um token em nome do servidor da loja e baixar os backups da nuvem.

O projeto já tem um cofre previsto (Stronghold e keyring no front), mas ele não é usado e o Rust não registra o plugin.

O backend é um sidecar Python e não consegue chamar plugins do Tauri. Ele roda com duas contas do Windows sobre o mesmo banco: SYSTEM, na tarefa agendada, e o usuário logado, no sidecar de reserva.

## 2. Decisão

Os segredos locais da licença (o **token** e a **chave de ativação**) passam a ser protegidos pela **DPAPI do Windows**, chamada diretamente pelo Python com `ctypes` (funções `CryptProtectData` e `CryptUnprotectData` da `crypt32`), no **escopo de máquina** (`CRYPTPROTECT_LOCAL_MACHINE`).

- No escopo de máquina, qualquer conta **deste computador** decifra, e nenhum outro computador decifra. A tarefa (SYSTEM) e o sidecar (usuário) leem o mesmo valor.
- O backend guarda o segredo cifrado e decifra quando precisa. O segredo nunca aparece em texto puro no banco nem no log.
- Nenhuma dependência nova é adicionada. A DPAPI já está no sistema.
- O código do app (`cofre.py`) só conhece a DPAPI. O cifrador falso fica em `test/` e é ligado por uma *fixture* do pytest; ele nunca entra no `.exe`.
- O sistema sempre sobe. Se o cofre falhar, a falha aparece na operação de licença que precisou dele (SPEC-01 §6.4).

## 3. Alternativas consideradas

| Alternativa | Por que foi descartada |
|-------------|------------------------|
| Plugin de keyring no Rust (já no `package.json`) | Exige dependência nova no Rust e passar a chave do Tauri ao sidecar, o que cria um segundo caminho para o segredo. |
| Stronghold (já no `package.json`) | Mais pesado. A senha do cofre precisaria ficar no keyring, e o plugin não está registrado. |
| SQLCipher para o banco inteiro | Muda a engine e exige migração do banco de cada loja. Fica como alternativa futura (ver ACORDO, seção 7). |
| DPAPI no escopo de usuário (versão original) | O backend roda com duas contas. Uma recuperação online cobriria a troca de conta, mas pararia o PDV sem internet. |
| Chave em arquivo na pasta de dados | Fica ao lado do banco: quem copia a pasta leva os dois. |
| Escolher o cifrador pelo ambiente (`APP_ENV`, `sys.frozen`) | A cifra fraca iria dentro do `.exe`, e um erro na condição a ligaria na loja (a tarefa não recebe `APP_ENV`). |

## 4. Consequências

- **Aceitas:**
  - Os segredos só funcionam no Windows. Fora dele, as operações de licença respondem `COFRE_INDISPONIVEL`, e o resto do sistema sobe.
  - No escopo de máquina, outro usuário ou programa **deste mesmo computador** consegue decifrar. O que fica protegido é a cópia do banco (ou de um backup local) para outro computador.
  - Banco copiado para outro computador: o token e a chave não abrem, e a saída é o re-login. Reinstalar o Windows tem o mesmo efeito, e já conta como computador novo (D-08).
  - A chave de ativação continua sendo a base da cifra do backup na nuvem (ACORDO D-03). A DPAPI protege o que fica no computador; a chave de ativação protege o que sai dele.
- **Efeitos em outros módulos, regras e skills:**
  - Nenhuma regra do harness precisa mudar.
  - O `CLAUDE.md` diz que o token da licença e a chave de ativação são protegidos pela DPAPI no escopo de máquina.

## 5. Como reverter

- O segredo cifrado fica nas colunas que já existem, com o prefixo `dpapi:v1:`. Reverter é voltar a guardar em texto puro (ou cifrado pelo HWID), o que é um retrocesso de segurança. O caminho seguro é trocar o cifrador (por exemplo, para o keyring), não remover a cifra.
- Se a DPAPI deixar de servir, a ADR seguinte registra a substituição.
