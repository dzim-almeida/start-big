# Licença 04 — Rede, token do login e superfície do front

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Frontend (Vue 3 + TypeScript), Backend (FastAPI, só CORS e rotas de sessão) e configuração do Tauri |
| Dependências | SPEC-01 (cofre DPAPI, usado pelo servidor) |
| Bloqueia     | — |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-12, D-17, D-18, D-20; [ADR-002](../../docs/licenca/adr/ADR-002-login-bearer-cofre.md); quadro F1, F33, F35, F38, F34 |

## 1. Objetivo

Fechar a superfície do app: quem pode falar com a API local, como o login do ERP é guardado, se um texto digitado pode virar código na tela e o que o Tauri deixa o front fazer.

## 2. Escopo

**Dentro do escopo**
- Lista fechada de origens no CORS (D-18, F1).
- Token do login guardado no cofre local e não mais no `localStorage` (D-12, F33), para o computador que roda o servidor.
- Remoção do `v-html` dos modais de confirmação (D-17, F35).
- Permissões do Tauri restritas: o sidecar não é mais liberado para o front, e o escopo de arquivos fica no mínimo necessário (D-20, F38).

**Fora do escopo**
- Armazenamento do token nos terminais. Não há backend local nos terminais, então o cofre DPAPI não se aplica. A pergunta está na seção 10.
- TLS na rede da loja (F34). A pergunta está na seção 10.
- Cookie HTTP-only. Decisão rejeitada na ADR-002.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/main.py` | alterar | `allow_origins` com lista fechada, no lugar de `["*"]` (linha ~50). |
| `backend-fastapi/app/core/config.py` | alterar | Constante `ORIGENS_PERMITIDAS` lida de uma variável de ambiente, com padrão para o app. |
| `backend-fastapi/app/api/v1/endpoints/sessao.py` | criar | Rotas `GET`, `PUT` e `DELETE /api/v1/sessao/token-erp`, só para chamadas de `127.0.0.1` ou `::1`. |
| `backend-fastapi/app/services/licenca/cofre.py` | usar | `proteger` e `desproteger` da SPEC-01 para o token do ERP. |
| `frontend/src/api/axios.ts` | alterar | Lê o token da memória e, se não houver, pede ao backend local. Deixa de usar `localStorage`. |
| `frontend/src/modules/auth/services/auth.service.ts` | alterar | `TOKEN_KEY` sai do `localStorage`. Login guarda o token em memória e no backend local. |
| `frontend/src/modules/sign-in/services/sign-in.service.ts` | alterar | Mesma troca na linha 16. |
| `frontend/src/modules/sign-in/composables/useSetup.ts` | alterar | Comentário da linha 32 corrigido. |
| `frontend/src/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue` | alterar | Remove `v-html`. A descrição vira texto escapado, e o destaque vem por slot. |
| `frontend/src/modules/products/views/ProductsView.vue` | alterar | Chamada do modal passa a usar slot, linha ~603. |
| `frontend/src/modules/order-service/views/tabs/ServicosTab.vue` | alterar | Nome do serviço passa a ser interpolação escapada, linha ~71. |
| `frontend/src/modules/products/labels/components/modelo/ModelosEtiquetaModal.vue` | alterar | Nome do modelo passa a ser interpolação escapada, linha ~173. |
| `frontend/src-tauri/capabilities/default.json` | alterar | Remove `shell:allow-execute` do `erp-api` e restringe o `fs` ao mínimo (seção 6.4). |
| `frontend/src-tauri/tauri.conf.json` | alterar | Confere a origem usada pelo Tauri no Windows (seção 6.1). |
| `backend-fastapi/test/api/v1/test_cors_origens.py` | criar | Casos CT-01 a CT-04. |
| `backend-fastapi/test/api/v1/test_sessao_token_erp.py` | criar | Casos CT-05 a CT-09. |
| `frontend/src/shared/components/commons/BaseConfirmModal/__tests__/BaseConfirmModal.spec.ts` | criar | Casos CT-10 a CT-12. |

## 4. Contrato da API

### 4.1. CORS (sem rota nova)

As origens permitidas passam a ser:

| Origem | Por quê |
|--------|---------|
| `http://localhost:1420` | Desenvolvimento, `npm run dev` |
| `http://tauri.localhost` | Janela do Tauri no Windows (confirmar na verificação, seção 6.1) |
| `https://tauri.localhost` | Mesma janela, caso o Tauri troque o protocolo |

`allow_credentials` continua `True`. Nenhuma origem fora da lista recebe `Access-Control-Allow-Origin`.

