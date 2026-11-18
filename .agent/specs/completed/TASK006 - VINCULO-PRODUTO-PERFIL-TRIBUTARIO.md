# SPEC 3 — Vínculo ProdutoFiscal → PerfilTributário

## 1. Objetivo

Permitir que um produto aponte para um perfil tributário via FK, e criar a função de resolução (match) que, dado um perfil, uma UF de destino e um NCM, devolve a regra aplicável com a prioridade correta.

Ao final desta spec, o lojista poderá associar um perfil tributário a qualquer produto no cadastro. A função de match estará pronta para ser consumida pelo motor de cálculo (SPEC 4), mas **nenhum cálculo novo é ativado ainda**. A emissão de NF-e continua funcionando exatamente como antes.

---

## 2. Contexto: O elo que faltava

### 2.1. De um lado, o perfil (SPEC 1 e 2)

As SPECs 1 e 2 criaram a infraestrutura de perfis — tabelas, CRUD, endpoints, tela. Mas até aqui os perfis existem de forma isolada: nenhum produto os referencia, e nenhum cálculo os consulta.

### 2.2. Do outro lado, o produto

O [`ProdutoFiscal`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/produto_fiscal.py) hoje carrega dados de operação interna: NCM, CFOP, CST/CSOSN, alíquota ICMS interna, PIS/COFINS. Esses campos são resolvidos pela cascata existente em [`tributacao.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tributacao.py):

```
produto.fiscal → regra por NCM → tributação padrão da loja
```

### 2.3. O que esta spec conecta

O perfil tributário traz dados **interestaduais** que a cascata não cobre. A conexão é uma FK simples:

```
ProdutoFiscal.perfil_tributario_id → PerfilTributario.id
```

Quando o motor fiscal (SPEC 4+) detectar uma operação interestadual, ele fará:
1. Ler o `perfil_tributario_id` do produto
2. Chamar `resolver_regra_perfil(perfil_id, uf_destino, ncm)` — a função criada **nesta spec**
3. Obter alíquotas interestadual, interna do destino, FCP, MVA

### 2.4. Coexistência: a cascata e o perfil vivem juntos

> [!IMPORTANT]
> O perfil **não substitui** a cascata existente. Os dois sistemas respondem perguntas diferentes e coexistem no mesmo produto:

| Pergunta | Quem responde | Quando |
|----------|--------------|--------|
| Qual o CST/CSOSN deste produto? | Cascata (`tributacao.py`) | Sempre |
| Qual o CFOP de saída? | Cascata + derivação (`cfop.py`) | Sempre |
| Qual a alíquota ICMS interna? | Cascata → AliquotaUF | Operação interna |
| Qual o PIS/COFINS? | Cascata → regime apuração | Sempre |
| Qual a alíquota interestadual? | **Perfil Tributário** | Operação interestadual |
| Qual a alíquota interna do destino? | **Perfil Tributário** | Operação interestadual |
| Qual o FCP do destino? | **Perfil Tributário** | Operação interestadual |
| Tem ST? Qual o MVA? | **Perfil Tributário** | Contribuinte interestadual |

Um produto **sem perfil** continua emitindo normalmente para operações internas — exatamente como hoje. A trava interestadual do [`resolver.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/resolver.py#L130-L139) continua ativa nesta spec; será removida somente na SPEC 4.

---

## 3. Detalhamento: Alteração no Model `ProdutoFiscal`

**Arquivo**: [`app/db/models/produto_fiscal.py`](file:///c:/dev/bigpdv/backend-fastapi/app/db/models/produto_fiscal.py)

### 3.1. Nova coluna

| Campo | Tipo SQLAlchemy | Tipo Python | Nullable | Constraint | Descrição |
|-------|----------------|-------------|----------|------------|-----------|
| `perfil_tributario_id` | `Integer` | `Mapped[Optional[int]]` | **Sim** | FK → `perfil_tributario.id`, ondelete SET NULL | Perfil tributário vinculado. NULL = produto sem perfil interestadual |

### 3.2. Novo relacionamento

| Relacionamento | Tipo | Target | Descrição |
|----------------|------|--------|-----------|
| `perfil_tributario` | Many-to-One | `PerfilTributario` | O perfil tributário associado, carregado por lazy load |

### 3.3. Posição no arquivo

A coluna deve ser adicionada na seção de campos fiscais, após os campos de reforma tributária e antes dos metadados. Posição sugerida — após a linha 139 (`c_benef`), antes de `data_atualizacao`:

```python
# --- Perfil Tributário (DIFAL/ST interestadual) ---

perfil_tributario_id: Mapped[Optional[int]] = mapped_column(
    Integer,
    ForeignKey("perfil_tributario.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
    doc="Perfil tributário para operações interestaduais (DIFAL/ST). "
        "NULL = produto sem configuração interestadual."
)

perfil_tributario: Mapped[Optional["PerfilTributario"]] = relationship(
    "PerfilTributario",
    doc="Perfil tributário vinculado ao produto"
)
```

### 3.4. Por que `ondelete=SET NULL` e não `CASCADE`?

Se o lojista deletar um perfil, os produtos que o usavam **não devem ser apagados** — eles continuam existindo, apenas perdem a configuração interestadual. `SET NULL` é o comportamento correto: o produto volta ao estado "sem perfil", e a próxima emissão interestadual será bloqueada pela trava do resolver (comportamento seguro).

Isso também alinha com o guard de deleção da SPEC 2: o `DELETE /perfis-tributarios/{id}` retorna 409 se houver produtos vinculados. Se o guard for ignorado (ex: deleção direta no banco), `SET NULL` garante que nada quebra.

---

## 4. Detalhamento: Alteração nos Schemas do Produto

**Arquivo**: [`app/schemas/produto_fiscal.py`](file:///c:/dev/bigpdv/backend-fastapi/app/schemas/produto_fiscal.py)

### 4.1. `ProdutoFiscalUpdate`

Adicionar campo opcional:

```python
perfil_tributario_id: Optional[int] = None
```

Comportamento: se enviado como `null` no JSON, desvincula o produto do perfil. Se omitido, não altera o vínculo existente. Este é o mesmo padrão que os demais campos opcionais do schema já seguem.

### 4.2. `ProdutoFiscalRead` (se existir schema de leitura)

Adicionar o campo para que o frontend saiba qual perfil está vinculado:

```python
perfil_tributario_id: Optional[int] = None
```

Opcionalmente, incluir um campo derivado com o nome do perfil para exibição na tela sem precisar de lookup extra:

```python
perfil_tributario_descricao: Optional[str] = None
```

---

## 5. Detalhamento: Função de Match (`resolver_regra_perfil`)

**Arquivo sugerido**: `app/services/fiscal/tax_engine/perfil_resolver.py`

Esta é a inteligência central do PerfilTributário — a função que, dado um perfil, uma UF e um NCM, devolve a regra mais específica aplicável.

### 5.1. Assinatura

```python
def resolver_regra_perfil(
    db: Session,
    perfil_id: int,
    uf_destino: str,
    ncm_produto: Optional[str] = None,
) -> Optional[RegraPerfilTributario]:
```

### 5.2. Algoritmo de match

A resolução segue **prioridade por especificidade decrescente**. As três camadas:

```
Prioridade 1 (mais específica):  UF = "SP"  AND  NCM = "85171200"
Prioridade 2 (estado genérico):  UF = "SP"  AND  NCM = NULL
Prioridade 3 (fallback geral):   UF = NULL  AND  NCM = NULL
```

### 5.3. Implementação recomendada: query única com ordenação

```python
from sqlalchemy import case, desc

def resolver_regra_perfil(
    db: Session,
    perfil_id: int,
    uf_destino: str,
    ncm_produto: Optional[str] = None,
) -> Optional[RegraPerfilTributario]:
    """
    Encontra a regra mais específica do perfil para a operação.

    Prioridade:
        1. UF igual AND NCM igual (exceção específica)
        2. UF igual AND NCM null  (regra do estado)
        3. UF null  AND NCM null  (fallback geral)

    Regras com UF null + NCM preenchido são ignoradas de propósito:
    NCM sem UF não tem significado operacional — a alíquota interestadual
    depende SEMPRE do par origem/destino, nunca só do produto.

    Returns:
        A regra aplicável, ou None se o perfil não existir ou não tiver
        regra que case. None aqui é sinal de que o produto não tem
        configuração interestadual para este destino.
    """
    uf = uf_destino.strip().upper()

    query = (
        db.query(RegraPerfilTributario)
        .filter(RegraPerfilTributario.perfil_id == perfil_id)
        .filter(
            or_(
                # Prioridade 1: UF + NCM exatos
                and_(
                    RegraPerfilTributario.uf_destino == uf,
                    RegraPerfilTributario.ncm_excecao == ncm_produto,
                ),
                # Prioridade 2: UF exata, NCM genérico
                and_(
                    RegraPerfilTributario.uf_destino == uf,
                    RegraPerfilTributario.ncm_excecao.is_(None),
                ),
                # Prioridade 3: Fallback geral
                and_(
                    RegraPerfilTributario.uf_destino.is_(None),
                    RegraPerfilTributario.ncm_excecao.is_(None),
                ),
            )
        )
        .order_by(
            # Mais específico primeiro: UF preenchida > UF null
            desc(case(
                (RegraPerfilTributario.uf_destino.isnot(None), 1),
                else_=0,
            )),
            # Dentro da mesma UF: NCM preenchido > NCM null
            desc(case(
                (RegraPerfilTributario.ncm_excecao.isnot(None), 1),
                else_=0,
            )),
        )
        .first()
    )

    return query
```

### 5.4. Por que uma query única e não 3 queries sequenciais?

A abordagem "tenta UF+NCM, se não achou tenta UF, se não achou tenta fallback" faria 1 a 3 roundtrips ao banco. Com SQLite local isso é rápido, mas a query única é:
- **Mais simples de manter** — um único ponto de lógica
- **Correta por construção** — a ordenação garante a prioridade sem `if/elif`
- **O mesmo padrão do pseudo-código da spec original** — reconhecível para quem escreveu a spec

### 5.5. Caso: NCM null no produto

Se o produto não tem NCM preenchido, `ncm_produto` chega como `None`. A prioridade 1 (UF+NCM) não casa com nenhuma regra que tenha NCM preenchido (porque `None != "85171200"`). A resolução cai para prioridade 2 (UF genérica) ou 3 (fallback) — que é o comportamento correto.

### 5.6. Caso: Perfil sem regra para a UF

Se o perfil não tem regra para a UF de destino, a resolução cai no fallback geral. Se o fallback existir (obrigatório pela validação da SPEC 2), o produto sempre tem uma resposta. Se o fallback não existir (dados inconsistentes), retorna `None` e o chamador (SPEC 4) deve tratar como "sem configuração interestadual".

---

## 6. Detalhamento: Atualização do guard de deleção (SPEC 2)

Com a FK `perfil_tributario_id` agora existindo em `ProdutoFiscal`, a função `perfil_em_uso` da SPEC 2 pode ser implementada corretamente:

```python
def perfil_em_uso(db: Session, perfil_id: int) -> bool:
    return db.query(
        db.query(ProdutoFiscal)
        .filter(ProdutoFiscal.perfil_tributario_id == perfil_id)
        .exists()
    ).scalar()
```

Se a SPEC 2 foi implementada antes com `return False`, agora ela ganha a implementação real.

---

## 7. Detalhamento: Frontend — Select de Perfil no Cadastro de Produto

### 7.1. Localização

No formulário de edição de produto, **aba Fiscal** (já existente). O select de perfil tributário é adicionado como um novo campo, **sem remover** nenhum campo existente.

### 7.2. Componente

```html
<label>Perfil Tributário (Interestadual)</label>
<select v-model="form.perfil_tributario_id">
  <option :value="null">Nenhum — apenas operações internas</option>
  <option 
    v-for="perfil in perfis" 
    :key="perfil.id" 
    :value="perfil.id"
  >
    {{ perfil.descricao }}
  </option>
</select>
<small class="hint">
  Define as alíquotas de DIFAL e ST para vendas interestaduais.
  Sem perfil, operações interestaduais serão bloqueadas.
</small>
```

### 7.3. Dados

- Usar o composable `usePerfisTributariosQuery()` criado na SPEC 2 para popular a lista
- O `perfil_tributario_id` é enviado no payload de update do produto junto com os demais campos fiscais
- Se o usuário selecionar "Nenhum", o valor `null` é enviado e o backend desvincula o perfil

### 7.4. Posicionamento visual

O select deve ficar **no topo da aba fiscal**, antes dos campos de NCM/CFOP/CST, com um leve destaque visual (borda ou background sutil) para indicar que é uma configuração de nível superior. A hint explica que ele afeta vendas interestaduais.

### 7.5. O que NÃO fazer

- **Não remover** campos existentes (alíquota ICMS, CST, CSOSN, CFOP, PIS/COFINS). Eles continuam sendo usados para operações internas via cascata.
- **Não condicionar** a exibição dos campos existentes à presença de perfil. Todos os campos coexistem.
- **Não duplicar** campos do perfil no cadastro de produto — as alíquotas interestaduais vivem só no perfil.

---

## 8. Detalhamento: Migration Alembic

### 8.1. Operação `upgrade()`

Adicionar coluna `perfil_tributario_id` à tabela `produto_fiscal`:

```python
op.add_column(
    "produto_fiscal",
    sa.Column(
        "perfil_tributario_id",
        sa.Integer(),
        sa.ForeignKey("perfil_tributario.id", ondelete="SET NULL"),
        nullable=True,
    ),
)
op.create_index(
    "ix_produto_fiscal_perfil_tributario_id",
    "produto_fiscal",
    ["perfil_tributario_id"],
)
```

### 8.2. Operação `downgrade()`

```python
op.drop_index("ix_produto_fiscal_perfil_tributario_id", table_name="produto_fiscal")
op.drop_column("produto_fiscal", "perfil_tributario_id")
```

### 8.3. Dependência de migration

Esta migration depende da migration da SPEC 1 (que cria a tabela `perfil_tributario`). O hash de dependência do Alembic (`down_revision`) deve apontar para ela.

---

## 9. Critérios de Aceite

### CA-1: FK e model atualizados
- [ ] `ProdutoFiscal` possui campo `perfil_tributario_id` (Integer, nullable, FK → perfil_tributario.id)
- [ ] FK usa `ondelete="SET NULL"`
- [ ] Relationship `perfil_tributario` carrega o perfil por lazy load
- [ ] Index criado na coluna `perfil_tributario_id`
- [ ] Migration aplica sem erro e downgrade reverte corretamente

### CA-2: Schema de produto atualizado
- [ ] `ProdutoFiscalUpdate` aceita `perfil_tributario_id` (Optional[int])
- [ ] Enviar `null` no JSON desvincula o produto do perfil
- [ ] Omitir o campo no JSON não altera o vínculo existente
- [ ] Schema de leitura inclui `perfil_tributario_id`

### CA-3: Função de match funciona corretamente
- [ ] `resolver_regra_perfil(perfil_id, "SP", "85171200")` retorna regra UF=SP + NCM=85171200 se existir
- [ ] `resolver_regra_perfil(perfil_id, "SP", "85171200")` retorna regra UF=SP + NCM=null se não existir regra específica por NCM
- [ ] `resolver_regra_perfil(perfil_id, "SP", "85171200")` retorna regra fallback (UF=null, NCM=null) se não existir regra para SP
- [ ] `resolver_regra_perfil(perfil_id, "AM", None)` retorna regra UF=AM se existir, senão fallback
- [ ] `resolver_regra_perfil(999, "SP", None)` retorna `None` para perfil inexistente
- [ ] A função executa uma única query SQL (não N queries sequenciais)

### CA-4: Guard de deleção funcional
- [ ] `perfil_em_uso(perfil_id)` retorna `True` quando ao menos um produto referencia o perfil
- [ ] `perfil_em_uso(perfil_id)` retorna `False` quando nenhum produto o referencia
- [ ] `DELETE /perfis-tributarios/{id}` retorna 409 quando perfil está em uso
- [ ] Deletar perfil sem produtos vinculados seta `perfil_tributario_id = NULL` em nenhum produto (porque não há vínculo)

### CA-5: Frontend integrado
- [ ] Aba fiscal do cadastro de produto exibe select de perfil tributário
- [ ] Select mostra opção "Nenhum" + lista de perfis da empresa
- [ ] Selecionar um perfil e salvar persiste o `perfil_tributario_id`
- [ ] Selecionar "Nenhum" e salvar desvincula (seta null)
- [ ] Campos fiscais existentes (NCM, CFOP, CST, alíquotas) continuam visíveis e funcionais

### CA-6: Zero impacto na emissão
- [ ] A trava interestadual do `resolver.py` continua ativa — `OperacaoInterestadualError` é levantada normalmente
- [ ] Emissão de NF-e para operação interna não consulta perfil tributário
- [ ] A cascata tributária existente (`tributacao.py`) não é alterada
- [ ] Todos os testes existentes passam


---

## Desvios aplicados (2026-09-18) — backend
Ver `docs/done/fiscal/TASK006.md`. Destaques: `crud.produto_fiscal.upsert` preservando o unset (CA-2 dependia disso e havia bug pré-existente); migration com `ADD COLUMN … REFERENCES` cru (§ 8.1 não roda no SQLite); 422 para perfil de outra empresa; `perfil_tributario_id` no `FiscalEfetivo` por exigência do teste de contrato (sem cascata). CA-5 (frontend) fica para a rodada de interface. 27 testes novos, gate 982 passed.
