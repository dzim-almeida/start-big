# Regra — Contrato da API (backend ↔ frontend)

**Status:** obrigatória · **Escopo:** `api/v1/endpoints/`, `schemas/`, `core/exceptions.py` e `helpers/` no backend; `services/` e composables no frontend · **Origem:** `core/exceptions.py`, `schemas/comum/paginacao.py`, `api/v1/api.py` e `frontend/src/api/axios.ts` (comportamento atual).

Se esta regra e uma spec divergirem, a spec ativa vence. Nesse caso, pare e pergunte se a regra deve ser atualizada.

---

## 1. URLs

- Prefixo único: `/api/v1`. Cada recurso tem o prefixo registrado em `api/v1/api.py`, **no plural e em minúsculas** (`/clientes`, `/produtos`, `/fornecedores`).
- Nome de rota em PT-BR, `kebab-case` ou `snake_case` seguindo o **arquivo vizinho** (hoje há `/cliente_pf` e `/nfe-entrada`: ao criar rota nova em arquivo existente, siga o estilo dele; em recurso novo, prefira `kebab-case`).
- Identificador na URL: `/{id}` numérico. Ação que não é CRUD vira sub-recurso verbo no fim (`/{id}/cancelar`), nunca `/cancelarVenda`.
- Barra final: o frontend chama exatamente como o backend declara (com ou sem `/`). Divergência vira `307` e perda de cabeçalho; confira no `/docs` (Swagger).
- Endpoint novo entra em `api.py` com `tags=["Nome legível em PT-BR"]`.

---

## 2. Métodos e códigos de sucesso

| Operação | Método | Sucesso |
|----------|--------|---------|
| Listar (paginado) | `GET /recurso/` | `200` |
| Buscar um | `GET /recurso/{id}` | `200` |
| Criar | `POST /recurso/` | `201` com o registro criado |
| Alterar | `PUT` (completo) ou `PATCH` (parcial) `/recurso/{id}` | `200` com o registro atualizado |
| Desativar / inativar | `PATCH /recurso/{id}/...` ou `PUT` com `ativo` | `200` |
| Apagar | `DELETE /recurso/{id}` | `204` sem corpo (ou `200` com o registro, se a tela precisa dele) |
| Ação de negócio | `POST /recurso/{id}/acao` | `200` (ou `201` se cria algo) |

- **Prefira desativar a apagar** quando o registro tem histórico (venda, financeiro, fiscal).
- Todo endpoint declara `status_code` e `response_model`; sem isso a documentação e o frontend ficam no escuro.

---

## 3. Corpo de sucesso

O backend devolve o **objeto direto** (o `response_model`), sem envelope `{ "data": ... }`.

- Campos em `snake_case`, PT-BR (`nome_fantasia`, `data_emissao`).
- Datas em ISO 8601 (`2026-11-17` ou `2026-11-17T14:30:00`). Dinheiro como número decimal com **2 casas** (ou texto decimal), nunca texto formatado (`"R$ 1,00"`).
- Campo opcional ausente vem `null`, não `""`.
- O schema de **saída** (`*Read`) é diferente do de **entrada** (`*Create`/`*Update`). Entrada **não** tem `id`, `empresa_id`, timestamps nem campos calculados.

---

## 4. Listas e paginação

- Listas que podem crescer são **sempre paginadas**: `GET /recurso/?page=1&limit=20&search=...`. Padrão `page=1`; `limit` com máximo definido (use `Query(le=...)`).
- A resposta usa o padrão de `schemas/comum/paginacao.py`:

```json
{
  "items": [ ],
  "total_items": 134,
  "page": 1,
  "limit": 20,
  "total_pages": 7,
  "links": { "next": "recurso/?page=2&limit=20", "prev": null }
}
```

  (O nome da lista pode variar por schema legado — confira o `*PaginationRead` do recurso antes de ler no frontend.)
- Filtro e busca por **query string**, em PT-BR ou no nome que o frontend já usa (`buscar`, `search`, `only_active`). Não invente um nome novo para o mesmo conceito: veja o recurso mais parecido.
- Lista pequena e fixa (ex.: cargos, formas de pagamento) pode devolver array simples, **declarado na spec**.

---

## 5. Erros

### 5.1. Corpo

Todo erro tem o mesmo formato (tratado em `core/exceptions.py`):

```json
{ "error": "Mensagem curta do tipo de erro", "detail": "..." }
```

- `detail` é **texto** para erro de negócio (`400`, `401`, `403`, `404`, `409`).
- `detail` é uma **lista** `[{ "field": "cliente.cpf", "message": "CPF inválido" }]` para `422` (validação do Pydantic).
- `500`: mensagem genérica; o detalhe técnico vai só para o log do servidor. **Nunca** devolva stack trace, SQL ou caminho de arquivo.

### 5.2. Backend

- Erro de negócio: `raise HTTPException(status_code=..., detail="Mensagem em PT-BR para o usuário")` no **service**. `ValueError` também serve: o `_handle_db_transaction` converte em `409`.
- Não capture `Exception` para esconder erro. Deixe subir: o handler global registra e responde `500`.
- Mensagem de erro é lida pelo usuário final: sem jargão técnico, sem expor existência de registro de outra empresa.

### 5.3. Qual status usar

