# SPEC 5 — Motor de Cálculo ICMS-ST + Derivação Dinâmica de CST e CFOP Interestadual

## 1. Objetivo

Implementar o cálculo do **ICMS por Substituição Tributária (ICMS-ST)** para operações interestaduais destinadas a contribuintes do ICMS (`indIEDest` 1 ou 2) e automatizar a **derivação contextual de CFOP e CST/CSOSN** de acordo com a operação (interna vs interestadual, contribuinte vs não contribuinte, com ST vs sem ST).

Ao final desta spec:
- A trava de operações interestaduais para clientes **contribuintes** será completamente desbloqueada (desde que haja `PerfilTributario` vinculado);
- A calculadora `icms_st.py` calculará a Base de ST e o Valor Retido por ST, integrando ao total da nota;
- Os módulos de derivação fiscal responderão automaticamente com os CFOPs (ex: `6102`, `6108`, `6404`) e CSTs (ex: `000`, `010`, `070` ou CSOSN `201`/`202`) corretos, eliminando ambiguidade e erros manuais;
- O payload de emissão XML continuará intocado até a SPEC 6, mantendo os resultados isolados no `ResultadoCalculo`.

---

## 2. Contexto: A Encruzilhada Tributária Interestadual (B2B vs B2C)

### 2.1. O Cenário B2B com ICMS-ST

Diferente do DIFAL (venda para consumidor final não contribuinte, coberto na SPEC 4), as vendas interestaduais entre empresas inscritas (B2B - Contribuinte) podem envolver antecipação do recolhimento tributário relativo a etapas subsequentes da cadeia de circulação da mercadoria:

1. **Cliente Contribuinte (`indIEDest == 1` ou `2`)**:
   - **Caso 1: Sem ST (`mva_st` nulo ou zero)**:
     Operação comercial normal de revenda interestadual. O emitente recolhe apenas o ICMS próprio pela alíquota interestadual (7% ou 12%). Não há retenção. CFOP típico: `6.102` (revenda) ou `6.101` (produção). CST: `00` / CSOSN: `102`.
   - **Caso 2: Com ST (`mva_st > 0`)**:
     O emitente assume a condição de **Substituto Tributário** por força de Convênio/Protocolo ICMS. Ele recolhe o seu ICMS próprio interestadual e retém o imposto devido no estado de destino calculado sobre o preço estimado de venda no varejo destino (aplicando a Margem de Valor Agregado - MVA). CFOP típico: `6.404` (revenda com ST) ou `6.403` (produção com ST). CST: `010` (ou `070` se houver redução de base) / CSOSN: `201` ou `202`.

### 2.2. A Diferença Financeira Crítica: DIFAL vs ICMS-ST

> [!IMPORTANT]
> **O ICMS-ST compõe o valor total da nota fiscal (`vNF`), enquanto o DIFAL NÃO compõe.**
> - No DIFAL (Consumidor Final B2C), o imposto já está embutido no preço comercial do item; trata-se de partilha entre os Estados. O comprador paga o preço normal da mercadoria.
> - No ICMS-ST (B2B), o imposto retido é um encargo cobrado **a mais** do destinatário na fatura. O valor do ICMS-ST é somado ao total dos produtos, frete e despesas para compor o `vNF` e a cobrança financeira.

### 2.3. Resolução da Ambiguidade em `cfop.py`

