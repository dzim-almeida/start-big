# Licença 01 — Cofre local e backup cifrado

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend (FastAPI), com verificação no Windows |
| Dependências | — |
| Bloqueia     | SPEC-02, SPEC-03, SPEC-04 |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-02, D-03, D-19; [ADR-001](../../docs/licenca/adr/ADR-001-cofre-local-dpapi.md); quadro F30, F31, F37 e F36 |

## 1. Objetivo

Tirar o token da licença e o banco de dados do estado de texto puro. O token passa a ser guardado cifrado com uma chave que só o Windows entrega, pela DPAPI. O backup enviado à nuvem passa a ser cifrado com uma chave derivada da chave de ativação da licença, para que a restauração funcione em outro computador da mesma licença.

Por que isso importa: hoje quem copiar o arquivo do banco leva o token, e o backup na nuvem leva o banco inteiro com o token em claro.

## 2. Escopo

**Dentro do escopo**
- Criar o cofre local com a DPAPI, chamada pelo Python com `ctypes`, sem dependência nova (ADR-001).
- Guardar o token cifrado na coluna `token` que já existe. Não há mudança de schema.
- Migração de dados no startup: token ainda em texto puro é cifrado uma vez. A migração é idempotente.
- Snapshot do backup sem o token.
- ZIP do backup cifrado com chave derivada da chave de ativação (D-03), com indicação de formato no manifest.
- Restauração que entende o formato novo e o antigo.
- Restrição de permissões do banco e da configuração ao usuário do Windows (D-19).

**Fora do escopo**
- Criptografia do banco inteiro com SQLCipher. Registrada como alternativa futura no ACORDO, seção 7.
- Restauração liberada ao titular (D-07). Fica na SPEC-03.
- Qualquer tela do front. O front não muda nesta spec.
- Mudança no contrato de nenhuma rota da API.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/services/licenca/cofre.py` | criar | Funções `proteger(bytes)` e `desproteger(bytes)` pela DPAPI. Fora do Windows, cifrador de teste marcado, recusado em produção. |
| `backend-fastapi/app/services/licenca/token_local.py` | criar | `guardar_token(token) -> str` e `ler_token(valor) -> str`. Único ponto que lê e escreve o token no banco. |
| `backend-fastapi/app/services/licenca/cripto.py` | alterar | Acrescentar `encriptar_com_chave` e `decriptar_com_chave` (AES-256-GCM com chave já pronta), para o ZIP. As funções atuais por HWID continuam. |
| `backend-fastapi/app/services/licenca/cadastro.py` | alterar | Gravar o token com `guardar_token` (criação da licença, linha ~240). |
| `backend-fastapi/app/services/licenca/transferencia.py` | alterar | Gravar o token com `guardar_token` (`_gravar_ativacao`, linha ~172). |
| `backend-fastapi/app/services/licenca/validacao.py` | alterar | Gravar com `guardar_token` (linha ~56). Ler com `ler_token` em `_validar_offline` e em `modulos_da_licenca`. |
| `backend-fastapi/app/services/licenca/sincronizacao.py` | alterar | Gravar com `guardar_token` (linha ~190). |
| `backend-fastapi/app/services/licenca/renovacao.py` | alterar | Gravar com `guardar_token` (linha ~439). |
| `backend-fastapi/app/services/cloud/_http.py` | alterar | `_get_license_token` passa a usar `ler_token`. Sem token legível, a chamada falha com erro claro. |
| `backend-fastapi/app/services/backup/_utils.py` | alterar | `_create_snapshot_db` zera `configuracoes_licenca.token` no snapshot, sem mexer no banco real. |
| `backend-fastapi/app/services/backup/local.py` | alterar | `create_backup` cifra o ZIP antes de gravar, quando houver chave de ativação. Marca `formato: 2` e `cifrado: true` no manifest. |
| `backend-fastapi/app/services/backup/restore.py` | alterar | Antes de abrir o ZIP, decifra quando `cifrado: true`. Backups `formato: 1` seguem como hoje. |
| `backend-fastapi/app/services/backup/_constants.py` | alterar | Constantes `FORMATO_BACKUP_ATUAL = 2` e o rótulo de cada formato. |
| `backend-fastapi/app/core/tarefas.py` | alterar | No startup, chama a migração de dados do token (idempotente). |
| `backend-fastapi/app/core/permissoes.py` | criar | Restringe ao usuário atual a ACL do banco e da pasta de configuração (D-19), com `icacls`. Fora do Windows, não faz nada. |
| `backend-fastapi/test/services/licenca/test_cofre_token.py` | criar | Casos CT-01 a CT-06. |
| `backend-fastapi/test/services/backup/test_backup_cifrado.py` | criar | Casos CT-07 a CT-12. |

Os arquivos de teste existentes que cobrem a mudança precisam continuar passando sem alteração de contrato: `backend-fastapi/test/api/v1/test_backup_preserva_licenca.py` e `backend-fastapi/test/api/v1/test_licenca_transferencia.py`.

## 4. Contrato da API

Nenhuma rota nova nem alterada nesta spec.

O formato do backup muda. O manifest ganha dois campos:

| Campo | Tipo | Significado |
|-------|------|-------------|
| `formato` | inteiro | `1` é o backup antigo (ZIP em claro). `2` é o backup cifrado. |
| `cifrado` | booleano | `true` quando o ZIP está cifrado. |

Erros internos novos, sempre com `codigo` estável (api-contract, seção 3):

| Código | Quando | Tratamento |
|--------|--------|------------|
| `COFRE_INDISPONIVEL` | DPAPI falhou ou o sistema não é Windows em produção | Erro 500 no startup, com mensagem de suporte |
| `TOKEN_ILEGIVEL` | O token guardado não decifra nesta máquina ou usuário | Erro 403 em `/licenca/...`, orientando o re-login |
| `BACKUP_CHAVE_INVALIDA` | Restauração com chave de ativação que não confere | Erro 422, sem alterar o banco |

## 5. Schemas

Nenhum schema Pydantic novo para a API. O manifest é um JSON interno, com os campos da seção 4.

## 6. Especificação técnica

### 6.1. Cofre pela DPAPI (`cofre.py`)

A DPAPI cifra com uma chave ligada ao usuário do Windows. Só o mesmo usuário, na mesma máquina, consegue decifrar. O Python chama as funções da `crypt32.dll` por `ctypes`:

```python
# cofre.py — guarda e lê segredos pela DPAPI do Windows (ADR-001)
import ctypes                      # biblioteca para chamar funções de DLLs do Windows
import sys                         # para saber em qual sistema operacional estamos
from ctypes import wintypes        # tipos que o Windows usa (inteiros, ponteiros)


