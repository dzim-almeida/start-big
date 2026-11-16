# Spec 04A — Base da Marcenaria (Backend): Perda no Produto, Parâmetros e Permissões

| Campo        | Valor                                                                     |
|--------------|---------------------------------------------------------------------------|
| Status       | Implementada em 09/10/2026                                                |
| Camada       | Backend (FastAPI) ⚠️ toca `produtos` (tabela compartilhada)               |
| Dependências | Spec 03A                                                                  |
| Bloqueia     | Spec 04B, Spec 05, Spec 06A                                               |
| Referência   | SPEC-00: F5, F6, C4, C5c, P1, P4, I2, O3, O7, T6 · SPEC-00 (Revisão 15): FB1, R15-MIG · PR1, PR4, PR6, PR7, PR8 |

> **Revisão 1 (08/10/2026) — convergência com a branch (SPEC-00 Revisão 15).** (1) A coluna **`produtos.sofre_perda` já existe** (migração `f1c7a2d9e3b4` da fábrica F1, `Boolean NOT NULL DEFAULT 0`, mesma definição que esta spec pedia): o model não muda e a migração desta spec **não** cria coluna; o que falta é o campo nos schemas do produto e o rótulo no histórico. (2) A migração passa a ser `608dc99a8616`, filha de `d7a3e9c2f418` (R15-MIG). (3) As chaves de permissão ficam em `app/services/marcenaria/permissoes.py`, no padrão de `services/compras/permissoes.py` e `services/fabrica/permissoes.py` (não existe `app/core/permissoes.py`). (4) A lista de unidades fracionáveis é `UNIDADES_FRACIONAVEIS` (`app/services/quantidade_venda.py`). As chaves `view_fabrica`/`manage_fabrica` da fábrica aposentada **não** são reaproveitadas: significavam outra coisa (orçar e liberar compra).

---

## 1. Objetivo

Criar as três peças que o orçamento de marcenaria vai usar, sem nenhuma tela de orçamento ainda:

1. **`produto.sofre_perda`** no contrato do produto: marca quais insumos recebem o fator de perda (MDF e fita sim; ferragem não). A coluna já existe no banco (Revisão 1).
2. **Parâmetros da marcenaria**: os valores padrão que todo orçamento novo copia (markup, perda, validade, prazo de entrega, custo/hora, RT) e as listas padrão de **etapas de produção** e de **checklist de vistoria**.
3. **Permissões** `view_custos_marcenaria` (ver custos e margens) e `manage_custos_marcenaria` (alterar os parâmetros).

E uma capacidade nova, **`orcamento_tecnico`**, que a marcenaria declara e que liga tudo isso só para ela.

## 2. Escopo

**Dentro do escopo**
- Capacidade `orcamento_tecnico` e a função `segmento_tem_capacidade()` (a primeira consulta de capacidade no backend).
- Campo `sofre_perda` nos schemas e no log de edição do produto (a coluna `produtos.sofre_perda` já existe; Revisão 1).
- Tabela `configuracoes_marcenaria` (1:1 com a empresa), CRUD, serviço e endpoints `GET`/`PUT /configuracoes/marcenaria`.
- Duas chaves de permissão e o recorte do `GET` para quem não vê custos.
- Migração Alembic que segue a regra do CLAUDE.md (PR8).
- Testes.

