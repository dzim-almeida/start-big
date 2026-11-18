# SPEC 1 — Modelagem de Dados: PerfilTributário e RegraPerfilTributário

## 1. Objetivo

Criar as duas tabelas que armazenam a matriz de regras tributárias interestaduais — `perfil_tributario` e `regra_perfil_tributario` — e a migration Alembic correspondente.

Ao final desta spec, o banco de dados terá a estrutura para que um perfil agrupe N regras de DIFAL e ICMS-ST, organizadas por UF de destino e exceção de NCM, sem nenhum impacto no sistema existente.

---

## 2. Contexto: Por que esta estrutura existe

### 2.1. O problema que o PerfilTributário resolve

Hoje o sistema emite NF-e **apenas para operações internas** (mesma UF). Toda tentativa de emissão interestadual é bloqueada por uma trava explícita no [`resolver.py:130-139`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/resolver.py#L130-L139):

```python
raise OperacaoInterestadualError(
    "Operação interestadual não presencial detectada (...). "
    "DIFAL/FCP não implementado.",
)
```

Para desbloquear operações interestaduais, o motor fiscal precisa de **alíquotas que variam por UF de destino**: a alíquota interestadual (7% ou 12%, conforme a tabela da CF/88), a alíquota interna do estado destino (17% a 22%), o FCP (0% a 4%), e para contribuintes, a MVA de substituição tributária.

Se cada produto cadastrasse essas alíquotas para cada UF, seriam **27 UFs × N produtos** configurações — inviável para uma loja de varejo. O **PerfilTributário** resolve isso agrupando regras em "perfis" reutilizáveis: um perfil "Varejo - Eletrônicos" define as alíquotas para cada UF uma vez, e todos os produtos eletrônicos apontam para ele.

### 2.2. A cascata existente e como o perfil se encaixa

O sistema já possui uma cascata tributária elegante em [`tributacao.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tributacao.py):

```
produto.fiscal → regra por NCM → tributação padrão da loja
```

Essa cascata resolve **CST/CSOSN, CFOP, PIS/COFINS, alíquota ICMS interna** — tudo que é necessário para operações internas. O perfil tributário **não substitui** esta cascata. Ele a **complementa** com dados que só existem em operações interestaduais:

| Dado | Cascata existente | Perfil Tributário |
|------|-------------------|-------------------|
| CST/CSOSN | ✅ | ❌ |
| CFOP | ✅ | ❌ |
| Alíquota ICMS interna | ✅ | ❌ |
| PIS/COFINS | ✅ | ❌ |
| Alíquota interestadual | ❌ | ✅ |
| Alíquota interna do destino | ❌ | ✅ |
| FCP do destino | ❌ | ✅ |
| Base dupla (DIFAL) | ❌ | ✅ |
| MVA (substituição tributária) | ❌ | ✅ |
| Redução de base ST | ❌ | ✅ |

### 2.3. A hierarquia de match das regras

Cada perfil contém N regras com prioridade de especificidade:

| Prioridade | `uf_destino` | `ncm_excecao` | Significado |
|------------|-------------|---------------|-------------|
| 1 (mais específica) | `"SP"` | `"85171200"` | Celulares vendidos para SP |
| 2 | `"SP"` | `NULL` | Qualquer produto vendido para SP |
| 3 (fallback) | `NULL` | `NULL` | Qualquer produto para qualquer UF |

A regra fallback (prioridade 3) garante que **toda operação encontre uma resposta**, mesmo que o contador não tenha configurado regras específicas para cada UF.

---

## 3. Detalhamento: Model `PerfilTributario`

**Arquivo**: `app/db/models/perfil_tributario.py`

### 3.1. Definição da classe

```python
class PerfilTributario(Base):
    __tablename__ = "perfil_tributario"
```

### 3.2. Campos

| Campo | Tipo SQLAlchemy | Tipo Python | Nullable | Constraint | Descrição |
|-------|----------------|-------------|----------|------------|-----------|
| `id` | `Integer` | `Mapped[int]` | Não | PK, autoincrement | Identificador único do perfil |
| `empresa_id` | `Integer` | `Mapped[int]` | Não | FK → `empresas.id`, ondelete CASCADE | Empresa dona do perfil. Cada empresa tem seus próprios perfis |
| `descricao` | `String(120)` | `Mapped[str]` | Não | — | Nome legível do perfil (ex: "Varejo - Eletrônicos", "Peças Automotivas - ST") |
| `data_criacao` | `DateTime` | `Mapped[datetime]` | Não | default=`func.now()` | Quando o perfil foi criado |
| `data_atualizacao` | `DateTime` | `Mapped[datetime]` | Não | default=`func.now()`, onupdate=`func.now()` | Última modificação |

### 3.3. Relacionamentos

| Relacionamento | Tipo | Target | Cascade | Descrição |
|----------------|------|--------|---------|-----------|
| `regras` | One-to-Many | `RegraPerfilTributario` | `all, delete-orphan` | Ao deletar o perfil, todas as regras são removidas |

### 3.4. Decisões de design

**Por que `Integer` e não `UUID` para a PK?**

O sistema inteiro — [`ProdutoFiscal`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/produto_fiscal.py), [`TributacaoPadrao`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/tributacao.py#L81), [`RegraTributariaNcm`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/tributacao.py#L116), [`DocumentoFiscal`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/documento_fiscal.py) — usa Integer autoincrement. O banco é SQLite (local, monousuário). UUID traria:
- Inconsistência com todas as FKs do sistema
- JOINs mais lentos no SQLite (string vs integer)
- Nenhum benefício real, pois não há replicação distribuída

**Por que `String(120)` na descrição?**

Segue o padrão de [`RegraTributariaNcm.descricao`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/tributacao.py#L143-L144) que usa `String(120)`. É suficiente para nomes descritivos como "Varejo Geral - Eletrônicos com ST" sem desperdiçar espaço.

---

## 4. Detalhamento: Model `RegraPerfilTributario`

**Arquivo**: `app/db/models/regra_perfil_tributario.py`

### 4.1. Definição da classe

```python
class RegraPerfilTributario(Base):
    __tablename__ = "regra_perfil_tributario"
```

### 4.2. Campos

| Campo | Tipo SQLAlchemy | Tipo Python | Nullable | Default | Descrição |
|-------|----------------|-------------|----------|---------|-----------|
| `id` | `Integer` | `Mapped[int]` | Não | PK, auto | Identificador da regra |
| `perfil_id` | `Integer` | `Mapped[int]` | Não | FK → `perfil_tributario.id`, ondelete CASCADE | Perfil ao qual pertence |
| `uf_destino` | `String(2)` | `Mapped[Optional[str]]` | **Sim** | `None` | UF destino (ex: "SP"). Se NULL, é regra de fallback |
| `ncm_excecao` | `String(8)` | `Mapped[Optional[str]]` | **Sim** | `None` | NCM específico (ex: "85171200"). Se NULL, vale para todos os NCMs |
| `aliquota_interestadual` | `Integer` | `Mapped[int]` | Não | — | Alíquota interestadual em centésimos (ex: 1200 = 12,00%) |
| `aliquota_interna_destino` | `Integer` | `Mapped[int]` | Não | — | Alíquota interna da UF de destino em centésimos (ex: 1800 = 18,00%) |
| `percentual_fcp` | `Integer` | `Mapped[int]` | Não | `0` | Fundo de Combate à Pobreza em centésimos (ex: 200 = 2,00%) |
| `calculo_base_dupla` | `Boolean` | `Mapped[bool]` | Não | `False` | Se True, usa fórmula de base dupla no cálculo do DIFAL |
| `mva_st` | `Integer` | `Mapped[Optional[int]]` | **Sim** | `None` | Margem de Valor Agregado para ST em centésimos. Se preenchido e > 0, indica que há substituição tributária |
| `reducao_base_calculo` | `Integer` | `Mapped[Optional[int]]` | **Sim** | `None` | Percentual de redução da base de cálculo do ST em centésimos |

### 4.3. Constraints

```python
__table_args__ = (
    UniqueConstraint(
        "perfil_id", "uf_destino", "ncm_excecao",
        name="uq_regra_perfil_uf_ncm",
    ),
)
```

Esta constraint impede que o mesmo perfil tenha duas regras para a mesma combinação de UF e NCM. Ela funciona corretamente com NULLs no SQLite — duas linhas com `uf_destino=NULL, ncm_excecao=NULL` são consideradas distintas pelo SQL padrão, mas **a validação de unicidade de fallback será feita na camada de serviço** (SPEC 2), não pelo banco.

### 4.4. Relacionamentos

| Relacionamento | Tipo | Target | Descrição |
|----------------|------|--------|-----------|
| `perfil` | Many-to-One | `PerfilTributario` | Perfil ao qual a regra pertence |

### 4.5. Decisões de design

**Por que alíquotas em centésimos (Integer) e não Numeric(5,2)?**

Todo o sistema armazena valores percentuais como Integer em centésimos de ponto percentual:

- [`ProdutoFiscal.aliquota_icms`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/produto_fiscal.py#L89-L92): `"1800 = 18,00%"`
- [`AliquotaUF.aliquota_icms_interna`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/aliquota_uf.py): mesmo padrão
- [`TributacaoPadrao`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/tributacao.py#L63): `aliquota_icms` como Integer

O [`resolver.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/resolver.py#L41-L48) converte para Decimal na hora do cálculo via `_centesimos_para_decimal()`. Usar `Numeric(5,2)` aqui obrigaria o resolver a tratar dois formatos diferentes, introduzindo bugs silenciosos de arredondamento.

**Por que incluir `mva_st` e `reducao_base_calculo` já na SPEC 1?**

A spec original os coloca na segunda spec (expansão). Porém, como são campos da mesma tabela `regra_perfil_tributario`, adicioná-los depois exigiria uma segunda migration na mesma tabela. Incluí-los agora:
- Evita migration adicional
- Os campos são nullable, então não impactam nada
- O motor de cálculo ST (SPEC 5) os usará sem precisar alterar schema

**Por que `uf_destino` é `String(2)` e não um Enum?**

O sistema usa strings para UF em vários lugares ([`Endereco.estado`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/endereco.py) usa Enum, mas o resolver converte para string). Manter String(2) permite flexibilidade e evita migrations quando novos territórios forem criados (Fernando de Noronha teve código próprio até 1988). A validação de UF válida será feita no schema Pydantic (SPEC 2).

---

## 5. Migration Alembic

### 5.1. Arquivo

Nome sugerido: `xxxx_criar_perfil_tributario.py` (o prefixo hash será gerado pelo Alembic)

### 5.2. Operações `upgrade()`

1. Criar tabela `perfil_tributario`:
   - `id` INTEGER PK AUTOINCREMENT
   - `empresa_id` INTEGER NOT NULL FK → empresas.id (ondelete CASCADE)
   - `descricao` VARCHAR(120) NOT NULL
   - `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
   - `data_atualizacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
   - INDEX em `empresa_id`

2. Criar tabela `regra_perfil_tributario`:
   - `id` INTEGER PK AUTOINCREMENT
   - `perfil_id` INTEGER NOT NULL FK → perfil_tributario.id (ondelete CASCADE)
   - `uf_destino` VARCHAR(2) NULLABLE
   - `ncm_excecao` VARCHAR(8) NULLABLE
   - `aliquota_interestadual` INTEGER NOT NULL
   - `aliquota_interna_destino` INTEGER NOT NULL
   - `percentual_fcp` INTEGER NOT NULL DEFAULT 0
   - `calculo_base_dupla` BOOLEAN NOT NULL DEFAULT FALSE
   - `mva_st` INTEGER NULLABLE
   - `reducao_base_calculo` INTEGER NULLABLE
   - INDEX em `perfil_id`
   - UNIQUE CONSTRAINT em `(perfil_id, uf_destino, ncm_excecao)`

### 5.3. Operações `downgrade()`

1. DROP TABLE `regra_perfil_tributario`
2. DROP TABLE `perfil_tributario`

(Nesta ordem, porque `regra_perfil_tributario` tem FK para `perfil_tributario`)

---

## 6. Registro dos models

### 6.1. Import no `__init__` de models

Garantir que os novos models sejam importados em `app/db/models/__init__.py` (ou equivalente) para que o Alembic os detecte automaticamente no `autogenerate`.

### 6.2. Arquivo `__repr__`

Cada model deve ter `__repr__` legível para debugging:

```python
# PerfilTributario
def __repr__(self) -> str:
    return f"<PerfilTributario(id={self.id}, descricao={self.descricao!r})>"

# RegraPerfilTributario  
def __repr__(self) -> str:
    return f"<RegraPerfilTributario(id={self.id}, perfil_id={self.perfil_id}, uf={self.uf_destino!r}, ncm={self.ncm_excecao!r})>"
```

---

## 7. Critérios de Aceite

### CA-1: Models existem e estão corretos
- [ ] Arquivo `app/db/models/perfil_tributario.py` existe com a classe `PerfilTributario`
- [ ] Arquivo `app/db/models/regra_perfil_tributario.py` existe com a classe `RegraPerfilTributario`
- [ ] Ambos herdam de `Base` (mesma base declarativa do sistema)
- [ ] Todos os campos listados na seção 3 e 4 estão presentes com os tipos corretos
- [ ] Relacionamento `regras` no `PerfilTributario` com `cascade="all, delete-orphan"`
- [ ] Relacionamento `perfil` no `RegraPerfilTributario`
- [ ] UniqueConstraint `(perfil_id, uf_destino, ncm_excecao)` declarada

### CA-2: Migration funciona
- [ ] Migration Alembic criada e aplica sem erro em banco limpo
- [ ] `downgrade()` remove as tabelas na ordem correta (regra primeiro, perfil depois)
- [ ] Nenhuma tabela existente é alterada

### CA-3: Zero impacto no sistema existente
- [ ] Todos os testes existentes continuam passando (`pytest` verde)
- [ ] Nenhum arquivo existente foi modificado além do import de models (se necessário)
- [ ] A cascata tributária existente (`tributacao.py`) não é tocada
- [ ] O tax engine não é tocado
- [ ] O payload builder não é tocado
- [ ] O frontend não é tocado

### CA-4: Convenções do projeto respeitadas
- [ ] PKs são `Integer` autoincrement (não UUID)
- [ ] Alíquotas são `Integer` em centésimos de ponto percentual (padrão do sistema)
- [ ] Docstrings presentes em todos os campos (atributo `doc=` no `mapped_column`)
- [ ] `__repr__` implementado em ambos os models
- [ ] Nomes de tabela em snake_case, singular (`perfil_tributario`, não `perfis_tributarios`)

### CA-5: Integridade referencial
- [ ] `perfil_tributario.empresa_id` referencia `empresas.id` com `ondelete=CASCADE`
- [ ] `regra_perfil_tributario.perfil_id` referencia `perfil_tributario.id` com `ondelete=CASCADE`
- [ ] Deletar uma empresa deleta seus perfis em cascata
- [ ] Deletar um perfil deleta suas regras em cascata

---

## Desvios aplicados (2026-09-18)
Ver `docs/done/fiscal/TASK004.md` § "Desvios da spec": `server_default` nas colunas com default; migration à mão (sem autogenerate) que decide pela ausência da tabela; índice em `id` pelo padrão do projeto. Todos os CAs atendidos — 16 testes novos, gate 909 passed.