class _DataBlob(ctypes.Structure):
    """Estrutura que a DPAPI usa para passar bytes de entrada e de saída."""
    _fields_ = [("cbData", wintypes.DWORD),               # quantos bytes existem
                ("pbData", ctypes.POINTER(ctypes.c_byte))]  # endereço dos bytes


def _blob_de(dados: bytes) -> _DataBlob:
    # Cria um blob apontando para os bytes recebidos.
    buffer = ctypes.create_string_buffer(dados, len(dados))
    return _DataBlob(len(dados), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))


def proteger(dados: bytes) -> bytes:
    """Cifra os bytes com a DPAPI. Só este usuário nesta máquina consegue ler."""
    if sys.platform != "win32":
        raise RuntimeError("DPAPI só existe no Windows. Use o cifrador de teste.")
    entrada = _blob_de(dados)
    saida = _DataBlob()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida))
    if not ok:
        raise RuntimeError("COFRE_INDISPONIVEL: a DPAPI recusou a cifra.")
    return ctypes.string_at(saida.pbData, saida.cbData)


def desproteger(dados: bytes) -> bytes:
    """Decifra os bytes. Falha se a máquina ou o usuário forem outros."""
    if sys.platform != "win32":
        raise RuntimeError("DPAPI só existe no Windows. Use o cifrador de teste.")
    entrada = _blob_de(dados)
    saida = _DataBlob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida))
    if not ok:
        raise RuntimeError("TOKEN_ILEGIVEL: não foi possível decifrar nesta máquina.")
    return ctypes.string_at(saida.pbData, saida.cbData)
