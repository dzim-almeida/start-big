# Licença 01 — Cofre local (token e chave de ativação) e backup cifrado na nuvem

| Campo        | Valor |
|--------------|-------|
| Status       | Concluída (2026-11-19) |
| Camada       | Backend (FastAPI), com verificação no Windows |
| Dependências | — |
| Bloqueia     | SPEC-02, SPEC-03 |
| Referência   | [acordo](../../../docs/licenca/ACORDO.md) decisões D-02, D-03, D-19, D-25, D-26, D-30; [ADR-001](../../../docs/licenca/adr/ADR-001-cofre-local-dpapi.md); quadro F30, F31, F36, F37 |

> **Revisão 1 (2026-11-18):** revisão de conflitos com o usuário, antes da aprovação.
> - **Conflito 1 (D-25):** a DPAPI usa o escopo **de máquina**. O backend roda como SYSTEM (tarefa `StartBigServer`) e como o usuário logado (sidecar de reserva), sobre o mesmo banco, e o escopo de usuário deixaria uma conta sem ler o que a outra gravou.
> - **Conflito 2 (D-19 revista):** sem `icacls`. O backend só **verifica** as permissões da pasta de dados e avisa.
> - **Conflito 3 (D-03 revista):** os backups locais não mudam. A cifra fica só na **cópia enviada à nuvem**, com uma marca no cabeçalho. O manifest fica dentro do ZIP e é lido pelo incremental, pela limpeza, pela verificação e pela restauração em cadeia, então cifrar o ZIP local quebraria o motor de backup.
> - **Conflito 4 (D-26):** o cifrador falso existe só em `test/`. O sistema sempre sobe, e a falha do cofre aparece na operação que precisou dele (tabela da §6.4). A pergunta da §10 está fechada.
> - **Conflito 17 (D-30):** a **chave de ativação** vai para o mesmo cofre. Hoje ela é cifrada com o HWID, que fica em texto puro na mesma tabela, então quem copia o banco abre a chave.

> **Revisão 2 (2026-11-19, implementação):** divergências achadas ao implementar, decididas com o usuário ou registradas aqui.
> - **Chave que não abre → `LICENCA_DE_OUTRA_MAQUINA` (decisão do usuário).** O código `CHAVE_ATIVACAO_ILEGIVEL` (§4, §6.4) **não é emitido**. O app atual leva `LICENCA_DE_OUTRA_MAQUINA` sozinho à tela de transferência (boot e login), e nenhuma spec ensinava isso ao código novo: a troca de servidor cairia numa tela sem saída. O significado é o mesmo, e o CA-08 continua valendo (a tela orienta entrar com a conta). Vale para a chave nos dois formatos (cofre e HWID).
> - **Fiscal lê o token (decisão do usuário).** `get_licenca_token` (`app/db/crud/fiscal/nucleo.py`), usado em ~30 pontos da emissão fiscal, lia a coluna `token` crua. Passou a abrir o token por `segredos_licenca.ler_token` (vazio se não abrir). Exceção documentada à regra de camadas (crud chamando service), para não trocar os 30 pontos.
> - **Snapshot com `token = ''`, não `NULL`.** A coluna `token` é `NOT NULL` no banco; o `UPDATE ... SET token = NULL` da §6.6 faria o backup inteiro falhar. O texto vazio tem o mesmo efeito (o snapshot sai sem token). CT-12 confere `''`.
> - **Assinaturas:** `ler_chave_ativacao(guardado, hwid)` e `migrar_segredos(db, hwid)` recebem o HWID de quem chama (todas as portas já o têm, e é assim que os testes simulam "outro computador" no formato antigo). `migrar_segredos` só faz `flush`; o commit é do startup (`tarefas.py`), pela regra das camadas.
> - **Ajudantes no `segredos_licenca.py`:** `gravar_token_na_licenca` (o token novo; se o cofre falhar, fica o anterior), `abrir_chave_ou_erro` e `abrir_token_ou_erro` (os erros da §6.4 num lugar só) e `erro_cofre_indisponivel`.
> - **Envio sem chave:** se a chave não abre (cofre fora do ar ou banco copiado), o ciclo de envio para antes de pedir a URL, com o código no `SyncResponse`. O backup nunca sai em claro.
> - **Fora da lista:** `app/db/crud/fiscal/nucleo.py` (aprovado); `test/apoio/__init__.py`, `test/services/licenca/__init__.py`, `test/services/backup/__init__.py` (pacotes de teste); `test/api/v1/test_licenca_recusa_vencimento.py` (a fixture trocava `decriptar_valor` do `terminal`; agora troca `abrir_chave_ou_erro`, sem mudar o que o teste verifica).
> - **Verificação:** CA-01, CA-02, CA-08 e CA-09 exigem Windows real (DPAPI e `Get-Acl`) e ficaram **não verificados** nesta sessão (Linux). Os outros CAs e os CT-01 a CT-17 têm teste automatizado.