Na codebase atual ([`app/services/fiscal/derivacao/cfop.py:133-139`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/derivacao/cfop.py#L133-L139)), existe a seguinte exceção proposital:

```python
if grupo == GRUPO_INTERESTADUAL:
    raise DerivacaoAmbiguaError(
        "Saida interestadual de mercadoria com ICMS-ST retido nao tem "
        "CFOP derivavel: nao existe equivalente limpo do 5.405 (...)"
    )
```

Essa trava existia porque o sistema não tinha como saber se havia protocolo de ST para a UF destino. Com o **Perfil Tributário**, essa ambiguidade deixa de existir: **é o próprio perfil cadastrado pelo contador da loja que dita se há ST para aquela UF e NCM através do campo `mva_st`**.

---

## 3. Detalhamento: Nova Calculadora `icms_st.py`

**Arquivo**: `app/services/fiscal/tax_engine/calculators/icms_st.py`

### 3.1. Dataclass de Retorno

```python
@dataclass
class ResultadoICMSST:
    """Resultado do cálculo de ICMS Substituição Tributária para um item."""

    base_calculo_st: Decimal
    mva: Decimal                         # Margem de Valor Agregado aplicada (%)
    aliquota_interna_destino: Decimal    # Alíquota interna da UF destino (%)
    aliquota_interestadual: Decimal      # Alíquota interestadual usada no ICMS próprio (%)
    valor_icms_proprio: Decimal          # ICMS da operação própria abatido da ST
    valor_icms_st: Decimal               # Valor efetivo do ICMS-ST retido
    reducao_base_st: Optional[Decimal] = None
```

### 3.2. Fórmula de Cálculo e Parâmetros

A base do ICMS-ST é calculada aplicando-se a MVA sobre o somatório de produto, frete, seguro, outras despesas, IPI (se houver) menos desconto:

$$\text{Base Inicial} = \text{Valor Bruto} + \text{Frete} + \text{Seguro} + \text{Despesas} - \text{Desconto}$$

$$\text{Base ST} = \text{Base Inicial} \times \left(1 + \frac{\text{MVA}}{100}\right)$$

Se houver percentual de redução de base de cálculo da ST (`reducao_base_calculo > 0`):
$$\text{Base ST Reduzida} = \text{Base ST} \times \left(1 - \frac{\text{Redução}}{100}\right)$$

O valor do débito total no destino é:
$$\text{Débito Destino} = \text{Base ST (ou Reduzida)} \times \frac{\text{Alíquota Interna Destino}}{100}$$

O ICMS-ST retido a pagar é o valor do débito no destino abatido do ICMS próprio que o remetente já recolheu na operação interestadual:
$$\text{ICMS-ST} = \text{Débito Destino} - \text{ICMS Próprio}$$

```python
def calcular_icms_st(
    base_inicial: Decimal,
    aliquota_interestadual: Decimal,
    aliquota_interna_destino: Decimal,
    mva: Decimal,
    reducao_base_st: Optional[Decimal] = None,
    icms_proprio_informado: Optional[Decimal] = None,
) -> ResultadoICMSST:
    """
    Calcula a Substituição Tributária (ICMS-ST) interestadual para contribuinte.
    Função pura (sem DB ou HTTP).
    """
    CEM = Decimal("100")

    # 1. ICMS próprio (se não fornecido externamente, calcula sobre a base inicial)
    if icms_proprio_informado is not None:
        icms_proprio = icms_proprio_informado
    else:
        icms_proprio = (base_inicial * aliquota_interestadual / CEM).quantize(PRECISAO, ROUND_MODE)

    # 2. Base ST com MVA
    fator_mva = (CEM + mva) / CEM
    base_st = (base_inicial * fator_mva).quantize(PRECISAO, ROUND_MODE)

    # 3. Redução de base de cálculo ST (se aplicável)
    if reducao_base_st and reducao_base_st > Decimal("0"):
        fator_red = (CEM - reducao_base_st) / CEM
        base_st_efetiva = (base_st * fator_red).quantize(PRECISAO, ROUND_MODE)
    else:
        base_st_efetiva = base_st

    # 4. Débito no destino
    debito_destino = (base_st_efetiva * aliquota_interna_destino / CEM).quantize(PRECISAO, ROUND_MODE)

    # 5. Valor ST retido (nunca negativo)
    valor_st = (debito_destino - icms_proprio).quantize(PRECISAO, ROUND_MODE)
    if valor_st < Decimal("0"):
        valor_st = Decimal("0")

    return ResultadoICMSST(
        base_calculo_st=base_st_efetiva,
        mva=mva,
        aliquota_interna_destino=aliquota_interna_destino,
        aliquota_interestadual=aliquota_interestadual,
        valor_icms_proprio=icms_proprio,
        valor_icms_st=valor_st,
        reducao_base_st=reducao_base_st,
    )
```

---

## 4. Detalhamento: Expansão dos DTOs (`tax_engine/types.py`)

**Arquivo**: [`app/services/fiscal/tax_engine/types.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/types.py)

### 4.1. `ItemEntrada`

Adicionar parâmetros para ST interestadual:
```python
# --- ICMS-ST (operação interestadual B2B - Contribuinte) ---
# Preenchido quando o destinatário é contribuinte e o Perfil possui mva_st > 0.
st_aliquota_interestadual: Optional[Decimal] = None
st_aliquota_interna_destino: Optional[Decimal] = None
st_mva: Optional[Decimal] = None
st_reducao_base: Optional[Decimal] = None
```

### 4.2. `ImpostosItem`

Armazenar o resultado por item para o payload e conferência contábil:
```python
# --- ICMS-ST ---
icms_st_modalidade_base_calculo: int = 4  # 4 = Margem Valor Agregado (%)
icms_st_base_calculo: Optional[Decimal] = None
icms_st_aliquota: Optional[Decimal] = None
icms_st_valor: Optional[Decimal] = None
icms_st_mva: Optional[Decimal] = None
icms_st_reducao_base: Optional[Decimal] = None
```

### 4.3. `TotaisNota`

Acrescentar os agregadores que alimentam o cabeçalho do documento fiscal:
```python
base_calculo_icms_st: Decimal = Decimal("0")
valor_icms_st: Decimal = Decimal("0")
```

---

## 5. Detalhamento: Motor e Consolidador

### 5.1. No `tax_engine/engine.py`

O pipeline do motor agora contempla os dois braços da encruzilhada interestadual de forma estritamente ordenada:

```python
# 1. Rateio proporcional
# 2. ICMS Próprio (calcular_icms)
# 3. Encruzilhada Interestadual:
if item.difal_aliquota_interestadual is not None:
    # Braço Não Contribuinte (SPEC 4)
    resultado_difal = calcular_difal(...)
elif item.st_mva is not None and item.st_mva > Decimal("0"):
    # Braço Contribuinte com ST (SPEC 5)
    resultado_st = calcular_icms_st(
        base_inicial=icms.base_calculo,
        aliquota_interestadual=item.st_aliquota_interestadual,
        aliquota_interna_destino=item.st_aliquota_interna_destino,
        mva=item.st_mva,
        reducao_base_st=item.st_reducao_base,
        icms_proprio_informado=icms.valor,
    )
# 4. PIS / COFINS (calcular_pis_cofins)
# 5. Consolidação
```

### 5.2. No `tax_engine/consolidador.py`

O consolidador deve:
1. Somar `base_calculo_icms_st` e `valor_icms_st` de todos os itens;
2. **Atualizar `valor_total_nota` somando `valor_icms_st`**:

$$\text{Valor Total da Nota} = \text{Produtos} + \text{Frete} + \text{Seguro} + \text{Despesas} - \text{Desconto} + \mathbf{Valor ICMS-ST}$$

```python
valor_total_nota = (
    totais_produtos + dados_nota.frete + dados_nota.seguro + dados_nota.outras_despesas
    - dados_nota.desconto_nota + valor_icms_st
).quantize(PRECISAO, ROUND_MODE)
```

---

## 6. Detalhamento: Inteligência de Derivação (CFOP e CST/CSOSN)

### 6.1. Derivação de CFOP ([`derivacao/cfop.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/derivacao/cfop.py))

A função `derivar_cfop` recebe a informação de se a regra do perfil para aquela operação contém ST:

```python
def derivar_cfop_operacao(
    uf_emitente: str,
    uf_destinatario: Optional[str],
    indicador_presenca: int,
    indicador_ie_destinatario: int, # 1=Contribuinte, 2=Isento, 9=Não Contribuinte
    existe_st_na_regra: bool,
    eh_producao_propria: bool = False,
) -> str:
    """
    Derivação precisa e determinística de CFOP eliminando qualquer ambiguidade.
    """
    # Operação interna (mesma UF ou presencial)
    if indicador_presenca == 1 or not uf_destinatario or uf_destinatario.upper() == uf_emitente.upper():
        if existe_st_na_regra:
            return "5405" # Venda mercadoria sujeita a ST (substituído)
        return "5101" if eh_producao_propria else "5102"

    # Operação Interestadual:
    if indicador_ie_destinatario == 9:
        # Venda interestadual para consumidor final não contribuinte (DIFAL)
        return "6108"

    # Venda interestadual para contribuinte:
    if existe_st_na_regra:
        # Remetente atua como substituto tributário
        return "6403" if eh_producao_propria else "6404"
    else:
        # Operação interestadual normal entre contribuintes
        return "6101" if eh_producao_propria else "6102"
```

### 6.2. Derivação de Situação Tributária ([`derivacao/situacao.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/derivacao/situacao.py))

Ajustar a indicação de CST/CSOSN quando a operação é interestadual:

| Tipo Cliente | Regime Emitente | Há ST (`mva_st > 0`) | CST / CSOSN Sugerido | Fundamentação |
|---|---|---|---|---|
| Não Contribuinte (`indIEDest=9`) | Regime Normal | Irrelevante | `00` | ICMS próprio normal; DIFAL vai no nó `<ICMSUFDest>` |
| Não Contribuinte (`indIEDest=9`) | Simples Nacional | Irrelevante | `102` | Simples sem crédito |
| Contribuinte (`indIEDest=1/2`) | Regime Normal | **Não** (`mva=0`) | `00` | Tributada integralmente pela alíquota interestadual |
| Contribuinte (`indIEDest=1/2`) | Regime Normal | **Sim** (`mva>0`) | `10` (ou `70` c/ redução) | Tributada e com cobrança do ICMS por Substituição Tributária |
| Contribuinte (`indIEDest=1/2`) | Simples Nacional | **Sim** (`mva>0`) | `201` (ou `202`) | Tributada pelo Simples com cobrança de ST |

---

## 7. Detalhamento: Integração no `resolver.py`

**Arquivo**: [`app/services/fiscal/tax_engine/resolver.py`](file:///c:/dev/bigpdv/backend-fastapi/app/services/fiscal/tax_engine/resolver.py)

### 7.1. Desbloqueio Definitivo da Trava Interestadual

O `resolver.py` agora contempla **ambos os casos**:
1. Se `_cliente_nao_contribuinte(venda)` -> Fluxo DIFAL (SPEC 4);
2. Se cliente **Contribuinte** -> Fluxo ICMS-ST (SPEC 5).

Se o cliente for contribuinte e o produto tiver `perfil_tributario_id`:
1. Consulta a regra via `resolver_regra_perfil(...)`;
2. Se a regra tiver `mva_st > 0`:
   - Preenche `st_mva`, `st_aliquota_interestadual`, `st_aliquota_interna_destino`, `st_reducao_base` no `ItemEntrada`;
   - Ajusta o CFOP efetivo do item para `6404` (ou correspondente derivado);
   - Ajusta o CST do item para `10` (ou CSOSN `201`/`202`);
3. Se a regra tiver `mva_st` nulo ou zero:
   - Operação interestadual normal B2B;
   - Alíquota de ICMS próprio do item passa a ser a `aliquota_interestadual` da regra;
   - CFOP vira `6102`;
   - CST vira `00` (ou CSOSN `102`).

Se o produto **não possuir perfil tributário**, a exceção `OperacaoInterestadualError` é mantida, orientando o usuário a configurar o perfil.

---

## 8. Cenários de Cálculo Numérico (Referência para Testes)

### Cenário 1: Venda Interestadual Contribuinte com ST (Sem Redução de Base)

```
Valor Produto: R$ 1.000,00 | Frete: R$ 0,00 | Desconto: R$ 0,00
UF Origem: SP | UF Destino: MG
Cliente: PJ Contribuinte (IE ativa em MG, indIEDest = 1)
Regra Perfil:
  - Alíq. Interestadual: 12%
  - Alíq. Interna Destino: 18%
  - MVA: 40%
  - Redução Base: 0%

Cálculo:
1. Base Inicial = R$ 1.000,00
2. ICMS Próprio = 1.000,00 * 12% = R$ 120,00
3. Base ST = 1.000,00 * (1 + 0,40) = R$ 1.400,00
4. Débito Destino = 1.400,00 * 18% = R$ 252,00
5. ICMS-ST Retido = 252,00 - 120,00 = R$ 132,00
6. Total da Nota (vNF) = 1.000,00 (produto) + 132,00 (ST) = R$ 1.132,00
7. CFOP Derivado: 6404 | CST Derivado: 010
```

### Cenário 2: Venda Interestadual Contribuinte com ST e com Redução de Base

```
Valor Produto: R$ 1.000,00
Alíq. Interestadual: 12% | Alíq. Interna Destino: 18%
MVA: 40% | Redução Base ST: 20%

Cálculo:
1. ICMS Próprio = 1.000,00 * 12% = R$ 120,00
2. Base ST Bruta = 1.000,00 * 1,40 = R$ 1.400,00
3. Base ST Efetiva (redução 20%) = 1.400,00 * (1 - 0,20) = R$ 1.120,00
4. Débito Destino = 1.120,00 * 18% = R$ 201,60
5. ICMS-ST Retido = 201,60 - 120,00 = R$ 81,60
6. Total da Nota (vNF) = 1.000,00 + 81,60 = R$ 1.081,60
7. CFOP Derivado: 6404 | CST Derivado: 070
```

### Cenário 3: Venda Interestadual Contribuinte SEM ST (`mva == 0`)

```
Valor Produto: R$ 1.000,00
Alíq. Interestadual: 12% | Alíq. Interna Destino: 18%
MVA: 0% (ou nulo)

Cálculo:
1. ICMS Próprio = 1.000,00 * 12% = R$ 120,00
2. ICMS-ST = R$ 0,00 (não se aplica ST)
3. Total da Nota (vNF) = R$ 1.000,00 (ST não é somada)
4. CFOP Derivado: 6102 | CST Derivado: 00
```

---

## 9. Critérios de Aceite

### CA-1: Calculadora `calcular_icms_st`
- [ ] Implementada em `tax_engine/calculators/icms_st.py` como função pura e isolada.
- [ ] Executa a fórmula $\text{Base ST} = \text{Base} \times (1 + \text{MVA})$ com precisão decimal.
- [ ] Aplica redução de base de ST se informada (`reducao_base_st`).
- [ ] Deduz o ICMS próprio do débito destino para apurar o valor retido.
- [ ] Garante que `valor_icms_st` nunca seja negativo (piso zero).

### CA-2: Composição do Total da Nota
- [ ] O consolidador de totais (`consolidador.py`) soma o `valor_icms_st` ao `valor_total_nota`.
- [ ] Valida que notas interestaduais B2B com ST têm `vNF` maior que o total dos produtos.
- [ ] Valida que notas sem ST (ou com DIFAL B2C) mantêm o `vNF` sem essa adição.

### CA-3: Derivação Automática de CFOP e CST/CSOSN
- [ ] Operação interestadual B2C (`indIEDest=9`) deriva CFOP `6108` e CST `00`.
- [ ] Operação interestadual B2B sem ST (`mva=0`) deriva CFOP `6102` e CST `00`.
- [ ] Operação interestadual B2B com ST (`mva>0`) deriva CFOP `6404` e CST `010` (ou `070` se redução de base).
- [ ] Não lança mais `DerivacaoAmbiguaError` quando o perfil tiver a regra cadastrada.

### CA-4: Desbloqueio e Tratamento de Erros no Resolver
- [ ] Venda interestadual para contribuinte com perfil configurado e regra compatível é processada com sucesso.
- [ ] Venda interestadual para contribuinte cujo produto não tem perfil lança `OperacaoInterestadualError` com mensagem amigável explicando a necessidade do Perfil Tributário.
- [ ] Venda interestadual cujo perfil não possui regra (nem fallback) lança `OperacaoInterestadualError`.

### CA-5: Retrocompatibilidade e Testes
- [ ] Vendas internas (balcão e entrega mesma UF) mantêm cálculo e comportamento 100% inalterados.
- [ ] Suíte de testes unitários para a calculadora cobrindo Cenários 1, 2 e 3.
- [ ] Testes de integração no `resolver.py` cobrindo o roteamento dinâmico DIFAL vs ST.
- [ ] Nenhuma alteração no `payload_builder.py` nesta fase (reserva para SPEC 6).


---

## Desvios aplicados (2026-09-19)
Ver `docs/fiscal/archive/TASK008.md`. Destaques: CST 10/70 e CSOSN 201/202 só na emissão (não no cadastro); sem ST a situação do produto não muda; 6107/6101/6403 por produção própria; dedução do ICMS próprio no Simples pela interestadual; CFOP 6xxx também para Simples B2C. 36 testes novos, gate 1043 passed. Payload intacto.