**Fora do escopo**
- Telas: campo no produto, seção em Configurações, linha na matriz de permissões (Spec 04B).
- Motor de cálculo (Spec 05) e orçamento (Spec 06A).
- Permissões de **orçamento** (criar, editar, aprovar): entram na Spec 06A, junto com as rotas que elas protegem.
- **Sinal padrão:** não existe (C7: o percentual é decidido em cada orçamento e pode ser zero).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── alembic/versions/
│   └── 608dc99a8616_base_marcenaria.py          # CRIAR — só a tabela (filha de d7a3e9c2f418; conferir com `alembic heads`)
├── app/
│   ├── core/
│   │   └── segmentos/
│   │       ├── capacidades.py                   # ALTERAR — CAP_ORCAMENTO_TECNICO
│   │       ├── __init__.py                      # ALTERAR — exportar o novo
│   │       └── definicoes/
│   │           ├── __init__.py                  # ALTERAR — segmento_tem_capacidade()
│   │           └── marcenaria.py                # ALTERAR — declara orcamento_tecnico
│   ├── db/
│   │   ├── models/
│   │   │   ├── produto.py                       # CONFERIR — sofre_perda já existe (fábrica F1)
│   │   │   ├── configuracao_marcenaria.py       # CRIAR
│   │   │   ├── empresa.py                       # ALTERAR — relacionamento config_marcenaria
│   │   │   └── __init__.py                      # ALTERAR — registrar o model
│   │   └── crud/configuracao_marcenaria.py      # CRIAR
│   ├── schemas/
│   │   ├── produto.py                           # ALTERAR ⚠️ — sofre_perda em Create/Update/Read
│   │   └── configuracao_marcenaria.py           # CRIAR
│   ├── services/
│   │   ├── produto.py                           # ALTERAR ⚠️ — rótulo "Sofre perda" no log de edição
│   │   ├── configuracao_marcenaria.py           # CRIAR
│   │   └── marcenaria/
│   │       ├── __init__.py                      # CRIAR (vazio; a Spec 05 põe o motor aqui)
│   │       └── permissoes.py                    # CRIAR — chaves da marcenaria (padrão de compras/permissoes.py)
│   └── api/v1/endpoints/configuracao.py         # ALTERAR — GET/PUT /configuracoes/marcenaria
└── test/
    ├── core/test_registry_segmentos.py          # ALTERAR — capacidade nova
    ├── db/test_migracao_base_marcenaria.py      # CRIAR — migração em banco antigo e novo
    └── api/v1/
        ├── test_produto_sofre_perda.py          # CRIAR
        └── test_configuracao_marcenaria.py      # CRIAR