## 1. Objetivo

Tirar os segredos da licença do estado "à vista" e proteger o backup que sai do computador:

- O **token da licença** e a **chave de ativação** passam a ser guardados pelo cofre do Windows (DPAPI), no escopo da máquina. Só este computador consegue abri-los.
- O **backup enviado à nuvem** passa a ser cifrado com uma chave derivada da chave de ativação, para que a restauração funcione em outro computador da mesma licença.

Por que isso importa: hoje quem copia o banco leva o token e consegue abrir a chave de ativação. Com a chave e o HWID (os dois no banco), dá para pedir à StartBig um token novo em nome do servidor da loja e baixar os backups da nuvem (conflito 17). O backup na nuvem leva o banco inteiro em claro.

## 2. Escopo

**Dentro do escopo**
- Cofre pela DPAPI no escopo de máquina, chamado pelo Python com `ctypes`, sem dependência nova (ADR-001, D-25).
- Um único módulo lê e grava o token e a chave de ativação (`segredos_licenca.py`).
- Migração de dados no startup: token em texto puro e chave cifrada pelo HWID passam para o cofre. A migração é idempotente.
- Snapshot do backup sem o token.
- Cópia enviada à nuvem cifrada com chave derivada da chave de ativação (D-03), com a marca `SBKC1` no começo do arquivo.
- Download que entende a cópia cifrada e o ZIP antigo.
- Verificação das permissões da pasta de dados, com aviso no log (D-19 revista).
- Cifrador falso só na pasta de testes (D-26).