### 4.2. `GET`, `PUT` e `DELETE /api/v1/sessao/token-erp` (novas)

Só respondem para chamadas vindas de `127.0.0.1` ou `::1`. Qualquer outra origem recebe `403` com `codigo: SOMENTE_NESTA_MAQUINA`.

| Método | Corpo | Resposta | Erros |
|--------|-------|----------|-------|
| `GET` | — | `200 {"token": "..."}` | `404 SESSAO_INEXISTENTE` quando não há token guardado |
| `PUT` | `{"token": "..."}` | `204` | `422` se o corpo não tiver `token` |
| `DELETE` | — | `204` | — |

O `GET` devolve o token decifrado pela DPAPI. Por isso só a própria máquina pode chamá-lo. O token nunca vai em log.

## 5. Schemas

```python
# schemas/sessao.py — corpo de PUT /sessao/token-erp
from pydantic import BaseModel

class TokenErpPayload(BaseModel):
    token: str                  # JWT do login do ERP; é guardado cifrado pela DPAPI
```

## 6. Especificação técnica

### 6.1. CORS com lista fechada (D-18)

```python
# main.py — só estas origens podem ler as respostas da API local (D-18)
ORIGENS_PERMITIDAS = [
    "http://localhost:1420",         # desenvolvimento
    "http://tauri.localhost",        # janela do Tauri no Windows
    "https://tauri.localhost",       # mesma janela, se o protocolo mudar
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,   # lista fechada, nunca "*" junto com credenciais
    allow_credentials=True,             # cookies e Authorization só vão para essas origens
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

Verificação na skill `verify`: confirmar a origem real da janela Tauri no Windows, com o log do navegador da janela. Se for diferente de `http://tauri.localhost`, a lista muda antes da entrega.

### 6.2. Token do login no servidor (D-12)

O front guarda o token em memória. Quando o app reabre, ele pede o token ao backend local, que o decifra da DPAPI. Nos terminais isso não funciona (seção 10).

```python
# sessao.py — o token do ERP fica cifrado; só a própria máquina pode ler (D-12)
from fastapi import APIRouter, HTTPException, Request
from app.services.licenca.cofre import proteger, desproteger

router = APIRouter()
LOCAIS = {"127.0.0.1", "::1"}          # só chamadas de dentro da máquina

def _so_local(request: Request) -> None:
    if request.client is None or request.client.host not in LOCAIS:
        raise HTTPException(status_code=403, detail={
            "codigo": "SOMENTE_NESTA_MAQUINA",
            "mensagem": "Esta operação só pode ser feita no próprio computador.",
        })

ARQUIVO_TOKEN = "sessao_erp.bin"    # arquivo cifrado, dentro da pasta de dados do app

@router.put("/token-erp", status_code=204)
def guardar_token(payload: TokenErpPayload, request: Request):
    _so_local(request)                                  # recusa quem não está nesta máquina
    cifrado = proteger(payload.token.encode("utf-8"))   # cifra pela DPAPI antes de gravar
    caminho_arquivo().write_bytes(cifrado)              # grava só o conteúdo cifrado

@router.get("/token-erp")
def ler_token(request: Request):
    _so_local(request)
    caminho = caminho_arquivo()
    if not caminho.exists():
        raise HTTPException(status_code=404, detail={"codigo": "SESSAO_INEXISTENTE",
                            "mensagem": "Nenhum login guardado neste computador."})
    texto = desproteger(caminho.read_bytes()).decode("utf-8")  # decifra só para devolver a quem chamou
    return {"token": texto}

@router.delete("/token-erp", status_code=204)
def apagar_token(request: Request):
    _so_local(request)
    caminho = caminho_arquivo()
    if caminho.exists():
        caminho.unlink()                                # apaga o arquivo cifrado no logout
```

`caminho_arquivo()` devolve a pasta de dados do app (a mesma usada pelo banco) mais `ARQUIVO_TOKEN`. O token não fica no banco nesta versão, para não misturar com a coluna da licença (SPEC-01).

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

### 6.4. Permissões do Tauri (D-20)

O front não inicia o sidecar. Quem inicia é o Rust, em `backend.rs`. Por isso a permissão `shell:allow-execute` para o `erp-api` sai do `default.json`. A permissão de arquivos fica limitada a escrita por diálogo: o `arquivo.ts` grava só em caminho que o usuário escolheu no diálogo de salvar, e o plugin já libera esse caminho. A verificação precisa confirmar que nenhum outro uso precisa do escopo amplo.

