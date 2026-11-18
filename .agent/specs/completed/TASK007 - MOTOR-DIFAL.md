# SPEC 4 — Motor de Cálculo DIFAL (Não Contribuinte)

## 1. Objetivo

Implementar o cálculo do Diferencial de Alíquota (DIFAL) e do Fundo de Combate à Pobreza (FCP) para vendas interestaduais a consumidores finais não contribuintes de ICMS. Isso inclui criar a calculadora, expandir os DTOs do tax engine, alterar o resolver para consultar o perfil tributário, e remover a trava interestadual **apenas para o cenário de não contribuinte com perfil configurado**.

Ao final desta spec, o motor fiscal será capaz de calcular DIFAL/FCP corretamente. Porém, o payload XML ainda **não será alterado** — os novos valores ficarão no `ResultadoCalculo` prontos para a SPEC 6 consumir.

---

## 2. Contexto: O que é DIFAL e por que é complexo

### 2.1. Fundamento legal

A EC 87/2015 determinou que, nas vendas interestaduais a **consumidor final não contribuinte** (indIEDest = 9), o ICMS é partilhado entre a UF de origem e a UF de destino. Desde 2019, 100% do diferencial vai para o destino.

O cálculo envolve:
- **ICMS próprio (origem)**: calculado pela alíquota interestadual (7% ou 12%, definida pela CF/88 conforme as UFs)
- **DIFAL (destino)**: diferença entre a alíquota interna do destino e a interestadual
- **FCP**: percentual adicional cobrado por alguns estados (0% a 4%)

### 2.2. As duas fórmulas de DIFAL

Existem **duas fórmulas** de cálculo, e qual usar depende da regulamentação do estado de destino:

**Fórmula simples (maioria dos estados)**:
```
Base = Valor do Produto (+ Frete + Seguro + Desp. - Desconto)
DIFAL = Base × (Alíq. Interna Destino − Alíq. Interestadual)
FCP   = Base × % FCP
```

**Fórmula base dupla (EC 87/2015, exigida por alguns estados como AL, BA, CE, MA, PA, PE, PI)**:
```
Base_dupla = Base / (1 − Alíq. Interna Destino / 100)
DIFAL = (Base_dupla × Alíq. Interna Destino) − (Base × Alíq. Interestadual)
FCP   = Base_dupla × % FCP
```

A diferença é que a base dupla "por dentro" inclui o próprio imposto na base de cálculo — o mesmo princípio do ICMS normal brasileiro. A flag `calculo_base_dupla` no `RegraPerfilTributario` (SPEC 1) controla qual fórmula usar.

### 2.3. O que muda no tax engine hoje

O [`tax_engine`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/engine.py) é um pipeline puro:

```
rateio → calcular_icms → calcular_pis_cofins → consolidar_totais
```

O DIFAL é um cálculo **paralelo** ao ICMS próprio — não o substitui. O ICMS próprio continua sendo calculado pela alíquota interestadual; o DIFAL é a diferença que vai para o destino. O pipeline se torna:

```
rateio → calcular_icms → calcular_difal (novo) → calcular_pis_cofins → consolidar_totais
```

### 2.4. A trava que será removida (parcialmente)