**Fora do escopo**
- Cifrar os backups locais. Eles ficam na mesma pasta do banco, que continua sem cifra (conflito 3).
- Alterar permissões de arquivo (`icacls`). Ver conflito 2.
- Mostrar o aviso de pasta aberta no painel. Isso fica na LIC-08.
- Criptografia do banco inteiro com SQLCipher (ACORDO, seção 7).
- Restauração liberada ao titular (D-07). Fica na SPEC-03.
- Qualquer tela do front e qualquer mudança de contrato de rota.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/services/licenca/cofre.py` | criar | `proteger(bytes)` e `desproteger(bytes)` pela DPAPI, escopo de máquina, com `LocalFree`. Não tem modo de teste. |
| `backend-fastapi/app/services/licenca/segredos_licenca.py` | criar | `guardar_token`, `ler_token`, `guardar_chave_ativacao`, `ler_chave_ativacao` e `migrar_segredos`. Único ponto que lê e grava esses dois segredos. |
| `backend-fastapi/app/services/licenca/cripto.py` | alterar | Acrescenta `encriptar_com_chave` e `decriptar_com_chave` (AES-256-GCM com chave pronta). As funções por HWID continuam, usadas só para ler o formato antigo e a chave pública. |
| `backend-fastapi/app/services/licenca/cadastro.py` | alterar | Grava token e chave com `guardar_token` e `guardar_chave_ativacao`. |
| `backend-fastapi/app/services/licenca/transferencia.py` | alterar | Idem, em `_gravar_ativacao`. |
| `backend-fastapi/app/services/licenca/validacao.py` | alterar | Grava com `guardar_token`; lê com `ler_token` e `ler_chave_ativacao`. Trata `TOKEN_ILEGIVEL` pela tabela da §6.4. |
| `backend-fastapi/app/services/licenca/sincronizacao.py` | alterar | Idem. |
| `backend-fastapi/app/services/licenca/renovacao.py` | alterar | Idem. |
| `backend-fastapi/app/services/licenca/terminal.py` | alterar | Lê a chave com `ler_chave_ativacao` (conectar e desconectar). |
| `backend-fastapi/app/services/cloud/_http.py` | alterar | `_get_license_token` passa a usar `ler_token`. |
| `backend-fastapi/app/services/cloud/cifra_backup.py` | criar | `chave_do_backup`, `cifrar_para_nuvem` e `decifrar_da_nuvem`, com a marca `SBKC1`. |
| `backend-fastapi/app/services/cloud/sync.py` | alterar | Envia a cópia cifrada. O `tamanhoBytes` passa a ser o tamanho da cópia cifrada. |
| `backend-fastapi/app/services/cloud/download.py` | alterar | Decifra antes do `save_backup` quando o arquivo começa com `SBKC1`. |
| `backend-fastapi/app/services/backup/_utils.py` | alterar | `_create_snapshot_db` zera `configuracoes_licenca.token` no snapshot, sem tocar no banco real. |
| `backend-fastapi/app/core/permissoes.py` | criar | `verificar_pasta_de_dados(caminho)`: lê a lista de acesso e avisa no log. Não altera nada. |
| `backend-fastapi/app/core/tarefas.py` | alterar | No startup, chama `migrar_segredos` e `verificar_pasta_de_dados`. Nenhuma das duas derruba o startup. |
| `backend-fastapi/test/apoio/cofre_falso.py` | criar | Cifrador falso. Fica fora de `app/`, então nunca entra no `.exe`. |
| `backend-fastapi/test/conftest.py` | alterar | Fixture `autouse` que troca o cofre pelo falso em todos os testes. |
| `backend-fastapi/test/services/licenca/test_segredos_licenca.py` | criar | Casos CT-01 a CT-11. |
| `backend-fastapi/test/services/backup/test_backup_nuvem_cifrado.py` | criar | Casos CT-12 a CT-16. |
| `backend-fastapi/test/core/test_permissoes.py` | criar | Caso CT-17. |

Os testes existentes que cobrem o backup e a licença precisam continuar passando sem mudança de expectativa (§9).

## 4. Contrato da API

Nenhuma rota nova nem alterada.

Erros novos, no formato do projeto (D-29: `error` + `detail` com `codigo` e `mensagem`):

| Código | Status | Quando |
|--------|--------|--------|
| `COFRE_INDISPONIVEL` | 503 | A DPAPI recusou uma operação de que a licença precisava (§6.4) |
| `TOKEN_ILEGIVEL` | 403 | O token guardado não abre neste computador, e não foi possível pedir outro (sem internet) |
| `CHAVE_ATIVACAO_ILEGIVEL` | 403 | A chave de ativação não abre neste computador. Típico de banco copiado de outra máquina: a saída é o re-login |
| `BACKUP_CHAVE_INVALIDA` | 422 | O backup baixado da nuvem não abre com a chave desta licença. Nada é salvo |

O aviso de pasta de dados aberta não é erro de API. Ele vai para o log com o código `PASTA_DADOS_ABERTA`, e a LIC-08 o mostra no painel.

## 5. Schemas

Nenhum schema Pydantic novo. Os valores no banco ganham um prefixo que diz o formato:

| Coluna | Formato antigo | Formato novo |
|--------|----------------|--------------|
| `configuracoes_licenca.token` | JWT em texto puro (`eyJ...`) | `dpapi:v1:<base64>` |
| `configuracoes_licenca.chave_ativacao` | cifrada pelo HWID (sem prefixo) | `dpapi:v1:<base64>` |

A cópia enviada à nuvem tem o formato: `SBKC1` (5 bytes) + nonce (12 bytes) + ZIP cifrado com AES-GCM (o *tag* de 16 bytes vai no fim, como a biblioteca `cryptography` entrega).

## 6. Especificação técnica

### 6.1. Cofre pela DPAPI, escopo de máquina (`cofre.py`)

A DPAPI é um cofre do Windows. Com a opção `CRYPTPROTECT_LOCAL_MACHINE`, a chave do cofre é **do computador**: qualquer conta deste computador abre, inclusive SYSTEM e o usuário logado, e nenhum outro computador abre (D-25).

```python
# cofre.py — guarda e lê segredos pela DPAPI do Windows, no escopo da máquina (ADR-001, D-25)
import ctypes                      # biblioteca para chamar funções de DLLs do Windows
import sys                         # para saber em qual sistema operacional estamos
from ctypes import wintypes        # tipos que o Windows usa (inteiros, ponteiros)

