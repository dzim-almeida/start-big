# Licença 04 — Rede, token do login e superfície do front

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Frontend (Vue 3 + TypeScript), Backend (FastAPI, CORS e rede da loja), instalador NSIS e configuração do Tauri |
| Dependências | — |
| Bloqueia     | LIC-07 (TLS na rede da loja, spec futura) |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-12, D-17, D-18, D-20, D-21, D-27, D-29; [ADR-002](../../docs/licenca/adr/ADR-002-login-bearer-cofre.md) (Bearer); [ADR-003](../../docs/licenca/adr/ADR-003-token-login-session-storage.md) (sessionStorage); quadro F1, F33, F34, F35, F38 |

> **Revisão 1 (2026-11-18):** revisão de conflitos com o usuário, antes da aprovação.
> - **Conflito 5 (D-27):** um único arquivo, `shared/services/tokenSessao.service.ts`, é dono do token do login. A spec antiga listava 3 pontos; o front tem 7 (`useUser.ts:9`, `auth.store.ts:24`, `axios.ts:62` e `App.vue:27` estavam fora). O truque do `App.vue` vira a limpeza do token antigo.
> - **Conflito 6 (D-20 revista):** lista exata de permissões do Tauri. Entra `fs:allow-write-file` (o `arquivo.ts` grava pelo plugin-fs) e sai também o `shell:default`, que o front não usa.
> - **Conflito 11 (D-29):** o bloqueio de rede responde no formato do projeto, `error` + `detail: {codigo, mensagem}`.
> - **Conflito 12 (D-21 revista):** existem três regras de firewall abrindo a API (a do instalador, a `StartBig-Server` do `system.py` e a do mDNS). As três são apagadas e recriadas com a mesma lista de redes do middleware. Entra o `169.254.0.0/16` e sai o `LocalSubnet`. Um teste compara as duas listas.
> - **Documentação:** origens do CORS numa lista fixa em `core/config.py`, sem variável de ambiente. Entra o `LicencaComputador.vue`, que tem `<strong>` na descrição. O `ProductsView` e o `ModelosEtiquetaModal` não têm HTML e não mudam. Esta spec não depende da SPEC-01, e o motivo antigo de "bloquear a SPEC-03" era da época da ADR-002.

## 1. Objetivo

Fechar a superfície do app: quem pode falar com a API local, onde o login do ERP fica guardado, se um texto digitado pode virar código na tela e o que o Tauri deixa o front fazer.

## 2. Escopo

**Dentro do escopo**
- Lista fechada de origens no CORS (D-18, F1).
- Token do login do ERP guardado só em `sessionStorage`, por um único arquivo (D-12, D-27, F33). Ele some quando a janela fecha, e o sistema pede login a cada abertura. Vale igual para servidor e terminal (ADR-003).
- Remoção do `v-html` do modal de confirmação (D-17, F35).
- Permissões do Tauri restritas ao que o código usa (D-20, F38).
- Rede da loja: a API local só aceita conexões das redes privadas, por firewall e por verificação no próprio app, com a mesma lista nas duas camadas (D-21, F34).