Hoje o [`resolver.py:130-139`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/resolver.py#L130-L139) levanta `OperacaoInterestadualError` para **toda** operação interestadual não presencial. Esta spec remove a trava **apenas quando**:

1. O cliente é **não contribuinte** (PF, ou PJ sem IE)
2. **Todos** os produtos da venda possuem perfil tributário com regra aplicável para a UF de destino

Se qualquer produto não tiver perfil, ou se o cliente for contribuinte (cenário de ST — SPEC 5), a trava continua ativa.

---

## 3. Detalhamento: Nova calculadora `difal.py`

**Arquivo**: `app/services/fiscal/tax_engine/calculators/difal.py`

### 3.1. Dataclass de resultado

```python
@dataclass
class ResultadoDIFAL:
    """Resultado do cálculo DIFAL/FCP para um item."""

    # Base usada no cálculo (pode ser simples ou dupla)
    base_calculo: Decimal

    # DIFAL
    aliquota_interna_destino: Decimal   # ex: Decimal("18.00")
    aliquota_interestadual: Decimal     # ex: Decimal("12.00")
    valor_difal: Decimal                # ICMS devido ao destino

    # FCP
    fcp_base_calculo: Decimal           # mesma base ou base dupla
    fcp_aliquota: Decimal               # ex: Decimal("2.00")
    fcp_valor: Decimal                  # valor do FCP

    # ICMS da operação interestadual (remetente)
    icms_interestadual_valor: Decimal   # ICMS próprio pela alíq. interestadual
```

### 3.2. Função de cálculo

```python
def calcular_difal(
    base_icms: Decimal,
    aliquota_interestadual: Decimal,
    aliquota_interna_destino: Decimal,
    percentual_fcp: Decimal = Decimal("0"),
    base_dupla: bool = False,
) -> ResultadoDIFAL:
```

### 3.3. Lógica interna

```python
CEM = Decimal("100")

# ICMS próprio (remetente) — sempre pela alíquota interestadual
icms_inter = (base_icms * aliquota_interestadual / CEM).quantize(PRECISAO, ROUND_MODE)

if base_dupla:
    # Base dupla: inclui o imposto na própria base (ICMS "por dentro")
    fator = CEM - aliquota_interna_destino
    if fator <= 0:
        raise ValueError("Alíquota interna do destino >= 100% — cálculo impossível.")
    base_difal = (base_icms * CEM / fator).quantize(PRECISAO, ROUND_MODE)
    icms_destino = (base_difal * aliquota_interna_destino / CEM).quantize(PRECISAO, ROUND_MODE)
    difal = (icms_destino - icms_inter).quantize(PRECISAO, ROUND_MODE)
    fcp_base = base_difal
else:
    # Base simples: diferença direta de alíquotas
    base_difal = base_icms
    difal = (base_icms * (aliquota_interna_destino - aliquota_interestadual) / CEM).quantize(PRECISAO, ROUND_MODE)
    fcp_base = base_icms

# FCP — sempre sobre a base (simples ou dupla, conforme o caso)
fcp = (fcp_base * percentual_fcp / CEM).quantize(PRECISAO, ROUND_MODE)

# DIFAL nunca negativo (se alíquota interestadual > interna, não há diferencial)
if difal < Decimal("0"):
    difal = Decimal("0")

return ResultadoDIFAL(
    base_calculo=base_difal,
    aliquota_interna_destino=aliquota_interna_destino,
    aliquota_interestadual=aliquota_interestadual,
    valor_difal=difal,
    fcp_base_calculo=fcp_base,
    fcp_aliquota=percentual_fcp,
    fcp_valor=fcp,
    icms_interestadual_valor=icms_inter,
)
```

### 3.4. Propriedades da função

- **Pura**: sem efeitos colaterais, sem DB, sem HTTP — segue o padrão dos demais calculators
- **Precisão**: usa `PRECISAO` e `ROUND_MODE` das constantes do engine (mesmo arredondamento do ICMS)
- **DIFAL nunca negativo**: se a alíquota interestadual for maior que a interna do destino (caso raro, mas possível em ZFM), o DIFAL é zero — não há "crédito reverso"
- **Base dupla protegida**: rejeita alíquota ≥ 100% para evitar divisão por zero

---

## 4. Detalhamento: Expansão dos DTOs (`types.py`)

**Arquivo**: [`app/services/fiscal/tax_engine/types.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/types.py)

### 4.1. `ItemEntrada` — novos campos opcionais

Adicionar após os campos de PIS/COFINS (linha 44):

```python
# --- DIFAL / Operação interestadual (preenchido pelo resolver) ---
# Campos opcionais: None = operação interna (sem DIFAL).
# Quando preenchidos, o engine chama calcular_difal() após o ICMS.

difal_aliquota_interestadual: Optional[Decimal] = None
difal_aliquota_interna_destino: Optional[Decimal] = None
difal_percentual_fcp: Decimal = Decimal("0")
difal_base_dupla: bool = False
```

**Por que opcionais?**

Operações internas (90%+ das vendas) não têm DIFAL. Tornar os campos opcionais com default `None` garante que:
- Nenhum chamador existente precisa ser alterado
- O engine pode verificar `if item.difal_aliquota_interestadual is not None` para decidir se calcula
- A serialização JSON omite campos None, mantendo payloads enxutos

### 4.2. `ImpostosItem` — novos campos de saída

Adicionar após o bloco de CSOSN 101 (linha 89):

```python
# --- DIFAL / ICMSUFDest (operação interestadual a não contribuinte) ---
# None quando operação interna. O payload_builder (SPEC 6) lê estes
# campos para montar o grupo <ICMSUFDest> do XML.

difal_base_calculo: Optional[Decimal] = None
difal_aliquota_interestadual: Optional[Decimal] = None
difal_aliquota_interna_destino: Optional[Decimal] = None
difal_valor: Optional[Decimal] = None          # ICMS devido ao UF destino
difal_valor_remetente: Optional[Decimal] = None # ICMS interestadual (remetente)

fcp_base_calculo: Optional[Decimal] = None
fcp_aliquota: Optional[Decimal] = None
fcp_valor: Optional[Decimal] = None
```

### 4.3. `TotaisNota` — novos totais

Adicionar após `valor_icms` (linha 112):

```python
# Totais interestaduais (DIFAL/FCP)
valor_difal: Decimal = Decimal("0")         # Soma do DIFAL de todos os itens
valor_fcp: Decimal = Decimal("0")           # Soma do FCP de todos os itens
base_calculo_fcp: Decimal = Decimal("0")    # Soma das bases FCP
```

---

## 5. Detalhamento: Alterações no `resolver.py`

**Arquivo**: [`app/services/fiscal/tax_engine/resolver.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/resolver.py)

### 5.1. Nova lógica na trava interestadual (linhas 120-139)

A trava atual:

```python
# ANTES (bloqueio total)
if not _operacao_presencial(venda):
    uf_cliente = _obter_uf_cliente(venda)
    if uf_cliente and uf_cliente.upper() != uf_emitente.upper():
        raise OperacaoInterestadualError(...)
```

Passa a ser:

```python
# DEPOIS (bloqueio condicional)
if not _operacao_presencial(venda):
    uf_cliente = _obter_uf_cliente(venda)
    if uf_cliente and uf_cliente.upper() != uf_emitente.upper():
        uf_destino = uf_cliente.upper()
        
        # Não contribuinte: tenta resolver DIFAL via perfil
        if _cliente_nao_contribuinte(venda):
            # Verificar se TODOS os produtos têm perfil com regra aplicável
            # (feito no loop de itens abaixo — flag levantada aqui)
            interestadual_nao_contribuinte = True
        else:
            # Contribuinte: SPEC 5 vai tratar. Por enquanto, mantém trava.
            raise OperacaoInterestadualError(
                f"Operação interestadual para contribuinte não suportada. "
                f"ICMS-ST não implementado.",
                campo="uf_destinatario",
            )
```

### 5.2. Nova função auxiliar `_cliente_nao_contribuinte`

```python
def _cliente_nao_contribuinte(venda: Venda) -> bool:
    """
    True se o cliente é não contribuinte de ICMS.

    Segue a mesma lógica que o payload builder usa para derivar indIEDest:
    - PF → sempre não contribuinte (indIEDest = 9)
    - PJ sem IE → não contribuinte (indIEDest = 9)
    - PJ com IE → contribuinte (indIEDest = 1)
    - Sem cliente → consumidor final, não contribuinte

    Importa aqui porque o DIFAL (SPEC 4) se aplica a não contribuintes,
    e o ICMS-ST (SPEC 5) a contribuintes. A rota do cálculo depende disso.
    """
    from app.db.models.cliente import ClientePJ

    cliente = venda.cliente
    if cliente is None:
        return True
    if not isinstance(cliente, ClientePJ):
        return True  # PF é sempre não contribuinte
    return not bool(cliente.ie)  # PJ sem IE = não contribuinte
```

### 5.3. Resolução do perfil no loop de itens

Dentro do loop `for idx, item_venda in enumerate(venda.itens, start=1):`, após resolver o fiscal efetivo e antes de montar o `ItemEntrada`, adicionar:

```python
# Resolver dados interestaduais do perfil (DIFAL)
difal_inter = None
difal_interna = None
difal_fcp = ZERO
difal_base_dupla_flag = False

if interestadual_nao_contribuinte and fiscal:
    perfil_id = getattr(fiscal, "perfil_tributario_id", None)
    # Se fiscal é FiscalEfetivo (cascata), o perfil_id vem do produto original
    if perfil_id is None and produto and produto.fiscal:
        perfil_id = produto.fiscal.perfil_tributario_id

    if perfil_id is None:
        raise OperacaoInterestadualError(
            f"Produto '{produto.nome}' (item {idx}) não possui perfil "
            f"tributário configurado. Para vendas interestaduais, todos "
            f"os produtos devem ter um perfil tributário vinculado.",
            campo="perfil_tributario_id",
            item=idx,
        )

    from .perfil_resolver import resolver_regra_perfil
    regra = resolver_regra_perfil(db, perfil_id, uf_destino, fiscal.ncm)

    if regra is None:
        raise OperacaoInterestadualError(
            f"Perfil tributário do produto '{produto.nome}' não possui "
            f"regra aplicável para a UF {uf_destino}.",
            campo="perfil_tributario_id",
            item=idx,
        )

    difal_inter = _centesimos_para_decimal(regra.aliquota_interestadual, ZERO)
    difal_interna = _centesimos_para_decimal(regra.aliquota_interna_destino, ZERO)
    difal_fcp = _centesimos_para_decimal(regra.percentual_fcp, ZERO)
    difal_base_dupla_flag = regra.calculo_base_dupla
```

### 5.4. Preenchimento no `ItemEntrada`

Os novos campos são adicionados na construção do `ItemEntrada`:

```python
itens_entrada.append(ItemEntrada(
    # ... campos existentes ...
    
    # DIFAL (None = operação interna)
    difal_aliquota_interestadual=difal_inter,
    difal_aliquota_interna_destino=difal_interna,
    difal_percentual_fcp=difal_fcp,
    difal_base_dupla=difal_base_dupla_flag,
))
```

### 5.5. Alíquota ICMS em operação interestadual

Quando a operação é interestadual para não contribuinte, o ICMS próprio do item deve ser calculado pela **alíquota interestadual** (não pela alíquota interna da UF do emitente). Isso requer ajustar `aliq_icms` no resolver:

```python
# Se interestadual, o ICMS próprio usa a alíquota interestadual do perfil
if difal_inter is not None:
    aliq_icms = difal_inter
```

Isso garante que o calculador de ICMS existente ([`icms.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/calculators/icms.py)) calcule o ICMS próprio corretamente sem precisar ser alterado.

---

## 6. Detalhamento: Alterações no `engine.py`

**Arquivo**: [`app/services/fiscal/tax_engine/engine.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/engine.py)

### 6.1. Novo passo no pipeline

Após o cálculo do ICMS (linha 76) e antes do PIS/COFINS (linha 79):

```python
# DIFAL (operação interestadual a não contribuinte)
resultado_difal = None
if item.difal_aliquota_interestadual is not None:
    from .calculators.difal import calcular_difal
    resultado_difal = calcular_difal(
        base_icms=icms.base_calculo,
        aliquota_interestadual=item.difal_aliquota_interestadual,
        aliquota_interna_destino=item.difal_aliquota_interna_destino,
        percentual_fcp=item.difal_percentual_fcp,
        base_dupla=item.difal_base_dupla,
    )
```

**Por que usar `icms.base_calculo` como base do DIFAL?**

A base do DIFAL é a **mesma** base do ICMS próprio: valor do produto + frete + seguro + despesas − desconto. Reutilizar o valor que o calculador de ICMS já computou evita recalcular e garante consistência. Se o ICMS tem redução de base (CST 20), a base do DIFAL usa a base **sem redução** — a redução é benefício do estado de origem, não afeta o DIFAL do destino.

> [!IMPORTANT]
> **Exceção CST 20**: quando o ICMS próprio usa redução de base, a base do DIFAL deve ser a base **original** (antes da redução). O `icms.base_calculo` já é a base reduzida. Nesse caso, recalcular a base original a partir do rateio:
> ```python
> if item.reducao_base_icms and item.reducao_base_icms > 0:
>     base_difal = _base_calculo_padrao(item, ...)  # base sem redução
> else:
>     base_difal = icms.base_calculo
> ```
> Esse tratamento deve ser validado com a contabilidade durante a implementação.

### 6.2. Preenchimento no `ImpostosItem`

Adicionar os campos DIFAL na construção do `ImpostosItem`:

```python
itens_impostos.append(ImpostosItem(
    # ... campos existentes ...
    
    # DIFAL
    difal_base_calculo=resultado_difal.base_calculo if resultado_difal else None,
    difal_aliquota_interestadual=resultado_difal.aliquota_interestadual if resultado_difal else None,
    difal_aliquota_interna_destino=resultado_difal.aliquota_interna_destino if resultado_difal else None,
    difal_valor=resultado_difal.valor_difal if resultado_difal else None,
    difal_valor_remetente=resultado_difal.icms_interestadual_valor if resultado_difal else None,
    fcp_base_calculo=resultado_difal.fcp_base_calculo if resultado_difal else None,
    fcp_aliquota=resultado_difal.fcp_aliquota if resultado_difal else None,
    fcp_valor=resultado_difal.fcp_valor if resultado_difal else None,
))
```

---

## 7. Detalhamento: Alterações no `consolidador.py`

**Arquivo**: `app/services/fiscal/tax_engine/consolidador.py`

### 7.1. Acumular totais DIFAL/FCP

Na função `consolidar_totais`, após somar `valor_icms`:

```python
valor_difal = sum(
    (item.difal_valor or Decimal("0")) for item in itens_impostos
).quantize(PRECISAO, ROUND_MODE)

valor_fcp = sum(
    (item.fcp_valor or Decimal("0")) for item in itens_impostos
).quantize(PRECISAO, ROUND_MODE)

base_calculo_fcp = sum(
    (item.fcp_base_calculo or Decimal("0")) for item in itens_impostos
).quantize(PRECISAO, ROUND_MODE)
```

### 7.2. Incluir nos `TotaisNota`

```python
return TotaisNota(
    # ... campos existentes ...
    valor_difal=valor_difal,
    valor_fcp=valor_fcp,
    base_calculo_fcp=base_calculo_fcp,
)
```

### 7.3. O DIFAL e FCP NÃO entram no `valor_total_nota`

O total da nota (`vNF` do XML) é `valor dos produtos + frete + seguro + despesas − desconto + ICMS-ST + IPI`. O DIFAL e o FCP são informados em tags separadas (`<ICMSUFDest>`) e **não** compõem o total da nota — são tributos partilhados, não custo do produto. Essa regra é da SEFAZ e será validada na SPEC 6.

---

## 8. Cenários de cálculo (referência para testes)

### Cenário A: Base simples, sem FCP

```
Produto: R$ 1.000,00
UF Origem: CE    UF Destino: SP
Alíq. Interestadual: 7%    Alíq. Interna SP: 18%    FCP: 0%
Base dupla: Não

ICMS próprio  = 1.000 × 7%  = R$ 70,00
DIFAL         = 1.000 × (18% - 7%) = 1.000 × 11% = R$ 110,00
FCP           = R$ 0,00
```

### Cenário B: Base simples, com FCP

```
Produto: R$ 500,00
UF Origem: CE    UF Destino: RJ
Alíq. Interestadual: 7%    Alíq. Interna RJ: 20%    FCP: 2%
Base dupla: Não

ICMS próprio  = 500 × 7%  = R$ 35,00
DIFAL         = 500 × (20% - 7%) = 500 × 13% = R$ 65,00
FCP           = 500 × 2%  = R$ 10,00
```

### Cenário C: Base dupla, com FCP

```
Produto: R$ 1.000,00
UF Origem: SP    UF Destino: BA
Alíq. Interestadual: 12%    Alíq. Interna BA: 20,5%    FCP: 2%
Base dupla: Sim

Base_dupla    = 1.000 / (1 − 0,205) = 1.000 / 0,795 = R$ 1.257,86
ICMS próprio  = 1.000 × 12% = R$ 120,00
ICMS destino  = 1.257,86 × 20,5% = R$ 257,86
DIFAL         = 257,86 − 120,00 = R$ 137,86
FCP           = 1.257,86 × 2% = R$ 25,16
```

### Cenário D: Alíquota interestadual ≥ interna (ZFM)

```
Produto: R$ 1.000,00
UF Origem: SP    UF Destino: AM (Zona Franca)
Alíq. Interestadual: 12%    Alíq. Interna AM: 12%    FCP: 0%

ICMS próprio  = 1.000 × 12% = R$ 120,00
DIFAL         = 1.000 × (12% - 12%) = R$ 0,00  (diferencial zero)
FCP           = R$ 0,00
```

### Cenário E: Operação interna (sem DIFAL)

```
Produto: R$ 1.000,00
UF Origem: CE    UF Destino: CE (mesma UF)

Nenhum campo DIFAL preenchido no ItemEntrada.
O engine NÃO chama calcular_difal.
Todos os campos DIFAL no ImpostosItem = None.
Comportamento idêntico ao de antes da SPEC 4.
```

---

## 9. Critérios de Aceite

### CA-1: Calculadora DIFAL funciona
- [ ] `calcular_difal` com base simples produz resultados corretos (Cenário A)
- [ ] `calcular_difal` com FCP soma corretamente (Cenário B)
- [ ] `calcular_difal` com base dupla usa a fórmula `base / (1 - aliq)` (Cenário C)
- [ ] `calcular_difal` com alíquota inter ≥ interna retorna DIFAL = 0, nunca negativo (Cenário D)
- [ ] `calcular_difal` com alíquota interna = 100% levanta `ValueError`
- [ ] A função é pura: sem DB, sem HTTP, sem efeitos colaterais
- [ ] Usa `PRECISAO` e `ROUND_MODE` das constantes do engine

### CA-2: DTOs expandidos são retrocompatíveis
- [ ] `ItemEntrada` sem campos DIFAL funciona normalmente (todos têm default None/0/False)
- [ ] `ImpostosItem` sem DIFAL retorna None nos campos novos
- [ ] `TotaisNota` com DIFAL/FCP zerados quando não há operação interestadual
- [ ] Nenhum chamador existente do engine precisa ser alterado (Cenário E)

### CA-3: Resolver consulta o perfil corretamente
- [ ] Operação interestadual + não contribuinte + produto com perfil → calcula DIFAL
- [ ] Operação interestadual + não contribuinte + produto **sem** perfil → `OperacaoInterestadualError` com mensagem orientadora
- [ ] Operação interestadual + contribuinte (PJ com IE) → `OperacaoInterestadualError` (mantém trava para SPEC 5)
- [ ] Operação interna (mesma UF) → nenhum DIFAL, comportamento inalterado
- [ ] Venda presencial para cliente de outra UF → tratada como interna (sem DIFAL), comportamento inalterado
- [ ] `_cliente_nao_contribuinte` retorna True para PF, PJ sem IE, e venda sem cliente
- [ ] `_cliente_nao_contribuinte` retorna False para PJ com IE preenchida

### CA-4: Engine orquestra DIFAL após ICMS
- [ ] Pipeline: rateio → ICMS → **DIFAL** → PIS/COFINS → consolidação
- [ ] DIFAL usa a base de cálculo do ICMS (sem redução, quando aplicável)
- [ ] Consolidador acumula `valor_difal`, `valor_fcp`, `base_calculo_fcp`
- [ ] DIFAL e FCP **não** entram no `valor_total_nota`
- [ ] `valor_icms` nos totais reflete o ICMS pela alíquota interestadual (não a interna do emitente)

### CA-5: Cenários numéricos conferem
- [ ] Cenário A: DIFAL = R$ 110,00, FCP = R$ 0,00
- [ ] Cenário B: DIFAL = R$ 65,00, FCP = R$ 10,00
- [ ] Cenário C: DIFAL = R$ 137,86, FCP = R$ 25,16 (±R$ 0,01 de arredondamento)
- [ ] Cenário D: DIFAL = R$ 0,00, FCP = R$ 0,00
- [ ] Cenário E: todos campos DIFAL = None, totais DIFAL = 0

### CA-6: Testes automatizados
- [ ] Testes unitários para `calcular_difal` cobrindo os 5 cenários acima
- [ ] Testes unitários para `_cliente_nao_contribuinte` com PF, PJ com IE, PJ sem IE, sem cliente
- [ ] Testes de integração do `resolver_aliquotas_venda` para operação interestadual com perfil
- [ ] Testes de integração do `calcular_impostos` end-to-end com DIFAL
- [ ] Todos os testes existentes continuam passando (operações internas inalteradas)

### CA-7: Payload XML ainda não é alterado
- [ ] O `payload_builder.py` **não** é modificado nesta spec
- [ ] O `local_destino` continua hardcoded como `1` no builder
- [ ] Os valores DIFAL/FCP ficam apenas no `ResultadoCalculo`, prontos para SPEC 6


---

## Desvios aplicados (2026-09-18)
Ver `docs/done/fiscal/TASK007.md`. Destaques: **Simples Nacional liberado sem DIFAL e sem perfil** (ADI 5464 — premissa legal a confirmar); CST 20 com base cheia; trava reestruturada em `_uf_destino_interestadual`; teste antigo da trava reescrito. Cenários A–E exatos. 24 testes novos, gate 1006 passed. Payload intacto (CA-7).