```

Ponto de atenção: `CryptProtectData` devolve memória que o Windows aloca. Em produção, o código também deve liberar essa memória com `LocalFree`. A spec exige isso no código final, com um comentário explicando.

Cifrador de teste: fora do Windows, a função `proteger` pode usar AES-GCM com uma chave fixa **somente dentro dos testes**. Fora dos testes, sem Windows, o backend recusa iniciar em modo de produção. A variável `APP_ENV=production` já existe e serve de referência.

### 6.2. Token guardado (`token_local.py`)

O token é guardado em base64 para caber na coluna de texto, com um prefixo que diz o formato:

```python
# token_local.py — único lugar que lê e grava o token da licença no banco
import base64                      # transforma bytes em texto seguro para o banco
from app.services.licenca.cofre import proteger, desproteger

PREFIXO = "dpapi:v1:"              # marca que o valor já está cifrado


def guardar_token(token: str) -> str:
    """Devolve o texto que deve ser gravado no banco."""
    cifrado = proteger(token.encode("utf-8"))            # cifra os bytes do token
    return PREFIXO + base64.b64encode(cifrado).decode()  # guarda com o prefixo


def ler_token(guardado: str | None) -> str | None:
    """Decifra o token lido do banco. Token antigo, em texto puro, é devolvido como está."""
    if not guardado:
        return None
    if not guardado.startswith(PREFIXO):
        return guardado                                  # formato antigo, ainda não migrado
    cifrado = base64.b64decode(guardado[len(PREFIXO):])
    return desproteger(cifrado).decode("utf-8")
```

### 6.3. Migração de dados no startup (`tarefas.py`)

Não há mudança de schema, então a regra da skill `migration` não se aplica. A migração decide pelo conteúdo: se o token ainda é um JWT em texto puro (começa com `eyJ`), ele é regravado cifrado. Rodar de novo não faz nada, porque o prefixo `dpapi:v1:` já está lá.

Falha da DPAPI no startup não derruba o sistema. Ela registra no log e tenta de novo na próxima vez.

### 6.4. Backup sem token e cifrado (`_utils.py`, `local.py`)

No snapshot, o token é apagado. O banco real não é tocado:

```sql
-- Roda só no arquivo do snapshot, nunca no banco da loja.
UPDATE configuracoes_licenca SET token = NULL;
```

A chave de ativação é lida como hoje, com `decriptar_valor(licenca.chave_ativacao, hwid)` (`cripto.py`). Dela sai a chave do ZIP. A chave de ativação não é usada direto: ela passa por HKDF, para que a chave do ZIP seja outra coisa, com um rótulo próprio.

```python
# Deriva a chave do ZIP a partir da chave de ativação (ACORDO D-03).
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

def chave_do_backup(chave_ativacao: str) -> bytes:
    """Mesma chave de ativação, em qualquer máquina da licença, gera a mesma chave do ZIP."""
    return HKDF(
        algorithm=hashes.SHA256(),       # função de resumo usada pelo HKDF
        length=32,                       # 32 bytes = AES-256
        salt=None,                       # sem sal: a chave precisa ser igual em todas as máquinas
        info=b"startbig-backup-v2",      # rótulo: separa esta chave de qualquer outra
    ).derive(chave_ativacao.encode("utf-8"))
```

O ZIP é cifrado com AES-GCM (`encriptar_com_chave`) antes do upload. O manifest registra `formato: 2` e `cifrado: true`.

### 6.5. Restauração (`restore.py`)

Antes de abrir o ZIP, a restauração lê o manifest. Se `cifrado: true`, decifra com `chave_do_backup`. Se a chave não confere, responde `BACKUP_CHAVE_INVALIDA` e não mexe no banco. Backups `formato: 1` são abertos como hoje.

A licença local continua sendo preservada pelo `_preserve_local_license`, como já é feito. A restauração não traz licença de outra máquina.

### 6.6. Permissões (`permissoes.py`)

Usa `icacls` para tirar a herança e dar acesso só ao usuário atual:

```python
# permissoes.py — deixa o banco e a configuração visíveis só para este usuário (D-19)
import getpass                      # descobre o nome do usuário logado
import subprocess                   # roda comandos do sistema, como o icacls
import sys