**Fora do escopo**
- Cookie HTTP-only. Decisão rejeitada na ADR-002.
- TLS na rede da loja (F34, opção C). Vai para a LIC-07, depois desta.
- Cofre DPAPI para o token do login. Não se aplica: o token não é guardado em disco (ADR-003).

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/core/config.py` | alterar | Constante `ORIGENS_PERMITIDAS`, lista fixa (sem variável de ambiente). |
| `backend-fastapi/app/main.py` | alterar | `allow_origins=ORIGENS_PERMITIDAS` no lugar de `["*"]` (linha ~52). Registra o middleware de rede da loja. |
| `backend-fastapi/app/core/rede_local.py` | criar | `REDES_DA_LOJA` (lista única) e o middleware que recusa, com 403, quem está fora dela. |
| `backend-fastapi/app/core/system.py` | alterar | `firewall_cfg` cria `StartBig-Server` e `StartBig-mDNS` com `remoteip` vindo de `REDES_DA_LOJA` (já apaga antes de criar). |
| `frontend/src-tauri/nsis/extend/hooks.nsh` | alterar | Apaga e recria as três regras com `remoteip` restrito (§6.5). |
| `frontend/src/shared/services/tokenSessao.service.ts` | criar | `guardarToken`, `lerToken`, `apagarToken` e `limparTokenAntigo`. Único dono do token do login. |
| `frontend/src/api/axios.ts` | alterar | Linhas 26 e 62 usam `lerToken()`. A constante `TOKEN_KEY` sai daqui. |
| `frontend/src/modules/auth/services/auth.service.ts` | alterar | Linhas 32 e 44 usam `guardarToken` e `apagarToken`. |
| `frontend/src/modules/sign-in/services/sign-in.service.ts` | alterar | Linha 16 usa `guardarToken`. |
| `frontend/src/shared/stores/auth.store.ts` | alterar | Linha 24 usa `apagarToken`. |
| `frontend/src/shared/composables/useUser.ts` | alterar | Linha 9 usa `lerToken()`. |
| `frontend/src/App.vue` | alterar | O truque das linhas 21-25 sai; no lugar, `limparTokenAntigo()` ao abrir. |
| `frontend/src/modules/sign-in/composables/useSetup.ts` | alterar | Comentário da linha 32 passa a dizer `sessionStorage`. |
| `frontend/src/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue` | alterar | Remove o `v-html` (linha 87). A descrição vira texto escapado, e o destaque vem por slot. |
| `frontend/src/modules/order-service/views/tabs/ServicosTab.vue` | alterar | Linha ~71: o `<b>` passa para o slot, com o nome interpolado. |
| `frontend/src/modules/configuracoes/components/sections/licenca/components/LicencaComputador.vue` | alterar | Linha ~150: o `<strong>` passa para o slot. |
| `frontend/src-tauri/capabilities/default.json` | alterar | Lista exata da §6.4. |
| `frontend/src-tauri/tauri.conf.json` | conferir | Origem usada pela janela no Windows (§6.1). |
| `backend-fastapi/test/api/v1/test_cors_origens.py` | criar | Casos CT-01 a CT-04. |
| `backend-fastapi/test/core/test_rede_local.py` | criar | Casos CT-12 a CT-16. |
| `frontend/src/shared/services/__tests__/tokenSessao.spec.ts` | criar | Casos CT-05 a CT-08 e CT-17. |
| `frontend/src/shared/components/commons/BaseConfirmModal/__tests__/BaseConfirmModal.spec.ts` | criar | Casos CT-09 a CT-11. |

O `ProductsView.vue:603` e o `ModelosEtiquetaModal.vue:173` usam `description` só com texto e interpolação, sem tag HTML. Sem o `v-html`, o Vue já escapa o texto, então eles não mudam.

Testes existentes que precisam continuar passando: `backend-fastapi/test/api/v1/test_auth_hwid.py` e os testes de login.

## 4. Contrato da API

### 4.1. CORS (sem rota nova)

As origens permitidas passam a ser:

| Origem | Por quê |
|--------|---------|
| `http://localhost:1420` | Desenvolvimento, `npm run dev` |
| `http://tauri.localhost` | Janela do Tauri no Windows (confirmar na verificação, §6.1) |
| `https://tauri.localhost` | Mesma janela, caso o Tauri troque o protocolo |

Nenhuma origem fora da lista recebe `Access-Control-Allow-Origin`.

### 4.2. Rede da loja (D-21, D-29)

Quem chama de fora das redes da loja recebe, em qualquer rota:

```json
{
  "error": "Fora da rede da loja",
  "detail": {
    "codigo": "FORA_DA_REDE_DA_LOJA",
    "mensagem": "Esta API só aceita conexões da rede da loja."
  }
}
```

## 5. Schemas

Nenhum schema novo.

## 6. Especificação técnica

### 6.1. CORS com lista fechada (D-18)

```python
# core/config.py — só estas origens podem ler as respostas da API local (D-18).
# Lista fixa de propósito: uma variável de ambiente permitiria "abrir" o CORS sem querer.
ORIGENS_PERMITIDAS = [
    "http://localhost:1420",         # desenvolvimento (npm run dev)
    "http://tauri.localhost",        # janela do Tauri no Windows
    "https://tauri.localhost",       # mesma janela, se o protocolo mudar
]
```