```

| Camada | Faz | Não faz |
|--------|-----|---------|
| `endpoints/configuracao.py` | Lê o token, aplica permissão, escolhe o schema de resposta | Regra |
| `services/configuracao_marcenaria.py` | Get-or-create, validação de segmento, atualização parcial | SQL |
| `crud/configuracao_marcenaria.py` | Consultas e gravação | Regra |

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Capacidade nova **`orcamento_tecnico`**, declarada só pela marcenaria. Os endpoints de parâmetros respondem **404** em segmento sem ela | Regra do registry: nada de `if segmento == "marcenaria"`. A mesma capacidade liga, nas próximas specs, o campo no produto, a seção em Configurações e o menu Orçamentos |
| D2 | Função `segmento_tem_capacidade(segmento, cap)` no registry | Hoje só o frontend consulta capacidades; o backend passa a precisar (D1) |
| D3 | `produtos.sofre_perda`: `Boolean NOT NULL DEFAULT false` — **já existe** (Revisão 1); esta spec só a expõe no contrato | F6. Coluna na tabela compartilhada, mas **aditiva**: nenhum segmento precisa enviá-la, e o padrão mantém o comportamento de todos |
| D4 | O schema do produto **aceita** `sofre_perda` em qualquer segmento; só a tela da marcenaria mostra (04B) | Validar por segmento aqui seria regra sem benefício: o valor só é lido pelo motor da marcenaria |
| D5 | Parâmetros numa tabela própria `configuracoes_marcenaria`, **1:1 com a empresa**, no mesmo padrão de `configuracoes_os` (get-or-create, `PUT` parcial) | Mesmo padrão das 6 configurações existentes |
| D6 | Percentuais em **basis points** (`int`, 9000 = 90,00%); dinheiro em **centavos** (PR4) | Igual a `cargo.comissao_*` |
| D7 | `etapas_producao` e `checklist_vistoria` como **listas JSON** de textos na própria configuração | São listas curtas de nomes, editadas juntas. Cada OS recebe uma **cópia** (P1, I2), então mudar a lista não altera OS já abertas |
| D8 | Duas permissões: **`view_custos_marcenaria`** (ver custos e margens) e **`manage_custos_marcenaria`** (alterar os parâmetros). `manage` implica `view` | P4. Segue o padrão do financeiro (`view_financeiro`/`manage_financeiro`): a chave da matriz de cargos é a **mesma** que o backend confere |
| D9 | `GET /configuracoes/marcenaria`: **qualquer usuário logado**, mas quem **não** tem `view_custos_marcenaria` recebe só os campos **sem custo** (validade, prazo, etapas, checklist) | O orçamento precisa dos padrões para todo vendedor; markup, perda, custo/hora e RT são informação de margem (P4) |
| D10 | `PUT /configuracoes/marcenaria`: exige **`manage_custos_marcenaria`** | Mudar o markup padrão muda o preço de todo orçamento novo |
| D11 | Master e cargo com `all` passam em tudo, como já faz `check_permission` | Comportamento atual do sistema |
| D12 | Sem campo de **sinal padrão** | C7: decidido em cada orçamento, pode ser zero |
| D13 | Validações no schema (Pydantic), com mensagens em português (vão para a tela) | Padrão do projeto |

### 4.1. Campos da configuração e valores padrão

| Campo | Tipo | Padrão | Limites | Vê sem `view_custos`? | Decisão |
|-------|------|--------|---------|------------------------|---------|
| `markup_padrao_bp` | int (bp) | 9000 (90%) | 0 a 100000 (0% a 1000%) | Não | C1 |
| `perda_padrao_bp` | int (bp) | 1000 (10%) | 0 a 5000 (0% a 50%) | Não | C2 |
| `custo_hora_centavos` | int (centavos) | 0 | ≥ 0 | Não | C4 |
| `rt_padrao_bp` | int (bp) | 0 | 0 a 3000 (0% a 30%) | Não | C5 |
| `rt_modo` | `"MARGEM"` \| `"PRECO"` | `"MARGEM"` | enum | Não | C5c |
| `validade_dias` | int | 15 | 1 a 365 | Sim | O3 |
| `prazo_entrega_dias` | int | 30 | 1 a 365 | Sim | O7 |
| `etapas_producao` | lista de texto | Corte, Borda, Furação, Montagem, Embalagem | 1 a 20 itens; 1 a 60 caracteres; sem repetir | Sim | P1 |
| `checklist_vistoria` | lista de texto | ver §4.2 | 1 a 30 itens; 1 a 120 caracteres; sem repetir | Sim | I2 |

`custo_hora_centavos = 0` é permitido: enquanto o dono não configurar, a mão de obra **por horas** dá zero, e a Spec 06B avisa na tela ("custo/hora não configurado").

### 4.2. Checklist de vistoria padrão

Tirado do Figma (Termo de Entrega), em linguagem que serve a qualquer ambiente:

1. Alinhamento de portas e gavetas
2. Acabamento de bordas e vedação com silicone
3. Funcionamento de corrediças, dobradiças e pistões
4. Fixação e nivelamento dos móveis
5. Limpeza final do ambiente

---

## 5. Contrato da API

### 5.1. Produto (`/produtos`)

`ProdutoCreate`, `ProdutoUpdate` e `ProdutoRead` ganham:

```json
{ "sofre_perda": false }
```

Opcional na criação (padrão `false`) e na edição (ausente = não muda). Mais nada muda no contrato do produto.

### 5.2. `GET /api/v1/configuracoes/marcenaria`

Com `view_custos_marcenaria` (ou master/`all`):

```json
{
  "markup_padrao_bp": 9000,
  "perda_padrao_bp": 1000,
  "custo_hora_centavos": 0,
  "rt_padrao_bp": 0,
  "rt_modo": "MARGEM",
  "validade_dias": 15,
  "prazo_entrega_dias": 30,
  "etapas_producao": ["Corte", "Borda", "Furação", "Montagem", "Embalagem"],
  "checklist_vistoria": ["Alinhamento de portas e gavetas", "..."],
  "inclui_custos": true
}
```

Sem a permissão: os mesmos campos **sem custo**, e `"inclui_custos": false`. Os campos de custo **não aparecem** (não vêm como `null`), para a tela não confundir "sem permissão" com "zerado".

### 5.3. `PUT /api/v1/configuracoes/marcenaria`

Corpo parcial (só os campos enviados mudam). Resposta igual ao `GET` completo.

### 5.4. Erros

| Status | `detail` | Quando |
|--------|----------|--------|
| `404` | "Parâmetros de marcenaria não disponíveis para este segmento." | Segmento sem `orcamento_tecnico` (`GET` e `PUT`) |
| `403` | "Permissão negada. Requer: 'manage_custos_marcenaria'" | `PUT` sem a permissão (mensagem padrão do `check_permission`) |
| `422` | mensagens do schema, ex.: "O markup deve ficar entre 0% e 1000%." | Fora dos limites da §4.1; lista vazia, com item vazio, longo demais ou repetido |

---

## 6. Especificação técnica

### 6.1. Capacidade e registry

```python
# capacidades.py
# O segmento orca por ambiente, movel e insumo (BOM), com perda, markup e
# margem (orcamento tecnico da marcenaria, SPEC-00). Liga os parametros da
# marcenaria, a flag "sofre perda" no produto e, nas proximas specs, o menu
# Orcamentos. Segmento que nao declara continua exatamente como antes.
CAP_ORCAMENTO_TECNICO = "orcamento_tecnico"
# ...e acrescentar em CAPACIDADES_CONHECIDAS.
```

```python
# definicoes/__init__.py
def segmento_tem_capacidade(segmento: Optional[str], capacidade: str) -> bool:
    """True se o segmento declara a capacidade. Segmento sem definicao: False."""
    definicao = get_definicao_segmento(segmento)            # None para segmento generico
    return bool(definicao) and capacidade in definicao.get("capacidades", [])
