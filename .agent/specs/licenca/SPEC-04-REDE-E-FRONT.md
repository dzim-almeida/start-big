# Licença 04 — Rede, token do login e superfície do front

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Frontend (Vue 3 + TypeScript), Backend (FastAPI, só CORS) e configuração do Tauri |
| Dependências | — |
| Bloqueia     | SPEC-03 (o re-login usa o token guardado pelo front desta spec) |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-12, D-17, D-18, D-20; [ADR-002](../../docs/licenca/adr/ADR-002-login-bearer-cofre.md) (Bearer); [ADR-003](../../docs/licenca/adr/ADR-003-token-login-session-storage.md) (sessionStorage); quadro F1, F33, F35, F38, F34 |

## 1. Objetivo

Fechar a superfície do app: quem pode falar com a API local, onde o login do ERP fica guardado, se um texto digitado pode virar código na tela e o que o Tauri deixa o front fazer.

## 2. Escopo

**Dentro do escopo**
- Lista fechada de origens no CORS (D-18, F1).
- Token do login do ERP guardado só em `sessionStorage` (D-12, F33). Ele some quando a janela fecha, e o sistema pede login a cada abertura. Vale igual para servidor e terminal (ADR-003).
- Remoção do `v-html` dos modais de confirmação (D-17, F35).
- Permissões do Tauri restritas: o sidecar não é mais liberado para o front, e o escopo de arquivos fica no mínimo necessário (D-20, F38).

**Fora do escopo**
- Cookie HTTP-only. Decisão rejeitada na ADR-002.
- TLS na rede da loja (F34). A pergunta está na seção 10.
- Cofre DPAPI para o token do login. Não se aplica: o token não é guardado em disco (ADR-003). O cofre é só para o token da licença (SPEC-01).

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/main.py` | alterar | `allow_origins` com lista fechada, no lugar de `["*"]` (linha ~50). |
| `backend-fastapi/app/core/config.py` | alterar | Constante `ORIGENS_PERMITIDAS` lida de uma variável de ambiente, com padrão para o app. |
| `frontend/src/api/axios.ts` | alterar | Lê o token de `sessionStorage` (linhas 14 e 26-28). Deixa de usar `localStorage`. |
| `frontend/src/modules/auth/services/auth.service.ts` | alterar | `TOKEN_KEY` vai para `sessionStorage` (linhas 32, 44). |
| `frontend/src/modules/sign-in/services/sign-in.service.ts` | alterar | Mesma troca na linha 16. |
| `frontend/src/modules/sign-in/composables/useSetup.ts` | alterar | Comentário da linha 32 atualizado para dizer `sessionStorage`. |
| `frontend/src/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue` | alterar | Remove `v-html`. A descrição vira texto escapado, e o destaque vem por slot. |
| `frontend/src/modules/products/views/ProductsView.vue` | alterar | Chamada do modal passa a usar slot, linha ~603. |
| `frontend/src/modules/order-service/views/tabs/ServicosTab.vue` | alterar | Nome do serviço passa a ser interpolação escapada, linha ~71. |
| `frontend/src/modules/products/labels/components/modelo/ModelosEtiquetaModal.vue` | alterar | Nome do modelo passa a ser interpolação escapada, linha ~173. |
| `frontend/src-tauri/capabilities/default.json` | alterar | Remove `shell:allow-execute` do `erp-api` e restringe o `fs` ao mínimo (seção 6.3). |
| `frontend/src-tauri/tauri.conf.json` | alterar | Confere a origem usada pelo Tauri no Windows (seção 6.1). |
| `backend-fastapi/test/api/v1/test_cors_origens.py` | criar | Casos CT-01 a CT-04. |
| `frontend/src/modules/auth/__tests__/sessao-token.spec.ts` | criar | Casos CT-05 a CT-08. |
| `frontend/src/shared/components/commons/BaseConfirmModal/__tests__/BaseConfirmModal.spec.ts` | criar | Casos CT-09 a CT-11. |

Testes existentes que precisam continuar passando: `backend-fastapi/test/api/v1/test_auth_hwid.py` e os testes de login. A expectativa de resposta não muda, só o lugar onde o front guarda o token.

## 4. Contrato da API

### 4.1. CORS (sem rota nova)

As origens permitidas passam a ser:

| Origem | Por quê |
|--------|---------|
| `http://localhost:1420` | Desenvolvimento, `npm run dev` |
| `http://tauri.localhost` | Janela do Tauri no Windows (confirmar na verificação, seção 6.1) |
| `https://tauri.localhost` | Mesma janela, caso o Tauri troque o protocolo |