```python
# main.py — o CORS usa a lista fechada, nunca "*"
from app.core.config import ORIGENS_PERMITIDAS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,   # lista fechada
    allow_credentials=True,             # o cabeçalho Authorization só vale para essas origens
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

Verificação na skill `verify`: confirmar a origem real da janela Tauri no Windows, com o log do navegador da janela. Se for diferente de `http://tauri.localhost`, a lista muda antes da entrega.

### 6.2. Um único dono do token do login (D-12, D-27, ADR-003)

```typescript
// tokenSessao.service.ts — o ÚNICO lugar que sabe onde o token do login fica (ADR-003, D-27).
// Os outros arquivos chamam estas funções; nunca usam sessionStorage/localStorage direto.
// Este arquivo não importa nada, então não entra em importação circular com o axios.
const CHAVE = 'access_token'                       // nome da chave, igual ao de hoje

export function guardarToken(token: string): void {
  sessionStorage.setItem(CHAVE, token)             // sobrevive a recarregar a página, some ao fechar a janela
}

export function lerToken(): string | null {
  return sessionStorage.getItem(CHAVE)             // null = ninguém logado nesta janela
}

export function apagarToken(): void {
  sessionStorage.removeItem(CHAVE)                 // logout ou sessão expirada
}

export function limparTokenAntigo(): void {
  localStorage.removeItem(CHAVE)                   // apaga o token que versões antigas gravaram no disco
}
```

Os sete pontos da §3 passam a chamar essas funções. O `App.vue` troca o truque do `session_active` (que apagava o token do `localStorage` a cada abertura) por uma chamada a `limparTokenAntigo()`. Ao abrir o app, o front não tem token, então o sistema pede login.

### 6.3. Front sem `v-html` (D-17)

`BaseConfirmModal` hoje mostra `description` com `v-html`. O texto passa a ser escapado, e o destaque vem por slot:

```vue
<!-- BaseConfirmModal.vue — texto escapado; o destaque é feito pelo slot -->
<slot name="description">
  <span>{{ description }}</span>      <!-- texto puro: nada é tratado como HTML -->
</slot>
```

Quem precisa de negrito usa o slot, com interpolação:

```vue
<!-- ServicosTab.vue — o nome do serviço é escapado pelo Vue -->
<template #description>
  Deseja realmente {{ servicoToToggle?.ativo ? 'desativar' : 'ativar' }} o serviço
  <b>{{ servicoToToggle?.descricao }}</b>?
</template>
```

O `LicencaComputador.vue` faz o mesmo com o seu `<strong>`.

### 6.4. Permissões do Tauri (D-20)

Cada permissão da lista tem um uso conferido no código:

```json
{
  "permissions": [
    "core:default",
    "opener:default",
    "opener:allow-open-path",
    "dialog:allow-save",
    "fs:allow-write-file"
  ]
}
```

| Permissão | Quem usa |
|-----------|----------|
| `core:default` | Base do Tauri (inclui `path`, usado pelo `downloadDir` em `arquivo.ts:37`) |
| `opener:default` | `openUrl` em vários módulos (licença, suporte, compras, fiscal) |
| `opener:allow-open-path` | `openPath` em `arquivo.ts:80` |
| `dialog:allow-save` | Janela "Salvar como" em `arquivo.ts:45` |
| `fs:allow-write-file` | `writeFile` em `arquivo.ts:70-71`. Só grava no caminho escolhido no "Salvar como", porque o plugin de diálogo libera aquele caminho no escopo do `fs` |

Saem em relação a hoje: `fs:allow-app-read`, `fs:allow-app-write`, `fs:allow-exists`, `shell:default` e `shell:allow-execute`. Quem inicia o backend é o Rust (`backend.rs`), que não passa por esta lista.

### 6.5. Rede da loja: duas camadas com a mesma lista (D-21, F34)

**Lista única** (em `rede_local.py`, e repetida no `hooks.nsh`):

| Rede | Por quê |
|------|---------|
| `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` | Redes privadas, as que as lojas usam |
| `169.254.0.0/16` | Endereço que o Windows se dá quando o roteador falha em distribuir IP |
| `127.0.0.0/8` e `::1` | O próprio computador (só no middleware; o firewall não filtra o tráfego local) |

O `LocalSubnet` **não** entra: ele aceitaria uma sub-rede pública que o middleware recusaria, e os caixas parariam com um erro difícil de entender.

**Camada 1: firewall do Windows.** O firewall libera a conexão se **qualquer** regra liberar. Hoje há três regras abertas para qualquer endereço:

| Regra | Quem cria | O que libera |
|-------|-----------|--------------|
| `StartBigERP_API_Server` | Instalador (`hooks.nsh`) | O programa `erp-api.exe` |
| `StartBig-Server` | Backend, ao virar servidor (`system.py:46-65`) | A porta da API |
| `StartBig-mDNS` | Backend (`system.py`) | UDP 5353 (descoberta do servidor) |

As três passam a ter `remoteip` restrito. O instalador **apaga antes de criar**, para a atualização não deixar uma regra antiga aberta ao lado da nova:

```nsis
; hooks.nsh — a API e o mDNS só aceitam conexões das redes da loja (D-21).
; Apaga antes de criar: numa atualização, a regra antiga (aberta) não pode sobrar.
!define REDES_DA_LOJA "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,169.254.0.0/16"

nsExec::Exec 'netsh advfirewall firewall delete rule name="${FIREWALL_RULE_NAME}"'
Pop $0
nsExec::Exec 'netsh advfirewall firewall add rule name="${FIREWALL_RULE_NAME}" dir=in action=allow program="$INSTDIR\erp-api.exe" profile=any remoteip=${REDES_DA_LOJA} description="Recebe conexões só da rede da loja"'
Pop $0
; O mesmo (delete + add com remoteip) para "StartBig-Server" e "StartBig-mDNS",
; para que as lojas já instaladas fiquem protegidas sem reconfigurar o servidor.
```

O `system.py` usa a mesma lista ao recriar `StartBig-Server` e `StartBig-mDNS` (ele já apaga antes de criar).

**Camada 2: middleware no próprio app.**

```python
# rede_local.py — recusa quem está fora da rede da loja (D-21, F34)
import ipaddress                                    # biblioteca para comparar endereços IP
from starlette.responses import JSONResponse        # resposta de erro em JSON

# Lista ÚNICA das redes da loja. O hooks.nsh repete as quatro primeiras, e um teste
# (CT-16) confere que as duas listas não divergem.
REDES_DA_LOJA = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16"]
_LOCAIS = ["127.0.0.0/8", "::1/128"]               # o próprio computador
_REDES = [ipaddress.ip_network(r) for r in REDES_DA_LOJA + _LOCAIS]


def _endereco_permitido(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)             # converte o texto em endereço IP
    except ValueError:
        return False                                # texto que não é IP é recusado
    return any(ip in rede for rede in _REDES if ip.version == rede.version)


class ExigirRedeDaLoja:
    """Middleware: é chamado antes de cada requisição, para barrar quem está fora."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            host = scope["client"][0] if scope.get("client") else ""
            if not _endereco_permitido(host):
                # Mesmo formato dos outros erros do projeto (D-29).
                resposta = JSONResponse(status_code=403, content={
                    "error": "Fora da rede da loja",
                    "detail": {
                        "codigo": "FORA_DA_REDE_DA_LOJA",
                        "mensagem": "Esta API só aceita conexões da rede da loja.",
                    },
                })
                await resposta(scope, receive, send)   # responde o erro e para aqui
                return
        await self.app(scope, receive, send)           # dentro da rede: segue normalmente
```

O middleware é registrado em `main.py` com `app.add_middleware(ExigirRedeDaLoja)`.

**Limites conhecidos:** a regra não protege contra quem já está na rede (isso é a LIC-07). Uma loja com caixas numa faixa fora da lista (por exemplo, uma rede de operadora `100.64.0.0/10`) precisa de ajuste, registrado na loja.

## 7. Critérios de aceite

- **CA-01:** uma chamada à API local vinda de origem fora da lista não recebe `Access-Control-Allow-Origin`.
- **CA-02:** a janela Tauri do Windows consegue chamar a API, com a origem confirmada na verificação.
- **CA-03:** recarregar a página mantém o login. Fechar e abrir o app pede login de novo.
- **CA-04:** nenhum `localStorage` contém `access_token`, nem depois de atualizar de uma versão antiga, e o token não é gravado em disco.
- **CA-05:** `grep` no front não encontra `v-html` no `BaseConfirmModal`.
- **CA-06:** um nome de fornecedor com `<img src=x onerror=...>` aparece como texto, sem executar nada.
- **CA-07:** o app grava arquivo pelo diálogo de salvar, sem erro de permissão.
- **CA-08:** o `erp-api` não pode ser iniciado pelo front (checado por tentativa no console da janela).
- **CA-09:** a tela não consegue gravar arquivo fora do caminho escolhido no "Salvar como".
- **CA-10:** uma requisição vinda de endereço público recebe `403 FORA_DA_REDE_DA_LOJA`.
- **CA-11:** depois de instalar por cima de uma versão antiga, `netsh advfirewall firewall show rule` mostra as três regras uma vez cada, todas com o `remoteip` da lista.
- **CA-12:** um caixa com endereço `169.254.x.x` é aceito nas duas camadas.