```

`marcenaria.py`: `"capacidades": [CAP_IMAGEM_NA_ENTRADA, CAP_GARANTIA_PRAZO, CAP_ORCAMENTO_TECNICO]`.

### 6.2. Chaves de permissão — `app/services/marcenaria/permissoes.py`

```python
# Chaves de permissao da marcenaria. SAO AS MESMAS da matriz de cargos do
# frontend (positions.constants.ts): o cargo grava a chave e o backend confere a
# mesma chave. Padrao do financeiro (view_financeiro/manage_financeiro).
VER_CUSTOS_MARCENARIA = "view_custos_marcenaria"        # ver custo, margem, markup, RT
GERIR_CUSTOS_MARCENARIA = "manage_custos_marcenaria"    # alterar os parametros de preco

# Quem gere tambem ve (D8): as listas para check_permission e para o recorte.
PERMISSOES_VER_CUSTOS = [VER_CUSTOS_MARCENARIA, GERIR_CUSTOS_MARCENARIA]
PERMISSOES_GERIR_CUSTOS = [GERIR_CUSTOS_MARCENARIA]


def pode_ver_custos_marcenaria(usuario_token: dict) -> bool:
    """Mesma regra do check_permission, sem levantar erro: master, 'all' ou a chave."""
    if usuario_token.get("is_master"):
        return True
    permissoes = usuario_token.get("permissoes") or {}
    if permissoes.get("all"):
        return True
    return any(permissoes.get(p) is True for p in PERMISSOES_VER_CUSTOS)
