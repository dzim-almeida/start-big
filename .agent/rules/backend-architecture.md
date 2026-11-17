# Regra — Arquitetura do Backend (camadas FastAPI)

**Status:** obrigatória · **Escopo:** `backend-fastapi/app/` · **Origem:** estrutura atual de `app/` e a seção "Backend" do `CLAUDE.md`.

Se esta regra e uma spec divergirem, a spec ativa vence. Nesse caso, pare e pergunte se a regra deve ser atualizada.

---

## 1. Estrutura

```
backend-fastapi/
├── app/
│   ├── main.py                   # Composição: cria o app, handlers de erro, routers, startup
│   ├── api/v1/
│   │   ├── api.py                # Junta todos os routers sob /api/v1
│   │   └── endpoints/            # Um arquivo por recurso (cliente.py, produto.py...)
│   ├── services/{domínio}/       # Regras de negócio
│   ├── db/
│   │   ├── session.py            # engine e get_db (sessão SQLAlchemy síncrona)
│   │   ├── base.py               # Base declarativa
│   │   ├── models/               # Models ORM (um arquivo por tabela ou pacote por segmento)
│   │   ├── crud/{domínio}/       # Consultas e gravações
│   │   └── migrations.py         # Aplica o Alembic no startup
│   ├── schemas/{domínio}/        # Pydantic: entrada (Create/Update) e saída (Read)
│   ├── helpers/                  # Utilitários de API (paginação, exceções)
│   └── core/                     # Config, segurança, dependências, validadores, infraestrutura
├── alembic/versions/             # Migrações (versionadas, viajam com o código)
└── test/                         # pytest: api/, services/, core/, db/
```

**Domínio novo** = uma pasta com o mesmo nome em `schemas/`, `services/` e `db/crud/`, mais o(s) model(s) em `db/models/` e um arquivo em `api/v1/endpoints/`.

---

## 2. Responsabilidade estrita de cada camada

| Camada | Faz | **Não faz** |
|--------|-----|-------------|
| `endpoints/*.py` (router) | Declara rota, método, `status_code`, `response_model` e permissão (`Depends(check_permission(...))`). Entrega o trabalho ao service **dentro de `_handle_db_transaction`**. | Regra de negócio, `db.query(...)`, `commit`, montar resposta à mão |
| `schemas/` | Valida entrada, serializa saída, documenta a API. Validação de **formato** (tamanho, padrão, tipo). | Consulta ao banco, regra que depende de outro registro |
| `services/` | Regra de negócio: decide, calcula, orquestra vários `crud`. Levanta `HTTPException` (ou `ValueError`) para erro de negócio. Recebe `db` e `empresa_id` como parâmetro. | Importar `fastapi.Request`, conhecer o formato HTTP além das exceções, dar `commit` |
| `db/crud/` | Consulta e grava via SQLAlchemy. Sempre filtra por `empresa_id` quando a tabela é de negócio. Faz `db.add` / `db.flush`. | Regra de negócio, decidir status HTTP, dar `commit` |
| `db/models/` | Tabelas, colunas, relacionamentos, constraints e `doc=` explicando campos importantes. | Lógica de negócio |
| `core/depends.py` | Dependências reutilizáveis: usuário atual, `check_permission`, `_handle_db_transaction`, módulo habilitado. | Regra específica de um domínio |
| `core/` (resto) | Infraestrutura transversal: config, segurança, validadores, tempo, descoberta de rede. | Importar de `services/` ou `endpoints/` (exceto `depends.py`, que já liga as peças) |

### Transação: quem dá o `commit`?

**Só o `_handle_db_transaction`** (em `core/depends.py`). Ele roda o service, faz `commit` se deu certo e `rollback` se deu erro, traduzindo `ValueError` em `409`. Consequências:

- Service e crud usam `db.flush()` quando precisam do `id` gerado, nunca `db.commit()`.
- Uma operação = um `_handle_db_transaction` = uma transação. Não encadeie dois dentro da mesma requisição.
- Leitura (GET) pode chamar o service direto, sem o wrapper.

```python
# Exemplo (comentado para quem está começando)
@router.post("/", response_model=ProdutoRead, status_code=status.HTTP_201_CREATED)
def criar_produto(
    dados: ProdutoCreate,                                              # corpo da requisição, já validado pelo Pydantic
    user_token: dict = Depends(check_permission("produto")),           # exige login + permissão "produto"
    db: Session = Depends(get_db),                                     # sessão do banco desta requisição
):
    # O wrapper executa o service e decide commit/rollback; o endpoint não decide nada.
    return _handle_db_transaction(
        db, produto_service.criar, dados, empresa_id=user_token["empresa_id"]
    )
```