# 0x4 = CRYPTPROTECT_LOCAL_MACHINE: a chave é do computador, não do usuário.
# A tarefa StartBigServer (SYSTEM) e o sidecar (usuário logado) abrem o mesmo banco,
# então os dois precisam conseguir ler o que o outro gravou.
CRYPTPROTECT_LOCAL_MACHINE = 0x4


class CofreIndisponivel(Exception):
    """A DPAPI não pôde ser usada (sistema não é Windows, ou o Windows recusou)."""


class SegredoIlegivel(Exception):
    """O valor guardado não abre neste computador (foi gravado em outro)."""


class _DataBlob(ctypes.Structure):
    """Estrutura que a DPAPI usa para passar bytes de entrada e de saída."""
    _fields_ = [("cbData", wintypes.DWORD),                 # quantos bytes existem
                ("pbData", ctypes.POINTER(ctypes.c_byte))]  # endereço dos bytes


def _blob_de(dados: bytes) -> tuple[_DataBlob, ctypes.Array]:
    # Cria o blob e devolve também o buffer, para ele não ser liberado antes da chamada.
    buffer = ctypes.create_string_buffer(dados, len(dados))
    blob = _DataBlob(len(dados), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    return blob, buffer


def _ler_e_liberar(saida: _DataBlob) -> bytes:
    # A DPAPI aloca a memória da saída; copiamos os bytes e devolvemos a memória
    # ao Windows com LocalFree, senão cada chamada vaza um pedaço de memória.
    try:
        return ctypes.string_at(saida.pbData, saida.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(saida.pbData)


def proteger(dados: bytes) -> bytes:
    """Cifra os bytes. Só este computador consegue abrir depois."""
    if sys.platform != "win32":
        raise CofreIndisponivel("A DPAPI só existe no Windows.")
    entrada, _buffer = _blob_de(dados)
    saida = _DataBlob()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(entrada), None, None, None, None,
        CRYPTPROTECT_LOCAL_MACHINE, ctypes.byref(saida))
    if not ok:
        raise CofreIndisponivel("O Windows recusou a cifra.")
    return _ler_e_liberar(saida)


def desproteger(dados: bytes) -> bytes:
    """Abre os bytes. Falha se eles foram cifrados em outro computador."""
    if sys.platform != "win32":
        raise CofreIndisponivel("A DPAPI só existe no Windows.")
    entrada, _buffer = _blob_de(dados)
    saida = _DataBlob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida))
    if not ok:
        raise SegredoIlegivel("Este valor não abre neste computador.")
    return _ler_e_liberar(saida)
```

Não existe "modo de teste" neste arquivo, e ele não lê variável de ambiente. A tarefa `StartBigServer` **não recebe** `APP_ENV` (`app/api/v1/api.py:71-74`), então qualquer regra baseada nessa variável trataria o servidor da loja como desenvolvimento (conflito 4).

### 6.2. Um ponto só para o token e a chave (`segredos_licenca.py`)

```python
# segredos_licenca.py — único lugar que lê e grava o token e a chave de ativação (D-30)
import base64                                           # transforma bytes em texto seguro para o banco
from app.core.hwid import obter_hwid
from app.services.licenca import cofre
from app.services.licenca.cripto import decriptar_valor  # formato antigo da chave (pelo HWID)

PREFIXO = "dpapi:v1:"                                   # marca que o valor já está no cofre


def _guardar(texto: str) -> str:
    cifrado = cofre.proteger(texto.encode("utf-8"))     # tranca no cofre do Windows
    return PREFIXO + base64.b64encode(cifrado).decode()


def _abrir(guardado: str) -> str:
    cifrado = base64.b64decode(guardado[len(PREFIXO):])
    return cofre.desproteger(cifrado).decode("utf-8")


def guardar_token(token: str) -> str:
    """Devolve o texto que deve ir para a coluna `token`."""
    return _guardar(token)


def ler_token(guardado: str | None) -> str | None:
    """Abre o token. Token antigo, em texto puro, é devolvido como está até a migração."""
    if not guardado:
        return None
    if not guardado.startswith(PREFIXO):
        return guardado                                 # formato antigo, ainda não migrado
    return _abrir(guardado)                             # pode lançar cofre.SegredoIlegivel


def guardar_chave_ativacao(chave: str) -> str:
    """Devolve o texto que deve ir para a coluna `chave_ativacao`."""
    return _guardar(chave)