```

Mesmo padrão de `services/compras/permissoes.py`: as listas de chaves e o `pode_ver_*` sem levantar erro, ao lado do módulo que as usa.

### 6.3. Model — `configuracao_marcenaria.py`

```python
class ConfiguracaoMarcenaria(Base):
    """Parametros padrao do orcamento de marcenaria, por empresa (1:1).

    Todo orcamento novo COPIA estes valores; mudar aqui nao altera orcamento
    nem OS ja existentes. Percentuais em basis points (9000 = 90%), dinheiro em
    centavos (SPEC-00, PR4).
    """
    __tablename__ = "configuracoes_marcenaria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False,
    )
    markup_padrao_bp: Mapped[int] = mapped_column(Integer, default=9000, nullable=False)
    perda_padrao_bp: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    custo_hora_centavos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rt_padrao_bp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rt_modo: Mapped[str] = mapped_column(String(10), default="MARGEM", nullable=False)  # 'MARGEM' | 'PRECO'
    validade_dias: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    prazo_entrega_dias: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    etapas_producao: Mapped[list[str]] = mapped_column(JSON, default=lambda: list(ETAPAS_PADRAO), nullable=False)
    checklist_vistoria: Mapped[list[str]] = mapped_column(JSON, default=lambda: list(CHECKLIST_PADRAO), nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False,
    )
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="config_marcenaria")
```

- `ETAPAS_PADRAO` e `CHECKLIST_PADRAO` são constantes no mesmo arquivo (§4.1, §4.2). O `default=lambda: list(...)` evita que todas as linhas compartilhem a **mesma** lista em memória.
- `Empresa` ganha `config_marcenaria` (`uselist=False`, `cascade="all, delete-orphan"`), espelhando `config_os`.

### 6.4. Schemas — `configuracao_marcenaria.py`

```python
class RtModo(str, Enum):
    MARGEM = "MARGEM"   # o RT sai da margem; o preco nao muda (padrao, C5c)
    PRECO = "PRECO"     # o RT e embutido no preco


def _lista_de_nomes(valores: list[str], maximo_itens: int, maximo_chars: int, nome: str) -> list[str]:
    """Limpa espacos, recusa vazio, longo demais e repetido (sem diferenciar maiusculas)."""
    limpos = [v.strip() for v in valores]
    if not 1 <= len(limpos) <= maximo_itens:
        raise ValueError(f"{nome}: informe de 1 a {maximo_itens} itens.")
    if any(not v for v in limpos):
        raise ValueError(f"{nome}: há um item vazio.")
    if any(len(v) > maximo_chars for v in limpos):
        raise ValueError(f"{nome}: cada item pode ter até {maximo_chars} caracteres.")
    if len({v.casefold() for v in limpos}) != len(limpos):
        raise ValueError(f"{nome}: há itens repetidos.")
    return limpos


class ConfiguracaoMarcenariaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")      # campo desconhecido = 422
    markup_padrao_bp: int | None = Field(None, ge=0, le=100_000)
    perda_padrao_bp: int | None = Field(None, ge=0, le=5_000)
    custo_hora_centavos: int | None = Field(None, ge=0)
    rt_padrao_bp: int | None = Field(None, ge=0, le=3_000)
    rt_modo: RtModo | None = None
    validade_dias: int | None = Field(None, ge=1, le=365)
    prazo_entrega_dias: int | None = Field(None, ge=1, le=365)
    etapas_producao: list[str] | None = None
    checklist_vistoria: list[str] | None = None
    # validators de campo chamando _lista_de_nomes(…, 20, 60, "Etapas de produção")
    # e _lista_de_nomes(…, 30, 120, "Checklist de vistoria").


class ConfiguracaoMarcenariaPublica(BaseModel):
    """O que qualquer usuario logado ve (sem custo; D9)."""
    validade_dias: int
    prazo_entrega_dias: int
    etapas_producao: list[str]
    checklist_vistoria: list[str]
    inclui_custos: bool = False


class ConfiguracaoMarcenariaCompleta(ConfiguracaoMarcenariaPublica):
    """Com custo e margem: so para view_custos_marcenaria (D9)."""
    markup_padrao_bp: int
    perda_padrao_bp: int
    custo_hora_centavos: int
    rt_padrao_bp: int
    rt_modo: RtModo
    inclui_custos: bool = True