---

## 3. Regras de dependência entre camadas

```
endpoint → service → crud → model
   └──────→ schema (usado por todos os de cima)
```

1. Cada camada só importa da **mesma linha ou de baixo**. `crud` nunca importa `service`; `model` nunca importa `crud`.
2. `endpoint` **nunca** importa `crud` nem `models` direto.
3. `core/` não importa de `services/` nem de `db/crud/` (a exceção histórica é `core/depends.py`; não crie outras).
4. Um service pode chamar o **service de outro domínio** (ex.: `vendas` usando `estoque`), nunca o `crud` do outro domínio. Evite ciclo: se A chama B e B chama A, extraia o trecho comum.
5. Import de pacote: o app inteiro usa `from app....` (nunca caminho relativo com `..`).
6. Cada pasta de domínio tem `__init__.py` reexportando o que os outros usam (`from app.services import cliente as cliente_service`).

---

## 4. Isolamento por empresa (inegociável)

Dado de uma empresa **nunca** aparece para outra.

1. Toda tabela de negócio tem `empresa_id` (FK para `empresas.id`, indexado).
2. O `empresa_id` vem do **token** (`user_token["empresa_id"]`, preenchido por `check_permission`), **nunca** do corpo, da query string ou da URL. Schema de entrada **não** tem campo `empresa_id`.
3. **Toda** consulta e gravação em tabela de negócio filtra por `empresa_id`. `db.get(Model, id)` sozinho é proibido para tabela de negócio: use um `crud` que filtre.
4. Registro de outra empresa responde **`404`** (não `403`), para não revelar que o `id` existe.
5. Usuário sem empresa vinculada recebe `403` (já tratado em `check_permission`). O usuário "master" passa direto: não use `is_master` como atalho em regra de negócio.
6. Todo domínio novo vem com **um teste de isolamento**: criar o registro na empresa A e provar que a empresa B recebe `404` ao ler, alterar e apagar.

---

## 5. Convenções

- **Idioma:** nomes, campos de banco e mensagens em PT-BR (como o `CLAUDE.md`). Comentário e docstring em PT-BR explicando o **porquê** e o **o quê** de forma simples.
- **Sessão síncrona.** O backend usa `Session` do SQLAlchemy síncrono e `def` (não `async def`) nos endpoints e services. Não misture `async` sem spec.
- **SQLite:** o banco é um arquivo local. Não use recurso exclusivo de outro banco (tipo `ARRAY`, `FOR UPDATE`). Dinheiro e quantidade com `Numeric`/`Decimal`, nunca `float`.
- **Erros de negócio:** `HTTPException` com mensagem clara em PT-BR para o usuário final; `ValueError` no service vira `409` pelo wrapper. Nunca devolva texto de exceção interna (stack, SQL) na resposta.
- **Log:** use `logging.getLogger(__name__)`. **Não** use `print` em código novo (o `_handle_db_transaction` ainda usa por legado; não replique). Nunca registre senha, token, CPF/CNPJ inteiro nem conteúdo de XML fiscal.
- **Permissão:** toda rota autenticada declara `check_permission("<permissão>")`. Rota de segmento ou módulo opcional também exige o módulo habilitado (`core/modulos.py`).
- **Configuração:** valores vêm de `core/config.py` (variáveis de ambiente). Segredo nunca no código.
- **Empacotamento:** o backend vira `.exe` por PyArmor + PyInstaller. Evite `exec`/`eval`, import dinâmico por string e leitura de arquivo relativo ao código; arquivo de dados novo (`app/data/`) precisa estar listado no `run.spec`.
- **Teste:** `pytest` com SQLite em memória (`test/conftest.py`). Estrutura espelhada: `test/api/`, `test/services/`, `test/core/`, `test/db/`.

---

## 6. Checklist rápido antes de criar um arquivo

1. É **rota** (endpoint), **forma do dado** (schema), **regra** (service), **banco** (crud/model) ou **infraestrutura** (core)? A tabela da §2 dá o lugar.
2. O `empresa_id` está sendo lido do token e aplicado em toda consulta?
3. Quem dá o `commit`? (Resposta certa: o `_handle_db_transaction`.)
4. Mexi em `models/`? Então tem migração (skill `migration`).
5. Mexi em qualquer arquivo de `app/`? Então o sidecar ficou velho (avisar o usuário).
6. Existe teste para o comportamento novo e para o isolamento por empresa (skill `tdd`)?