def ler_chave_ativacao(guardado: str) -> str:
    """Abre a chave. A chave antiga, cifrada pelo HWID, ainda é lida pelo caminho antigo."""
    if not guardado.startswith(PREFIXO):
        return decriptar_valor(guardado, obter_hwid())  # formato antigo, ainda não migrado
    return _abrir(guardado)
```

A chave pública **não** vai para o cofre: ela é pública por definição, e o código atual (cifrada pelo HWID) continua.

### 6.3. Migração de dados no startup (`migrar_segredos`, chamada em `tarefas.py`)

Não há mudança de schema, então a regra da skill `migration` não se aplica. A migração decide pelo **conteúdo** de cada coluna:

- token sem o prefixo `dpapi:v1:` e começando com `eyJ` (JWT) → regrava com `guardar_token`;
- chave de ativação sem o prefixo → abre com `decriptar_valor(valor, obter_hwid())` e regrava com `guardar_chave_ativacao`.

Rodar de novo não faz nada, porque o prefixo já está lá. Se o cofre falhar, a migração registra no log, **não altera nada** e tenta de novo no próximo boot. Os valores antigos continuam legíveis pelo caminho antigo de `ler_token` e `ler_chave_ativacao`.

### 6.4. Quando o cofre falha: o sistema sempre sobe (D-26)

| Situação | O que o sistema faz | O que a pessoa vê |
|---|---|---|
| A migração do startup não consegue trancar | Mantém o valor antigo, registra no log e tenta no próximo boot | Nada |
| A validação online deu certo, mas o token novo não pôde ser trancado | Mantém o token anterior (ainda vale até 7 dias), registra no log e tenta na próxima validação. A resposta da validação continua sendo "licença válida" | Nada |
| O token não abre, **com internet** | Pede um token novo à StartBig com a chave de ativação e regrava | Nada, no máximo alguns segundos a mais |
| O token não abre, **sem internet** | `TOKEN_ILEGIVEL` | Tela de erro de licença: conectar à internet ou entrar de novo com a conta |
| A chave de ativação não abre (banco copiado de outra máquina) | `CHAVE_ATIVACAO_ILEGIVEL` | Tela de erro de licença, orientando o re-login |
| Desenvolvimento fora do Windows | `COFRE_INDISPONIVEL` nas operações de licença; o resto do sistema sobe | Erro de licença, com a causa no log |

Com o escopo de máquina, o token e a chave só deixam de abrir quando o banco foi copiado para outro computador (o caso que esta spec **quer** bloquear) ou quando o Windows foi reinstalado (que já conta como computador novo pela D-08).

### 6.5. Cofre falso só nos testes (`test/apoio/cofre_falso.py`, `test/conftest.py`)

```python
# test/conftest.py — antes de cada teste, troca a DPAPI por um cifrador falso.
# O cofre falso mora em test/: o PyInstaller nunca o coloca no .exe da loja.
import pytest
from app.services.licenca import cofre
from test.apoio import cofre_falso


@pytest.fixture(autouse=True)          # autouse=True: vale para todos os testes, sem precisar pedir
def usar_cofre_falso(monkeypatch):     # monkeypatch: troca uma função só durante o teste
    monkeypatch.setattr(cofre, "proteger", cofre_falso.proteger)
    monkeypatch.setattr(cofre, "desproteger", cofre_falso.desproteger)
```

O cofre falso pode simular a falha (`cofre_falso.falhar_proxima = True`) para os casos da §6.4.

### 6.6. Backup: snapshot sem token (`_utils.py`)

No snapshot, o token é apagado. O banco real não é tocado:

```sql
-- Roda só no arquivo do snapshot, nunca no banco da loja.
UPDATE configuracoes_licenca SET token = NULL;
```

A chave de ativação continua no snapshot, mas agora trancada no cofre (§6.3): em outro computador ela não abre.

### 6.7. Cópia cifrada para a nuvem (`cifra_backup.py`, `sync.py`, `download.py`)

Os backups locais **não mudam**: o incremental, a limpeza, a verificação e a restauração em cadeia continuam lendo o manifest de dentro do ZIP, como hoje. A cifra acontece só na cópia que sai do computador.

```python
# cifra_backup.py — cifra a cópia do backup que vai para a nuvem (D-03, conflito 3)
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MARCA_CIFRADO = b"SBKC1"           # "StartBig Backup Cifrado", versão 1. Um ZIP comum começa com b"PK\x03\x04".