CA-02, CA-03, CA-07, CA-08, CA-09 e CA-11 precisam do app instalado no Windows e ficam para a skill `verify`.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `test_cors_origens.py` | `OPTIONS` com `Origin: http://evil.example` | Sem `Access-Control-Allow-Origin` |
| CT-02 | `test_cors_origens.py` | `OPTIONS` com `Origin: http://localhost:1420` | Origem devolvida |
| CT-03 | `test_cors_origens.py` | `Origin` com `*` | Nenhum cabeçalho de origem |
| CT-04 | `test_cors_origens.py` | Origem da janela Tauri | Origem devolvida |
| CT-05 | `tokenSessao.spec.ts` | `guardarToken` e depois `lerToken` | Mesmo token, em `sessionStorage` |
| CT-06 | `tokenSessao.spec.ts` | Recarregar a página (mesma sessão) | Token ainda disponível |
| CT-07 | `tokenSessao.spec.ts` | Janela fechada (sessão nova) | `lerToken` devolve `null` |
| CT-08 | `tokenSessao.spec.ts` | `access_token` antigo no `localStorage` e `limparTokenAntigo()` | Removido |
| CT-09 | `BaseConfirmModal.spec.ts` | Texto contendo `<img onerror>` | Aparece escapado, sem elemento `img` |
| CT-10 | `BaseConfirmModal.spec.ts` | Slot com `<b>` e interpolação | Negrito aplicado ao valor escapado |
| CT-11 | `BaseConfirmModal.spec.ts` | Nenhum `v-html` na árvore do modal | Verdadeiro |
| CT-12 | `test_rede_local.py` | Requisição de `192.168.1.20` | Passa |
| CT-13 | `test_rede_local.py` | Requisição de `8.8.8.8` | `403 FORA_DA_REDE_DA_LOJA`, no formato `error` + `detail` |
| CT-14 | `test_rede_local.py` | `127.0.0.1`, `::1` e texto que não é IP | Locais passam; texto inválido é recusado |
| CT-15 | `test_rede_local.py` | Requisição de `169.254.10.5` | Passa |
| CT-16 | `test_rede_local.py` | Ler o `REDES_DA_LOJA` do `hooks.nsh` | Igual ao `REDES_DA_LOJA` do `rede_local.py` |
| CT-17 | `tokenSessao.spec.ts` | `useUser` com token no `sessionStorage` | A busca do usuário é habilitada |

## 9. Testes existentes que a mudança afeta

- Testes de `BaseConfirmModal` e dos modais: se algum usa `description` com HTML, ajustar para o slot. A expectativa de texto visível não muda.
- Testes de login que leem `localStorage`: passam a usar o `tokenSessao.service`. Nenhuma expectativa de resposta muda.

## 10. Perguntas antes da aprovação

- Nenhuma.
- **Token do login nos terminais.** Resolvida em 2026-11-18: `sessionStorage`, para servidor e terminal (ADR-003).
- **Rede da loja (F34).** Resolvida em 2026-11-18: opção A (D-21), refinada no conflito 12.
- **Sub-decisão confirmada na revisão de conflitos:** redes privadas fixas, e não a sub-rede do servidor (detectar a máscara é frágil, e o DHCP muda o IP). A lista ganhou o `169.254.0.0/16`.

## 11. Observações

- Mudou o backend e o front: avisar o usuário para rodar `npm run build:sidecar` depois da entrega.
- Mudança nas permissões do Tauri e no instalador exige recompilar o app. Não é só o build do front.
- A proteção do token enquanto a janela está aberta depende da correção do `v-html` (D-17). Por isso as duas mudanças entram juntas.