```

Mensagens de erro de limite em português, por campo (ex.: "O markup deve ficar entre 0% e 1000%."), via `Field(..., description)` + mensagem customizada no validator, seguindo o padrão dos schemas existentes.

### 6.5. Serviço — `configuracao_marcenaria.py`

```python
def _exigir_orcamento_tecnico(db: Session) -> None:
    """404 fora de segmento com orcamento tecnico (D1)."""
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_ORCAMENTO_TECNICO):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parâmetros de marcenaria não disponíveis para este segmento.",
        )


def obter_configuracao(db: Session, empresa_id: int) -> ConfiguracaoMarcenaria:
    _exigir_orcamento_tecnico(db)
    return crud.get(db, empresa_id) or crud.create(db, empresa_id)    # get-or-create


def atualizar_configuracao(db: Session, empresa_id: int, dados: ConfiguracaoMarcenariaUpdate) -> ConfiguracaoMarcenaria:
    config = obter_configuracao(db, empresa_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():   # so o que veio
        setattr(config, campo, valor.value if isinstance(valor, Enum) else valor)
    return crud.update(db, config)
```

A função `obter_configuracao` também é o ponto que o orçamento (Spec 06A) usa para copiar os padrões.

### 6.6. Endpoints — `configuracao.py`

```python
@router.get("/marcenaria", summary="Parâmetros do orçamento de marcenaria")
def get_configuracao_marcenaria(
    usuario_token: dict = Depends(get_current_active_user),          # qualquer usuario logado (D9)
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    config = _handle_db_transaction(db, configuracao_marcenaria_service.obter_configuracao, empresa_id)
    # Recorte por permissao: sem view_custos, so os campos sem custo (D9).
    if pode_ver_custos_marcenaria(usuario_token):
        return ConfiguracaoMarcenariaCompleta.model_validate(config, from_attributes=True)
    return ConfiguracaoMarcenariaPublica.model_validate(config, from_attributes=True)


@router.put("/marcenaria", response_model=ConfiguracaoMarcenariaCompleta,
            summary="Atualizar parâmetros do orçamento de marcenaria")
def update_configuracao_marcenaria(
    data: ConfiguracaoMarcenariaUpdate,
    usuario_token: dict = Depends(check_permission(required_permission=PERMISSOES_GERIR_CUSTOS)),  # D10
    db: Session = Depends(get_db),
):
    ...  # mesmo padrao do update_configuracao_os
```

- O `GET` devolve dois formatos; declarar `response_model=ConfiguracaoMarcenariaCompleta | ConfiguracaoMarcenariaPublica` para o Swagger, ou devolver o modelo já montado (conferir o padrão aceito pelo projeto).
- **Atenção à ordem das verificações no `PUT`:** a permissão é checada **antes** do segmento. Usuário sem permissão num segmento sem a capacidade recebe `403`, não `404`. É aceitável (não revela dado nenhum).

### 6.7. Produto

- `models/produto.py`: **não muda** (Revisão 1). A coluna já está declarada assim:

```python
    sofre_perda: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False,
        doc="A perda do orçamento (%) entra na quantidade deste insumo (MDF e fita sim, ferragem não)",
    )
```

- `schemas/produto.py`: `sofre_perda: bool = False` em `ProdutoCreate` (logo `ProdutoRead` herda); `sofre_perda: Optional[bool] = None` em `ProdutoUpdate`.
- `services/produto.py`: `"sofre_perda": "Sofre perda"` em `_CAMPO_LEGIVEL`, para o histórico do produto dizer o que mudou. Conferir se a criação copia o campo para o model (se o serviço monta o `ProdutoModel` campo a campo, acrescentar).

> **Nota da implementação (09/10/2026):** `ProdutoUpdate` trata `"sofre_perda": null` como "não enviado" (um `model_validator` tira o campo dos enviados), porque o serviço grava tudo o que veio e a coluna é `NOT NULL`. Coberto pelo caso 08. O teste da fábrica `test_insumo_api.py::test_cadastro_do_produto_nao_muda` foi ajustado: ele comparava a resposta do produto antes e depois de gravar o insumo pela rota da fábrica, e agora `sofre_perda` faz parte dessa resposta (de propósito). Ele continua conferindo que `unidade_consumo` e `consumo_por_unidade` não vazam para o cadastro.

### 6.8. Migração — `608dc99a8616_base_marcenaria.py`

`down_revision = "d7a3e9c2f418"` (a head de 08/10; R15-MIG) e a regra do CLAUDE.md (decidir pelo schema **antigo**; o `create_all()` do startup já pode ter criado a tabela nova). A coluna `produtos.sofre_perda` **não** entra: a `f1c7a2d9e3b4` já a cria, decidindo pela ausência dela.

```python
def upgrade() -> None:
    insp = sa.inspect(op.get_bind())                   # o que o banco tem AGORA
    # Tabela nova: o create_all() do startup costuma cria-la antes; so cria se faltar.
    if not insp.has_table("configuracoes_marcenaria"):
        op.create_table("configuracoes_marcenaria", ...)  # mesmas colunas do model


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table("configuracoes_marcenaria"):     # nao falha num banco sem a tabela
        op.drop_table("configuracoes_marcenaria")
```

Conferir com `alembic heads` qual é a head atual antes de fixar `down_revision`, e seguir o padrão de nome das migrações recentes.

---

## 7. Prova de não regressão (⚠️ PR1)

1. `pytest test/` inteiro antes e depois.
2. **Produto em todos os segmentos:** criar e editar produto sem enviar `sofre_perda` → resposta igual à de hoje, mais `"sofre_perda": false`. O frontend atual ignora a chave nova.
3. **Migração em banco antigo:** copiar um banco de desenvolvimento de antes desta spec, subir o backend (startup roda `create_all()` + `upgrade head`): tabela nova criada, nenhum dado alterado, `produtos.sofre_perda` com os valores que já tinha.
4. **Migração em banco novo:** banco vazio → `create_all()` cria tudo → `upgrade head` não falha (nada a fazer).
5. Endpoints de configuração existentes (`/clientes`, `/produtos`, `/os`, `/vendas`, `/seguranca`) iguais.

## 8. Limitações e observações

- **Chaves antigas × chaves da matriz (conferido):** alguns endpoints conferem chaves antigas (`"produto"`, `"servico"`, `"cargo"`), enquanto a matriz de cargos usa `view_products`, `manage_services` etc. A tela de cargos traduz ao salvar (`applyEndpointPermissions` + `MODULE_PERMISSION_MAP` em `positions.constants.ts`). As chaves da marcenaria são **iguais** nos dois lados, como as do financeiro, e **não** entram no `MODULE_PERMISSION_MAP`.
- **Custo do insumo no orçamento:** qual custo do produto é copiado para o BOM (`estoque.valor_entrada`, o último preço de compra, ou `estoque.custo_medio`)? A decisão fica para a Spec 06A, que é onde o custo é copiado (O3). Recomendação prévia: último preço de compra (é o que o dono vai pagar na próxima chapa).
- **Retirada fracionada (E3b):** a Spec 10A decide "arredonda para cima" pela `unidade_medida` do produto, com a lista que já existe, `UNIDADES_FRACIONAVEIS` (`app/services/quantidade_venda.py`: KG, G, L, ML, M, CM, M2, M3 aceitam fração; o resto, como UN, não). **Não** é preciso coluna nova para isso.
- **Colunas da fábrica no produto:** `unidade_consumo` e `consumo_por_unidade` ficam no banco sem uso (FB1); o motor da Spec 05 trabalha na unidade do estoque.

## 9. Entrega (PR7)

`npm run build:sidecar` depois do merge. A migração nova vai dentro do sidecar (`alembic` é empacotado); conferir que o instalador leva o arquivo da migração.

---

## 10. Critérios de aceite

- [ ] `orcamento_tecnico` está em `CAPACIDADES_CONHECIDAS` e só a marcenaria declara.
- [ ] `segmento_tem_capacidade` responde certo para marcenaria, serigrafia, oficina e segmento genérico.
- [ ] Produto criado sem `sofre_perda` grava `false`; com `true`, grava `true`; a edição altera e aparece no histórico como "Sofre perda alterado".
- [ ] `GET /configuracoes/marcenaria` na marcenaria cria a configuração com os padrões da §4.1 na primeira chamada.
- [ ] Usuário sem `view_custos_marcenaria` recebe só validade, prazo, etapas, checklist e `inclui_custos = false`, **sem** as chaves de custo.
- [ ] `PUT` com `manage_custos_marcenaria` altera só os campos enviados; sem a permissão, `403`.
- [ ] Limites da §4.1 recusados com `422` e mensagem em português; campo desconhecido recusado.
- [ ] Fora da marcenaria, `GET` e `PUT` respondem `404`.
- [ ] Migração passa em banco antigo e em banco novo (§7).
- [ ] Mudar `etapas_producao` não altera nada além da configuração (as OS copiam a lista nas próximas specs).
- [ ] Código novo comentado (PR6); suíte inteira verde.

## 11. Casos de teste

### Registry — `test/core/test_registry_segmentos.py`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `CAP_ORCAMENTO_TECNICO` | Em `CAPACIDADES_CONHECIDAS` |
| 02 | Quem declara `orcamento_tecnico` | Só `marcenaria` (o teste diz isso em voz alta, como o de imagem na entrada) |
| 03 | `segmento_tem_capacidade("marcenaria", CAP_ORCAMENTO_TECNICO)` | `True` |
| 04 | O mesmo para `serigrafia`, `oficina_mecanica`, `None`, `"outros"` | `False` |

### Produto — `test/api/v1/test_produto_sofre_perda.py`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 05 | `POST /produtos` sem o campo (qualquer segmento) | `sofre_perda = false` |
| 06 | `POST` com `sofre_perda = true` | Gravado `true` |
| 07 | `PUT` mudando para `true` | Alterado; movimentação `EDICAO_DADOS` com "Sofre perda" na observação |
| 08 | `PUT` sem o campo | Valor anterior mantido |

### Configuração — `test/api/v1/test_configuracao_marcenaria.py`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 09 | Marcenaria, master, `GET` | `200`, padrões da §4.1, `inclui_custos = true` |
| 10 | Marcenaria, cargo **sem** a permissão, `GET` | `200`, só os 4 campos sem custo; chaves `markup_padrao_bp`, `perda_padrao_bp`, `custo_hora_centavos`, `rt_padrao_bp`, `rt_modo` **ausentes** |
| 11 | Cargo com `view_custos_marcenaria`, `GET` | Completo |
| 12 | Cargo com `view_custos_marcenaria`, `PUT` | `403` |
| 13 | Cargo com `manage_custos_marcenaria`, `PUT { markup_padrao_bp: 8000 }` | `200`; só o markup mudou |
| 14 | `PUT { markup_padrao_bp: 100001 }` | `422` com mensagem em português |
| 15 | `PUT { etapas_producao: [] }`, `[" "]`, `["Corte", "corte"]`, item com 61 caracteres | `422` nos quatro |
| 16 | `PUT { etapas_producao: ["  Corte  ", "Borda"] }` | Gravado `["Corte", "Borda"]` (espaços removidos) |
| 17 | `PUT { rt_modo: "OUTRO" }` | `422` |
| 18 | `PUT { campo_inventado: 1 }` | `422` |
| 19 | Serigrafia, master, `GET` e `PUT` | `404` nos dois |
| 20 | Duas chamadas `GET` seguidas | Uma linha só em `configuracoes_marcenaria` |

### Migração — `test/db/test_migracao_base_marcenaria.py`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 21 | Banco na `d7a3e9c2f418` sem a tabela; `upgrade()` | Tabela de configuração criada; `produtos` intacta |
| 22 | Banco já com a tabela (criada pelo `create_all`); `upgrade()` | Nada muda, sem erro |
| 22a | `downgrade()` e `upgrade()` de novo | Tabela removida e recriada, sem erro |