def chave_do_backup(chave_ativacao: str) -> bytes:
    """A mesma chave de ativação, em qualquer máquina da licença, gera a mesma chave do backup."""
    return HKDF(
        algorithm=hashes.SHA256(),       # função de resumo usada pelo HKDF
        length=32,                       # 32 bytes = AES-256
        salt=None,                       # sem sal: a chave precisa ser igual em todas as máquinas
        info=b"startbig-backup-v2",      # rótulo: separa esta chave de qualquer outra
    ).derive(chave_ativacao.encode("utf-8"))


def esta_cifrado(primeiros_bytes: bytes) -> bool:
    # Olha só o começo do arquivo, sem precisar abrir o ZIP nem o manifest.
    return primeiros_bytes.startswith(MARCA_CIFRADO)


def cifrar_para_nuvem(zip_bytes: bytes, chave_ativacao: str) -> bytes:
    nonce = os.urandom(12)                                   # número único por cifra (exigência do AES-GCM)
    cifrado = AESGCM(chave_do_backup(chave_ativacao)).encrypt(nonce, zip_bytes, MARCA_CIFRADO)
    return MARCA_CIFRADO + nonce + cifrado                   # marca + nonce + dados cifrados


def decifrar_da_nuvem(conteudo: bytes, chave_ativacao: str) -> bytes:
    nonce = conteudo[len(MARCA_CIFRADO):len(MARCA_CIFRADO) + 12]
    cifrado = conteudo[len(MARCA_CIFRADO) + 12:]
    # Se a chave não confere, o AES-GCM lança InvalidTag: vira BACKUP_CHAVE_INVALIDA.
    return AESGCM(chave_do_backup(chave_ativacao)).decrypt(nonce, cifrado, MARCA_CIFRADO)