| Situação | Status |
|----------|--------|
| Token ausente, inválido ou expirado | `401` |
| Logado, mas sem permissão, módulo desabilitado ou sem empresa | `403` |
| Registro não existe **ou é de outra empresa** | `404` |
| Regra de negócio violada (estoque insuficiente, venda já cancelada) | `400` ou `409` — `409` para conflito de estado/duplicidade |
| Dado de entrada inválido (formato) | `422` (automático pelo Pydantic) |
| Violação de constraint do banco (duplicado) | `400` (automático pelo handler de `IntegrityError`) |
| Bug do servidor | `500` |

### 5.4. Frontend

- O interceptor de `api/axios.ts` já trata: **sem resposta** (backend fora do ar), **`401`** (limpa a sessão e volta ao login) e **`5xx`** (log). Não repita isso em cada tela.
- O **composable** traduz o erro da requisição em aviso ao usuário (toast) usando o `detail` quando for texto, e mostra cada `message` do `422` no campo `field` correspondente.
- Decida por **status**, não por comparar texto da mensagem (mensagens mudam).

### 5.5. Erros com código (decisão D-29 do módulo `licenca`)

Quando a tela precisa decidir **pelo tipo do erro** (e não só mostrar o texto), o `detail` é um **objeto** com um código estável:

```json
{ "error": "Mensagem curta do tipo de erro", "detail": { "codigo": "LICENCA_DE_OUTRA_CONTA", "mensagem": "Texto em PT-BR para o usuário" } }
```

- No backend: `raise HTTPException(status_code=..., detail={"codigo": "...", "mensagem": "..."})`. O handler de `core/exceptions.py` acrescenta o `error`.
- O `codigo` é em `MAIUSCULAS_COM_SUBLINHADO` e não muda depois de publicado: o front e os caixas em versões antigas dependem dele.
- Um middleware que responde antes do handler monta o mesmo corpo à mão (exemplo: `FORA_DA_REDE_DA_LOJA`, LIC-04).
- No front, o código é lido por **uma** função do módulo (exemplo: `lerErroDaLicenca`), que também aceita o código no topo do corpo, para conversar com servidores em versão antiga.
- Erro de negócio sem decisão por código continua com `detail` em texto (§5.1).

---

## 6. Consumo no frontend (`*.service.ts`)

- Um service = um endpoint. Usa a instância `api` de `@/api/axios` (já anexa o token e a URL base).
- A URL base do recurso fica em `constants/` do módulo (`BASE_CUSTOMER_URL`), não repetida em string solta.
- Valide a resposta com o schema Zod. Se a validação falhar, **registre o aviso** (`console.warn`) e devolva o dado mesmo assim, como o projeto faz hoje, **a menos que a spec peça para bloquear**.
- Parâmetros de consulta: monte o objeto só com o que tem valor (não envie `undefined` nem `""`).
- O service não mostra toast nem navega.

```ts
// Exemplo comentado (padrão do projeto)
export async function getCliente(id: number): Promise<ClienteRead> {
  // GET /clientes/{id}: o interceptor já coloca o token no cabeçalho
  const { data } = await api.get(`${BASE_CLIENTE_URL}/${id}`);
  // safeParse não lança erro: devolve { success, data/error } para eu decidir o que fazer
  const resultado = ClienteReadSchema.safeParse(data);
  if (!resultado.success) {
    // Contrato divergente: aviso no console para o time perceber, mas a tela continua
    console.warn('[getCliente] resposta fora do contrato:', resultado.error.issues);
    return data as ClienteRead;
  }
  return resultado.data; // dado validado e tipado
}
```

---

## 7. Mudança de contrato

Mudar rota, método, status, nome de campo, formato de erro ou paginação **já em uso** é **divergência** (`AGENT.md` §7) e segue este roteiro:

1. Pare e pergunte ao usuário.
2. Prefira **acrescentar** (campo opcional novo, rota nova) a **alterar ou remover**. Campo removido quebra a tela e o sidecar de clientes já instalados.
3. Se for inevitável alterar: backend e frontend na **mesma** spec, e o schema Zod do frontend junto.
4. Lembre que o instalador leva o backend junto: cliente que atualiza só um dos lados quebra. Compatibilidade para trás é o padrão.
5. Registre no `CHANGELOG.md` do módulo, seção "Alterado".

---

## 8. Checklist rápido ao criar ou alterar um endpoint

- [ ] Prefixo no `api.py`, `tags` em PT-BR e `check_permission` na rota
- [ ] `status_code` e `response_model` declarados
- [ ] Schema de entrada sem `id`/`empresa_id`; schema de saída sem dado sensível (senha, hash, token)
- [ ] `empresa_id` vem do token e filtra toda consulta; outra empresa → `404`
- [ ] Lista paginada, com busca/filtros na query string
- [ ] Erros de negócio com `HTTPException` e mensagem clara em PT-BR
- [ ] Teste de sucesso, de erro de negócio, de permissão e de isolamento por empresa
- [ ] Frontend: service com schema Zod, composable tratando o erro por status
- [ ] Avisar o usuário que o sidecar precisa ser regerado (`npm run build:sidecar`)

---

## 9. Decisões pendentes

Lista viva: contradições do código atual que ainda não viraram decisão. Ao resolver uma, mova para a seção certa e apague daqui.

- Estilo de URL misto (`snake_case` e `kebab-case`) e barra final inconsistente entre recursos.
- Nome do campo da lista paginada e dos parâmetros de busca (`buscar` × `search`) varia por recurso.
