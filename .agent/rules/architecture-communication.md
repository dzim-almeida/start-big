# Regras Rígidas de Comunicação — Arquitetura Backend/Frontend

## 1. Padrão de Resposta da API

### 1.1 Sucesso (2xx)
```json
{
  "data": <T>,
  "status": "success"
}
```

**Obrigatório:**
- Campo `data` sempre presente, mesmo que `null`
- Status HTTP 200 para operações bem-sucedidas
- Nunca embrulhar em array raiz (quando lista: `data: [...]`)

### 1.2 Erro (4xx/5xx)
```json
{
  "status": "error",
  "message": "descrição legível do erro",
  "error_code": "CODIGO_DO_ERRO",
  "details": <object>
}
```

**Obrigatório:**
- `status: "error"` em 4xx/5xx
- `message`: mensagem amigável (será exibida ao usuário)
- `error_code`: UPPER_SNAKE_CASE para tratamento programático
- Nunca lance stacktrace ao cliente

---

## 2. Contrato de Dados

### 2.1 Tipos Base
- **Datas**: ISO 8601 (`YYYY-MM-DDTHH:mm:ssZ`) — sempre UTC no banco, convertidas para local no frontend
- **Valores monetários**: centavos (inteiros) no banco e na API
- **IDs**: string UUID ou int
- **Booleanos**: `true`/`false` (nunca strings)
- **Nulos**: `null` explícito (nunca omitir campo)

### 2.2 Validação
- **Backend valida tudo**: não confia em dados do frontend
- **Frontend valida para UX**: esquemas Zod como fonte de verdade
- **Schema duplo obrigatório**: se há validação no frontend (Zod), há schema Pydantic correspondente no backend

### 2.3 Enums e Constantes
- Backend define enum: `CRT`, `CST_ICMS`, `StatusOS`
- Frontend consome via tipo TypeScript
- **Sincronização**: mudança em enum backend exige PR no frontend (verificar em code review)

---

## 3. Endpoints

### 3.1 Convenção REST
```
GET    /api/v1/<recurso>              # Listar (com paginação)
POST   /api/v1/<recurso>              # Criar
GET    /api/v1/<recurso>/<id>         # Detalhe
PUT    /api/v1/<recurso>/<id>         # Atualizar (completo)
PATCH  /api/v1/<recurso>/<id>         # Atualizar (parcial)
DELETE /api/v1/<recurso>/<id>         # Deletar
```

### 3.2 Paginação
Query params obrigatórios em lista:
```
?page=1&limit=50&sort=-created_at
```

Resposta:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1000,
    "pages": 20
  }
}
```

### 3.3 Filtros
- Suportar `?field=value` para cada campo indexável
- AND implícito entre filtros
- OR via `?status=aberta,cancelada` (separados por vírgula)

---

## 4. Autenticação e Autorização

### 4.1 JWT
- Token no cookie `Authorization` (HttpOnly, Secure)
- Header alternativo: `Authorization: Bearer <token>`
- Payload contém `sub` (user ID) e `exp`

### 4.2 Middleware
```
1. Validar token (rejeitar se inválido/expirado)
2. Extrair user_id
3. Carregar usuário do banco
4. Injetar em dependência FastAPI
```

### 4.3 Recursos Protegidos
- Todo endpoint `/api/v1/**` exige autenticação
- Sem token: HTTP 401 (frontend redireciona para login)
- Sem permissão: HTTP 403 (frontend mostra toast de acesso negado)

---

## 5. Tratamento de Erros

### 5.1 Conflitos e Validação (422/409)
```json
{
  "status": "error",
  "message": "Conflito ao criar recurso",
  "error_code": "CONFLICT",
  "details": { "field": "email", "value": "ja-existe@example.com" }
}
```

### 5.2 Não Encontrado (404)
```json
{
  "status": "error",
  "message": "Recurso não encontrado",
  "error_code": "NOT_FOUND"
}
```

### 5.3 Erro de Servidor (5xx)
- Log completo no backend com stack trace
- Cliente recebe apenas mensagem genérica + ID de correlação

---

## 6. Estado da Aplicação

### 6.1 Máquina de Estados
Recursos com workflow respeitam transições definidas:
- Backend garante transição válida
- Frontend respeita máquina de estados
- Transição inválida: HTTP 409 `INVALID_STATE_TRANSITION`

### 6.2 Soft Deletes
- Marcar como `deleted_at: datetime`, não remover do banco
- Filtrar automaticamente em LIST
- GET detalhe retorna 404 se deletado

---

## 7. Checklist para Novo Endpoint

- [ ] Schema Pydantic definido
- [ ] Schema Zod correspondente no frontend
- [ ] Validação duplicada (backend + frontend)
- [ ] Autenticação requerida (ou justificar exceção)
- [ ] Teste unitário no backend
- [ ] Documentado em AGENT.md