def restringir_ao_usuario(caminho: str) -> None:
    if sys.platform != "win32":
        return                      # fora do Windows não há ACL para ajustar
    usuario = getpass.getuser()
    subprocess.run(
        ["icacls", caminho, "/inheritance:r", "/grant:r", f"{usuario}:F"],  # tira herança e dá controle total ao usuário
        check=True,                 # se o comando falhar, lança erro em vez de ignorar
        capture_output=True,        # guarda a saída para não poluir o terminal
    )
```

## 7. Critérios de aceite

Todos verificados no Windows, com backend na porta 8000 e banco de teste (nunca `start_big.db` da loja):

- **CA-01:** após o startup, `configuracoes_licenca.token` não começa com `eyJ` e começa com `dpapi:v1:`.
- **CA-02:** o ZIP gerado não contém a string do token nem o padrão `eyJ`.
- **CA-03:** um backup `formato: 2` restaura em outra instalação com a mesma chave de ativação.
- **CA-04:** um backup `formato: 1` continua restaurável.
- **CA-05:** rodar a migração duas vezes não muda o banco na segunda vez.
- **CA-06:** com a chave de ativação errada, a restauração responde `BACKUP_CHAVE_INVALIDA` e o banco fica intacto.
- **CA-07:** no Windows, `icacls` do banco mostra só o usuário atual.
- **CA-08:** token copiado para outro usuário do Windows gera `TOKEN_ILEGIVEL`, e o app orienta o re-login.

Os critérios CA-06 e CA-07 precisam de uma máquina Windows real. Fora dela, ficam marcados como "não verificado", com o motivo.

## 8. Casos de teste

| ID | Caso | Esperado |
|----|------|----------|
| CT-01 | `guardar_token` e `ler_token` no mesmo usuário Windows | Mesmo token devolvido |
| CT-02 | `ler_token` com valor antigo, sem prefixo | Devolve o valor como está |
| CT-03 | `ler_token` com valor que não decifra | Lança `TOKEN_ILEGIVEL` |
| CT-04 | Migração com token em texto puro | Vira `dpapi:v1:...` |
| CT-05 | Migração executada duas vezes | Segunda execução não altera o banco |
| CT-06 | `proteger` fora do Windows, em produção | Recusa com `COFRE_INDISPONIVEL` |
| CT-07 | Snapshot do backup | `configuracoes_licenca.token` é `NULL` no snapshot |
| CT-08 | Banco real após criar backup | Token continua cifrado, sem alteração |
| CT-09 | ZIP `formato: 2` | Não contém o token nem o padrão `eyJ` |
| CT-10 | Restauração `formato: 2` com a chave certa | Banco restaurado, licença local preservada |
| CT-11 | Restauração `formato: 2` com chave errada | `BACKUP_CHAVE_INVALIDA`, banco intacto |
| CT-12 | Restauração `formato: 1` | Abre como antes |

## 9. Testes existentes que a mudança afeta

- `test/api/v1/test_backup_preserva_licenca.py`: deve passar sem alteração. Se o snapshot mudar a forma, o teste acusa e a correção é no snapshot, não no teste.
- `test/api/v1/test_licenca_transferencia.py`: lê e escreve o token. Deve passar com `guardar_token` e `ler_token` no lugar do campo direto. Ajustar o teste só para usar o helper, sem mudar o que ele verifica.
- `test/api/v1/test_licenca_validacao_offline.py` e `test_licenca_recusa_vencimento.py`: passam pela leitura do token. Devem passar sem mudança de expectativa.

## 10. Perguntas antes da aprovação

- **Fora do Windows, em produção:** a recomendação é recusar o início do backend. A alternativa é deixar o cifrador de teste funcionar em produção. Não recomendo, porque um dado cifrado de forma fraca daria falsa sensação de proteção.

## 11. Observações

- Mudou o código do backend: depois da entrega, avisar o usuário para rodar `npm run build:sidecar` (AGENT.md §7).
- A migração de dados roda no startup (`tarefas.py`). Não há backup automático antes dela. Por isso o `CT-05` e o `CA-05` são obrigatórios.
- Usuário do Windows trocado ou perfil recriado: o token não decifra. A solução é o re-login, que já é o caminho de recuperação (ADR-001, seção 4).