```json
{
  "permissions": [
    "core:default",
    "opener:default",
    "opener:allow-open-path",
    "dialog:allow-save",
    "shell:default"
  ]
}
```

Se a verificação mostrar que `arquivo.ts` precisa de escrita fora do caminho do diálogo, a permissão volta com um escopo fixo, e a spec registra o motivo.

## 7. Critérios de aceite

- **CA-01:** uma chamada à API local vinda de origem fora da lista não recebe `Access-Control-Allow-Origin`.
- **CA-02:** a janela Tauri do Windows consegue chamar a API, com a origem confirmada na verificação.
- **CA-03:** após reabrir o app no servidor, o login continua sem pedir a senha de novo.
- **CA-04:** nenhum `localStorage` contém mais o `access_token`.
- **CA-05:** `grep` no front não encontra `v-html` nos três modais citados.
- **CA-06:** um nome de fornecedor com `<img src=x onerror=...>` aparece como texto, sem executar nada.
- **CA-07:** o app abre e grava arquivo pelo diálogo de salvar, sem erro de permissão.
- **CA-08:** o `erp-api` não pode ser iniciado pelo front (checado por tentativa no console da janela).

Os critérios CA-02, CA-03, CA-07 e CA-08 precisam do app rodando no Windows. Ficam para a skill `verify`.

## 8. Casos de teste

| ID | Caso | Esperado |
|----|------|----------|
| CT-01 | `OPTIONS` com `Origin: http://evil.example` | Sem `Access-Control-Allow-Origin` |
| CT-02 | `OPTIONS` com `Origin: http://localhost:1420` | Origem devolvida, com credenciais |
| CT-03 | `Origin` com `*` | Nenhum cabeçalho de origem |
| CT-04 | Origem da janela Tauri | Origem devolvida |
| CT-05 | `PUT` e depois `GET` na própria máquina | Mesmo token |
| CT-06 | `GET` de outra origem de rede | `403 SOMENTE_NESTA_MAQUINA` |
| CT-07 | `GET` sem token guardado | `404 SESSAO_INEXISTENTE` |
| CT-08 | `DELETE` e depois `GET` | `404` |
| CT-09 | Token no banco | Não aparece em texto puro (depende da SPEC-01) |
| CT-10 | `BaseConfirmModal` com texto contendo `<img onerror>` | Texto aparece escapado, sem elemento `img` |
| CT-11 | Slot com `<b>` e interpolação | Negrito aplicado ao valor escapado |
| CT-12 | Nenhum `v-html` na árvore do modal | Verdadeiro |

## 9. Testes existentes que a mudança afeta

- Testes de `BaseConfirmModal` e dos três modais: se algum usa `description` com HTML, ajustar para o slot. A expectativa de texto visível não muda.
- `test/api/v1/test_auth_hwid.py` e os testes de login: passam a receber o token pelo cofre. A expectativa de resposta não muda.

## 10. Perguntas antes da aprovação

- **1. Onde guardar o token nos terminais (D-12).** O terminal não roda backend local, então a DPAPI do servidor não protege o token dele.
  - **A.** Usar o cofre do Tauri (keyring ou Stronghold), com o plugin registrado no Rust. Exige aprovar uma dependência nova no Rust. É a opção mais segura para o terminal.
  - **B.** O token do terminal fica só em memória, e o dono entra de novo a cada abertura do app. Mais seguro, mais atrito.
  - **C.** Manter o `localStorage` no terminal, com validade curta e limpeza no logout. Sem mudança, mas o token continua legível pelo navegador.
  - **Recomendação: A.** O terminal é o caso mais comum de uso, e B cria atrito diário no caixa.

- **2. Rede da loja (F34).** O caixa chama o servidor por `http://IP:porta`, sem criptografia, e o token viaja em claro.
  - **A.** Restringir a API local à rede da loja e configurar o firewall. Não exige certificado. Não protege contra quem já está na rede.
  - **B.** Token amarrado a cada terminal, com um segredo que assina cada pedido. Protege sem TLS, com complexidade.
  - **C.** TLS na rede da loja, com certificado próprio. É a solução completa, e exige configuração de cada loja.
  - **Recomendação: A agora, com C no plano de infraestrutura.** Reduz a exposição já, sem exigir uma mudança grande em cada loja. B fica como alternativa se a loja não puder instalar certificado.

## 11. Observações

- Mudou o backend e o front: avisar o usuário para rodar `npm run build:sidecar` depois da entrega.
- Mudança nas permissões do Tauri exige recompilar o app. Não é só o build do front.
