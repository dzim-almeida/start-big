# SPEC 2 — CRUD + API REST de Perfis Tributários

## 1. Objetivo

Expor endpoints REST para criar, listar, visualizar, atualizar e deletar perfis tributários e suas regras. Inclui os schemas Pydantic de validação, o módulo CRUD, os endpoints no router fiscal existente, e as telas de frontend (listagem + formulário).

Ao final desta spec, o contador ou o lojista poderá cadastrar perfis como "Varejo - Eletrônicos" com regras por UF e exceções por NCM, tudo via interface. Nenhum cálculo tributário é ativado ainda — isso é SPEC 4+.

---

## 2. Contexto: Onde isso se encaixa

### 2.1. O router fiscal existente

Todos os endpoints fiscais vivem em [`app/api/v1/endpoints/fiscal.py`](file:///c:/dev/bigpdv/backend-fastapi/app/api/v1/endpoints/fiscal.py). O router é protegido por `requer_modulo("NFE")` no nível do router inteiro ([linha 71](file:///c:/dev/bigpdv/backend-fastapi/app/api/v1/endpoints/fiscal.py#L71)), o que garante que apenas lojas com licença fiscal ativa acessem.

Os endpoints de configuração (tributação padrão, regras NCM, certificado) usam `requer_configuracao_fiscal` — um nível de permissão mais brando que permite configurar antes de contratar o plano completo. Os perfis tributários seguirão esse mesmo padrão, pois são **configuração**, não emissão.

### 2.2. Padrão de CRUD existente

O sistema segue um padrão consistente para CRUDs fiscais. Tomando como referência as regras de NCM ([`app/db/crud/tributacao.py`](file:///c:/dev/bigpdv/backend-fastapi/app/db/crud/tributacao.py)):

- CRUD em `app/db/crud/perfil_tributario.py` — funções puras que recebem `Session`
- Schemas em `app/schemas/perfil_tributario.py` — validação Pydantic
- Endpoints em `app/api/v1/endpoints/fiscal.py` — delegam ao CRUD, tratam transação via `_handle_db_transaction`

### 2.3. O formulário aninhado (perfil + regras)

A particularidade desta API em relação aos CRUDs existentes é que o perfil chega com suas regras **em bloco**. Não existe endpoint separado para adicionar/remover regras individuais — o frontend envia o perfil com a lista completa de regras, e o backend faz replace-all. Essa decisão simplifica o frontend (um único POST/PUT) e evita estados inconsistentes (perfil sem regra fallback).

---

## 3. Detalhamento: Schemas Pydantic

**Arquivo**: `app/schemas/perfil_tributario.py`

### 3.1. `RegraPerfilTributarioBase`

Schema de entrada para uma regra individual dentro do perfil.

| Campo | Tipo | Obrigatório | Validação | Descrição |
|-------|------|-------------|-----------|-----------|
| `uf_destino` | `Optional[str]` | Não | Se preenchido: exatamente 2 caracteres, uppercase, deve ser UF válida do Brasil | UF de destino. NULL = fallback |
| `ncm_excecao` | `Optional[str]` | Não | Se preenchido: exatamente 8 dígitos numéricos | NCM específico. NULL = todos os NCMs |
| `aliquota_interestadual` | `int` | Sim | `>= 0`, `<= 2500` (máx 25%) | Alíquota interestadual em centésimos |
| `aliquota_interna_destino` | `int` | Sim | `>= 0`, `<= 3500` (máx 35%) | Alíquota interna da UF destino em centésimos |
| `percentual_fcp` | `int` | Não | `>= 0`, `<= 600` (máx 6%) | FCP em centésimos. Default: `0` |
| `calculo_base_dupla` | `bool` | Não | — | Default: `False` |
| `mva_st` | `Optional[int]` | Não | Se preenchido: `>= 0`, `<= 50000` (máx 500%) | MVA para ST em centésimos. NULL = sem ST |
| `reducao_base_calculo` | `Optional[int]` | Não | Se preenchido: `>= 0`, `<= 10000` (máx 100%) | Redução da base ST em centésimos |

**Validações de campo (`field_validator`)**:

```python
UFS_VALIDAS = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
}

@field_validator("uf_destino")
def validar_uf(cls, v):
    if v is None:
        return v
    v = v.strip().upper()
    if v not in UFS_VALIDAS:
        raise ValueError(f"UF '{v}' não é válida.")
    return v

@field_validator("ncm_excecao")
def validar_ncm(cls, v):
    if v is None:
        return v
    v = v.strip()
    if not v.isdigit() or len(v) != 8:
        raise ValueError("NCM deve conter exatamente 8 dígitos numéricos.")
    return v
```

### 3.2. `PerfilTributarioCreate`

Schema de entrada para criar um perfil com suas regras.

| Campo | Tipo | Obrigatório | Validação | Descrição |
|-------|------|-------------|-----------|-----------|
| `descricao` | `str` | Sim | `min_length=3`, `max_length=120`, strip whitespace | Nome do perfil |
| `regras` | `list[RegraPerfilTributarioBase]` | Sim | `min_length=1` | Deve conter ao menos 1 regra |

**Validações de modelo (`model_validator`)**:

```python
@model_validator(mode="after")
def validar_regras(self):
    # 1. Exatamente uma regra fallback (uf=None, ncm=None)
    fallbacks = [r for r in self.regras if r.uf_destino is None and r.ncm_excecao is None]
    if len(fallbacks) == 0:
        raise ValueError(
            "O perfil deve conter uma regra de fallback (UF e NCM vazios) "
            "que será usada quando não houver regra específica para o destino."
        )
    if len(fallbacks) > 1:
        raise ValueError("O perfil não pode ter mais de uma regra de fallback.")
    
    # 2. Sem duplicatas de (uf, ncm)
    chaves = [(r.uf_destino, r.ncm_excecao) for r in self.regras]
    if len(chaves) != len(set(chaves)):
        raise ValueError(
            "Existem regras duplicadas (mesma UF e mesmo NCM). "
            "Cada combinação de UF e NCM deve aparecer apenas uma vez."
        )
    
    return self
```

**Por que validar o fallback no schema e não no banco?**

O SQL padrão trata `NULL != NULL`, então a UniqueConstraint do banco **não impede** duas regras com `uf_destino=NULL, ncm_excecao=NULL`. A garantia precisa vir da camada de validação. Isso é consistente com o padrão do sistema — o [`validators.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/validators.py) fiscal já faz validações que o banco não cobre.

### 3.3. `PerfilTributarioUpdate`

Idêntico ao `PerfilTributarioCreate`. O update é um replace-all: o frontend envia a lista completa de regras e o backend apaga as antigas e cria as novas dentro da mesma transação.

Herda de `PerfilTributarioCreate` ou é definido como alias — a escolha é de implementação.

### 3.4. `RegraPerfilTributarioRead`

Schema de leitura de uma regra, com o `id` incluído.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `int` | ID da regra |
| (todos os campos de `RegraPerfilTributarioBase`) | — | Mesmos campos de entrada |

```python
class RegraPerfilTributarioRead(RegraPerfilTributarioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

### 3.5. `PerfilTributarioRead`

Schema de leitura de um perfil com suas regras.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `int` | ID do perfil |
| `descricao` | `str` | Nome do perfil |
| `regras` | `list[RegraPerfilTributarioRead]` | Regras do perfil com IDs |
| `data_criacao` | `datetime` | Quando foi criado |
| `data_atualizacao` | `datetime` | Última modificação |

```python
class PerfilTributarioRead(BaseModel):
    id: int
    descricao: str
    regras: list[RegraPerfilTributarioRead]
    data_criacao: datetime
    data_atualizacao: datetime
    model_config = ConfigDict(from_attributes=True)
```

### 3.6. `PerfilTributarioListItem`

Schema enxuto para listagem (sem carregar todas as regras).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `int` | ID do perfil |
| `descricao` | `str` | Nome do perfil |
| `quantidade_regras` | `int` | Total de regras no perfil |
| `data_atualizacao` | `datetime` | Última modificação |

---

## 4. Detalhamento: Módulo CRUD

**Arquivo**: `app/db/crud/perfil_tributario.py`

### 4.1. Funções

| Função | Assinatura | Descrição |
|--------|-----------|-----------|
| `listar_perfis` | `(db: Session, empresa_id: int) → list[PerfilTributario]` | Lista todos os perfis da empresa, ordered by descricao. Carrega `regras` via joinedload para evitar N+1 |
| `get_perfil` | `(db: Session, perfil_id: int) → Optional[PerfilTributario]` | Busca por ID com eager load das regras |
| `criar_perfil` | `(db: Session, empresa_id: int, data: PerfilTributarioCreate) → PerfilTributario` | Cria perfil e regras em uma única transação |
| `atualizar_perfil` | `(db: Session, perfil_id: int, data: PerfilTributarioUpdate) → PerfilTributario` | Atualiza descrição e faz replace-all das regras (deleta todas, recria) |
| `deletar_perfil` | `(db: Session, perfil_id: int) → None` | Deleta o perfil (cascade remove as regras) |
| `perfil_em_uso` | `(db: Session, perfil_id: int) → bool` | Verifica se algum `ProdutoFiscal` referencia este perfil (guard de deleção — usado a partir da SPEC 3) |

### 4.2. Detalhe do `atualizar_perfil` (replace-all)

```python
def atualizar_perfil(db: Session, perfil_id: int, data: PerfilTributarioUpdate) -> PerfilTributario:
    perfil = get_perfil(db, perfil_id)
    if not perfil:
        raise  # 404

    perfil.descricao = data.descricao

    # Replace-all: o cascade="all, delete-orphan" cuida da limpeza
    perfil.regras.clear()
    for regra_data in data.regras:
        perfil.regras.append(RegraPerfilTributario(
            perfil_id=perfil.id,
            **regra_data.model_dump(),
        ))

    db.flush()
    return perfil
```

**Por que replace-all e não diff?**

- É o padrão do sistema: o update de regras NCM em [`tributacao.py`](file:///c:/dev/bigpdv/backend-fastapi/app/db/crud/tributacao.py) faz upsert, mas regras NCM são 1:1 por NCM. Regras de perfil são N:M dentro do perfil — diff exigiria reconciliação de IDs do frontend, um ponto de falha desnecessário.
- A tabela é pequena (tipicamente 5-30 regras por perfil). O custo do replace é desprezível.
- A transação garante atomicidade: se qualquer regra falhar, nada muda.

---

## 5. Detalhamento: Endpoints REST

Todos os endpoints ficam em [`app/api/v1/endpoints/fiscal.py`](file:///c:/dev/bigpdv/backend-fastapi/app/api/v1/endpoints/fiscal.py), agrupados em uma nova seção `PERFIS TRIBUTÁRIOS`.

### 5.1. `GET /fiscal/perfis-tributarios`

| Aspecto | Detalhe |
|---------|---------|
| **Permissão** | `requer_configuracao_fiscal` |
| **Response** | `list[PerfilTributarioListItem]` |
| **Descrição** | Lista todos os perfis da empresa do usuário |
| **Query params** | Nenhum (a lista de perfis por empresa é curta — tipicamente 2-5) |

Comportamento:
- Filtra por `empresa_id` do token do usuário
- Retorna lista enxuta (sem carregar regras — só contagem)
- Ordenado por `descricao` ASC

### 5.2. `POST /fiscal/perfis-tributarios`

| Aspecto | Detalhe |
|---------|---------|
| **Permissão** | `requer_configuracao_fiscal` |
| **Request body** | `PerfilTributarioCreate` |
| **Response** | `PerfilTributarioRead` (201 Created) |
| **Descrição** | Cria perfil com suas regras em bloco |

Comportamento:
- Valida schema (fallback obrigatório, sem duplicata, UFs válidas, NCMs 8 dígitos)
- Cria perfil e regras na mesma transação
- Retorna o perfil criado com IDs preenchidos

Erros:
- `422` — validação do schema falhou (mensagem detalhada de qual regra está errada)

### 5.3. `GET /fiscal/perfis-tributarios/{perfil_id}`

| Aspecto | Detalhe |
|---------|---------|
| **Permissão** | `requer_configuracao_fiscal` |
| **Path param** | `perfil_id: int` (ge=1) |
| **Response** | `PerfilTributarioRead` |
| **Descrição** | Retorna perfil completo com todas as regras |

Erros:
- `404` — perfil não encontrado

### 5.4. `PUT /fiscal/perfis-tributarios/{perfil_id}`

| Aspecto | Detalhe |
|---------|---------|
| **Permissão** | `requer_configuracao_fiscal` |
| **Path param** | `perfil_id: int` (ge=1) |
| **Request body** | `PerfilTributarioUpdate` |
| **Response** | `PerfilTributarioRead` |
| **Descrição** | Atualiza descrição e faz replace-all das regras |

Comportamento:
- Mesmas validações do POST
- Replace-all das regras (dentro de transação)
- Retorna perfil atualizado

Erros:
- `404` — perfil não encontrado
- `422` — validação do schema

### 5.5. `DELETE /fiscal/perfis-tributarios/{perfil_id}`

| Aspecto | Detalhe |
|---------|---------|
| **Permissão** | `requer_configuracao_fiscal` |
| **Path param** | `perfil_id: int` (ge=1) |
| **Response** | `204 No Content` |
| **Descrição** | Deleta perfil e suas regras (cascade) |

Comportamento:
- Verifica se o perfil está em uso por algum produto (`perfil_em_uso()`)
- Se estiver em uso: retorna erro com lista de produtos que o referenciam
- Se não estiver: deleta (cascade remove as regras)

Erros:
- `404` — perfil não encontrado
- `409 Conflict` — perfil está vinculado a produtos (mensagem lista os nomes dos produtos)

> [!NOTE]
> O guard `perfil_em_uso` depende da FK `produto_fiscal.perfil_tributario_id` que será criada na SPEC 3. Até lá, o guard retorna `False` sempre (nenhum produto referencia perfis). Implementar o guard agora com essa lógica "futura" evita ter que reabrir este endpoint depois.

---

## 6. Detalhamento: Frontend

### 6.1. Rota

Adicionar rota no módulo fiscal, acessível pela tela de configurações:

```
/fiscal/configuracoes/perfis-tributarios
```

### 6.2. `PerfisTributariosView.vue`

**Arquivo**: `frontend/src/modules/fiscal/views/PerfisTributariosView.vue`

Tela de listagem com DataTable mostrando:

| Coluna | Conteúdo |
|--------|----------|
| Descrição | Nome do perfil |
| Regras | Quantidade de regras (badge numérico) |
| Atualização | Data da última modificação (formato relativo: "há 2 dias") |
| Ações | Botões Editar / Excluir |

Funcionalidades:
- Botão "+ Novo Perfil" abre o formulário de criação
- Clicar em Editar abre o formulário preenchido
- Clicar em Excluir mostra confirmação; se perfil em uso, mostra a mensagem de erro da API
- Query composable: `usePerfisTributariosQuery()` (TanStack Query / VueQuery)

### 6.3. `PerfilTributarioForm.vue`

**Arquivo**: `frontend/src/modules/fiscal/components/configuracoes/PerfilTributarioForm.vue`

Modal ou drawer com formulário de perfil e tabela dinâmica de regras.

#### Cabeçalho

| Campo | Componente | Validação |
|-------|-----------|-----------|
| Descrição | `<input type="text">` | Mín 3 caracteres |

#### Tabela de regras

Tabela editável onde cada linha é uma regra:

| Coluna | Componente | Comportamento |
|--------|-----------|---------------|
| **UF Destino** | `<select>` com as 27 UFs + opção "Todos (Fallback)" | "Todos" envia `null` |
| **NCM (Exceção)** | `<input>` com máscara 8 dígitos | Opcional. Vazio envia `null` |
| **Alíq. Interestadual** | `<input type="number">` com step 0.01 | Exibe em % (12,00), envia em centésimos (1200) |
| **Alíq. Interna Destino** | `<input type="number">` com step 0.01 | Exibe em %, envia centésimos |
| **FCP** | `<input type="number">` com step 0.01 | Exibe em %, envia centésimos. Default: 0 |
| **Base Dupla** | `<switch>` / `<checkbox>` | Default: off |
| **MVA (ST)** | `<input type="number">` com step 0.01 | Opcional. Se preenchido, indica que há ST |
| **Red. Base** | `<input type="number">` com step 0.01 | Opcional. Só aparece se MVA preenchido |
| **Ações** | Botão 🗑️ Remover | Não permite remover a linha fallback |

#### Comportamentos da tabela

1. **Linha fallback fixa**: A primeira linha (UF = "Todos", NCM = vazio) não pode ser removida. Os campos UF e NCM ficam desabilitados nessa linha com label "Fallback — aplica-se quando não houver regra específica".

2. **Botão "+ Adicionar Regra"**: Adiciona uma nova linha vazia ao array reativo. A nova linha começa com UF vazia e NCM vazio — o usuário deve preencher ao menos a UF.

3. **Validação client-side antes de submeter**:
   - Exatamente uma regra fallback
   - Sem duplicata de `(UF, NCM)`
   - Alíquota interestadual e interna preenchidas em todas as linhas
   - Se UF preenchida, verificar que é UF válida
   - Se NCM preenchido, verificar 8 dígitos

4. **Conversão centavos ↔ percentual**: O usuário digita `18.00` (visual) e o payload envia `1800` (centésimos). A conversão é feita no momento do submit e na carga do formulário. Esse padrão já existe nos demais formulários fiscais do sistema.

5. **Estado reativo**: O array de regras é um `ref<RegraPerfilTributarioBase[]>` gerenciado via `v-model` na tabela.

#### Mutation composable

`usePerfilTributarioMutation()` — encapsula POST (criar) e PUT (atualizar), invalidando a query de listagem no sucesso.

---

## 7. Critérios de Aceite

### CA-1: Schemas validam corretamente
- [ ] `PerfilTributarioCreate` rejeita payload sem regras (`min_length=1`)
- [ ] `PerfilTributarioCreate` rejeita payload sem regra fallback (UF=null, NCM=null)
- [ ] `PerfilTributarioCreate` rejeita payload com 2+ regras fallback
- [ ] `PerfilTributarioCreate` rejeita payload com regras duplicadas (mesma UF + NCM)
- [ ] `RegraPerfilTributarioBase` rejeita UF com 3+ caracteres
- [ ] `RegraPerfilTributarioBase` rejeita UF inválida (ex: "XX")
- [ ] `RegraPerfilTributarioBase` rejeita NCM com menos ou mais de 8 dígitos
- [ ] `RegraPerfilTributarioBase` rejeita NCM com letras
- [ ] Alíquotas aceitam zero (é caso legítimo)
- [ ] Campos `mva_st` e `reducao_base_calculo` aceitam `null`

### CA-2: CRUD funciona end-to-end
- [ ] `POST /fiscal/perfis-tributarios` cria perfil com regras e retorna 201 com IDs
- [ ] `GET /fiscal/perfis-tributarios` retorna lista de perfis da empresa (sem regras, com contagem)
- [ ] `GET /fiscal/perfis-tributarios/{id}` retorna perfil com todas as regras
- [ ] `PUT /fiscal/perfis-tributarios/{id}` atualiza descrição e faz replace-all das regras
- [ ] `DELETE /fiscal/perfis-tributarios/{id}` deleta perfil e regras em cascade (204)
- [ ] `DELETE` retorna 409 se perfil em uso (após SPEC 3 estar implementada)
- [ ] `GET/PUT/DELETE` retornam 404 para ID inexistente

### CA-3: Permissões corretas
- [ ] Todos os endpoints exigem autenticação (`get_current_active_user` ou `requer_configuracao_fiscal`)
- [ ] Endpoints filtram por `empresa_id` do token — não é possível acessar perfil de outra empresa
- [ ] Endpoints estão protegidos pelo `requer_modulo("NFE")` do router

### CA-4: Frontend funcional
- [ ] Tela de listagem mostra perfis com descrição, contagem de regras e data
- [ ] Botão "Novo Perfil" abre formulário com linha fallback pré-criada
- [ ] Formulário permite adicionar e remover regras dinamicamente
- [ ] Linha fallback não pode ser removida
- [ ] Validação client-side impede submit com dados inválidos
- [ ] Conversão `percentual ↔ centésimos` funciona nos dois sentidos
- [ ] Edição carrega perfil existente com regras preenchidas
- [ ] Exclusão pede confirmação e mostra erro se perfil em uso

### CA-5: Zero impacto no sistema existente
- [ ] Nenhum endpoint existente foi alterado
- [ ] A emissão de NF-e/NFC-e continua funcionando sem mudanças
- [ ] Todos os testes existentes passam
- [ ] O tax engine não é tocado
- [ ] O payload builder não é tocado


---

## Desvios aplicados (2026-09-18) — backend
Ver `docs/done/fiscal/TASK005.md`. Destaques: serviço entre endpoint e CRUD (rule backend-layer § 1); GET para usuário ativo, escrita master; `get_perfil` escopado por empresa; **§ 4.2 tinha bug** — `clear()`+`append` colide na UNIQUE ao reenviar a mesma UF (INSERT antes do DELETE); corrigido com `flush` intermediário. CA-4 (frontend) fica para a rodada de interface. 47 testes novos, gate 956 passed.