```

No `sync.py`, a cópia cifrada é montada **antes** do pedido de URL, porque o `tamanhoBytes` enviado à API (`sync.py:55`) passa a ser o tamanho dela. O `codigoConteudo` continua vindo do manifest, sem mudança.

No `download.py`, antes do `save_backup`: se o arquivo começa com `SBKC1`, decifra com a chave desta licença (`ler_chave_ativacao`); se não abrir, responde `BACKUP_CHAVE_INVALIDA` e não salva nada. Se começa com `PK`, é um backup antigo e segue como hoje.

**Cuidado registrado:** os backups enviados antes desta spec continuam em claro na nuvem até expirarem. A deduplicação ("PULAR: conteúdo já na nuvem") pode manter uma cópia antiga em claro de um conteúdo que não mudou.

### 6.8. Verificação da pasta de dados (`permissoes.py`, D-19 revista)

A pasta padrão (`%LOCALAPPDATA%\StartBigERP\data`) fica no perfil do usuário, que o Windows já restringe ao próprio usuário, a SYSTEM e aos administradores. O backend só **confere** e **avisa**:

- lê a lista de acesso pelo PowerShell (`Get-Acl`), com cada conta traduzida para o SID, que não depende do idioma do Windows;
- se encontrar acesso para "Todos" (`S-1-1-0`), "Usuários" (`S-1-5-32-545`) ou "Usuários autenticados" (`S-1-5-11`), ou se a pasta estiver fora do perfil, registra `PASTA_DADOS_ABERTA` no log;
- nunca altera permissões. Fora do Windows, não faz nada. Uma falha na leitura só vai para o log.

## 7. Critérios de aceite

- **CA-01:** depois do startup, `configuracoes_licenca.token` começa com `dpapi:v1:`.
- **CA-02:** depois do startup, `configuracoes_licenca.chave_ativacao` começa com `dpapi:v1:`, e a licença continua validando.
- **CA-03:** o arquivo enviado à nuvem começa com `SBKC1` e não contém o token nem o padrão `eyJ`.
- **CA-04:** um backup cifrado baixado da nuvem restaura em outra instalação da mesma licença.
- **CA-05:** um backup antigo da nuvem (ZIP sem marca) continua restaurável.
- **CA-06:** um backup cifrado que não abre com a chave desta licença responde `BACKUP_CHAVE_INVALIDA`, e nada é salvo.
- **CA-07:** rodar a migração duas vezes não muda o banco na segunda vez.
- **CA-08:** um banco copiado para outro computador não abre o token nem a chave: a tela orienta o re-login.
- **CA-09:** uma pasta de dados liberada para "Todos" gera `PASTA_DADOS_ABERTA` no log, sem alterar permissão nenhuma.
- **CA-10:** os backups locais, o incremental e a limpeza funcionam como antes.

CA-01, CA-02, CA-08 e CA-09 precisam de Windows real (DPAPI e lista de acesso de verdade) e são verificados na skill `verify`. Os outros são cobertos por teste automatizado.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `test_segredos_licenca.py` | `guardar_token` e `ler_token` | Mesmo token devolvido |
| CT-02 | `test_segredos_licenca.py` | `ler_token` com valor antigo, sem prefixo | Devolve o valor como está |
| CT-03 | `test_segredos_licenca.py` | `ler_token` com valor que não abre | `SegredoIlegivel` |
| CT-04 | `test_segredos_licenca.py` | `guardar_chave_ativacao` e `ler_chave_ativacao` | Mesma chave devolvida |
| CT-05 | `test_segredos_licenca.py` | `ler_chave_ativacao` no formato antigo (HWID) | Abre pelo caminho antigo |
| CT-06 | `test_segredos_licenca.py` | Migração com token e chave antigos | Os dois viram `dpapi:v1:...` |
| CT-07 | `test_segredos_licenca.py` | Migração executada duas vezes | A segunda não altera o banco |
| CT-08 | `test_segredos_licenca.py` | Migração com o cofre falhando | Valores antigos intactos, log registrado, sem exceção no startup |
| CT-09 | `test_segredos_licenca.py` | Validação online ok, cofre falha ao gravar o token novo | Licença válida; token anterior mantido; log registrado |
| CT-10 | `test_segredos_licenca.py` | Token não abre, com internet | Token novo pedido com a chave e regravado; licença válida |
| CT-11 | `test_segredos_licenca.py` | Procurar o cofre falso dentro de `app/` | Nenhum arquivo de `app/` importa ou contém o cofre falso |
| CT-12 | `test_backup_nuvem_cifrado.py` | Snapshot do backup | `token` é `NULL` no snapshot; o banco real não muda |
| CT-13 | `test_backup_nuvem_cifrado.py` | Cópia para a nuvem | Começa com `SBKC1`, sem token nem `eyJ`; `tamanhoBytes` é o da cópia cifrada |
| CT-14 | `test_backup_nuvem_cifrado.py` | Download cifrado com a chave certa | Salvo, restaurável, licença local preservada |
| CT-15 | `test_backup_nuvem_cifrado.py` | Download cifrado com outra chave | `BACKUP_CHAVE_INVALIDA`; nada salvo |
| CT-16 | `test_backup_nuvem_cifrado.py` | Download de ZIP antigo (começa com `PK`) | Salvo como antes |
| CT-17 | `test_permissoes.py` | `verificar_pasta_de_dados` fora do Windows | Não faz nada e não lança erro |

## 9. Testes existentes que a mudança afeta

- `test/api/v1/test_backup_preserva_licenca.py`: deve passar sem alteração. Se o snapshot mudar de forma, a correção é no snapshot, não no teste.
- `test/api/v1/test_licenca_transferencia.py`: lê e escreve o token e a chave. Ajustar só para usar os helpers, sem mudar o que ele verifica.
- `test/api/v1/test_licenca_validacao_offline.py` e `test_licenca_recusa_vencimento.py`: passam pela leitura do token. Devem passar sem mudança de expectativa.
- Os testes de backup local (incremental, limpeza, verificação, restauração em cadeia) não mudam.

## 10. Perguntas antes da aprovação

- Nenhuma. A pergunta sobre "fora do Windows, em produção" foi fechada pelo conflito 4 (D-26): o cifrador falso não existe no `.exe`, e o sistema sempre sobe.

## 11. Observações

- Mudou o código do backend: depois da entrega, avisar o usuário para rodar `npm run build:sidecar` (AGENT.md §7).
- A migração de dados roda no startup (`tarefas.py`). Não há backup automático antes dela. Por isso o CT-07, o CT-08 e o CA-07 são obrigatórios.
- O R-02 (F5 aceito, conflito 7) é mitigado por esta spec: sem a chave de ativação legível numa cópia do banco, o ataque do F5 perde a porta de entrada.