`allow_credentials` continua `True`. Nenhuma origem fora da lista recebe `Access-Control-Allow-Origin`.

Não há rota nova. Nesta versão, o token do login não é guardado no backend (ADR-003).

## 5. Schemas

Nenhum schema novo.

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

### 6.2. Token do login só na sessão da janela (D-12, ADR-003)

O front guarda o token em `sessionStorage`. A chave é a mesma de hoje (`access_token`), só muda o lugar onde ela fica.

```typescript
// auth.service.ts — o token do login fica só na sessão da janela (ADR-003)
const TOKEN_KEY = 'access_token'            // nome da chave, igual ao de hoje

export function guardarToken(token: string): void {
  // sessionStorage: sobrevive a recarregar a página, some ao fechar a janela.
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function lerToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)  // null quando a janela foi fechada
}

export function apagarToken(): void {
  sessionStorage.removeItem(TOKEN_KEY)      // chamado no logout
}
```

No `axios.ts`, o interceptor passa a chamar `lerToken()` em vez de `localStorage.getItem`. Nenhum outro código lê o token do armazenamento.

Ao abrir o app, o front não tem token, então o sistema pede login. Esse é o comportamento que o dono escolheu.

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
- **CA-03:** recarregar a página mantém o login. Fechar e abrir o app pede login de novo.
- **CA-04:** nenhum `localStorage` contém mais o `access_token`, e o token não é gravado em disco.
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
| CT-05 | `guardarToken` e depois `lerToken` | Mesmo token, em `sessionStorage` |
| CT-06 | Recarregar a página (novo carregamento, mesma sessão) | Token ainda disponível |
| CT-07 | Janela fechada (sessão nova) | `lerToken` devolve `null` |
| CT-08 | Após o login, o `localStorage` não tem `access_token` | Verdadeiro |
| CT-09 | `BaseConfirmModal` com texto contendo `<img onerror>` | Texto aparece escapado, sem elemento `img` |
| CT-10 | Slot com `<b>` e interpolação | Negrito aplicado ao valor escapado |
| CT-11 | Nenhum `v-html` na árvore do modal | Verdadeiro |

## 9. Testes existentes que a mudança afeta

- Testes de `BaseConfirmModal` e dos três modais: se algum usa `description` com HTML, ajustar para o slot. A expectativa de texto visível não muda.
- Testes de login que leem `localStorage`: passam a ler `sessionStorage`. Nenhuma expectativa de resposta muda.

## 10. Perguntas antes da aprovação

- **1. Onde guardar o token do login nos terminais.** **Resolvida em 2026-11-18:** `sessionStorage`, para servidor e terminal, sem persistência entre aberturas (ADR-003). Não há mais pergunta sobre isso.

- **2. Rede da loja (F34).** O caixa chama o servidor por `http://IP:porta`, sem criptografia, e o token do login viaja em claro na rede.
  - **A.** Restringir a API local à rede da loja e configurar o firewall. Não exige certificado. Não protege contra quem já está na rede.
  - **B.** Token amarrado a cada terminal, com um segredo que assina cada pedido. Protege sem TLS, com complexidade.
  - **C.** TLS na rede da loja, com certificado próprio. É a solução completa, e exige configuração de cada loja.
  - **Recomendação: A agora, com C no plano de infraestrutura.** Reduz a exposição já, sem exigir uma mudança grande em cada loja. B fica como alternativa se a loja não puder instalar certificado.

## 11. Observações

- Mudou o backend e o front: avisar o usuário para rodar `npm run build:sidecar` depois da entrega.
- Mudança nas permissões do Tauri exige recompilar o app. Não é só o build do front.
- A proteção do token enquanto a janela está aberta depende da correção do `v-html` (D-17). Por isso as duas mudanças entram juntas.
