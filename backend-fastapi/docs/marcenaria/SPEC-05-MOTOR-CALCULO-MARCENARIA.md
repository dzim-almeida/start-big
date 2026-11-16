# Spec 05 — Motor de Cálculo do Orçamento de Marcenaria

| Campo        | Valor                                                                         |
|--------------|-------------------------------------------------------------------------------|
| Status       | Implementada em 09/10/2026                                                    |
| Camada       | Backend (Python puro, sem banco)                                              |
| Dependências | Spec 04A (parâmetros e `sofre_perda`)                                         |
| Bloqueia     | Spec 06A, Spec 08A, Spec 09A                                                  |
| Referência   | SPEC-00: C1–C8, C3a, C5a–C5d, O3a, O4, C9 (Revisão 6) · PR4, PR6              |

> **Revisão 1 (08/10/2026) — pedidos da Spec 06B e da SPEC-00 Revisão 15.** (1) Duas saídas novas, **só para exibição**: `desconto_bp_efetivo` e `sinal_bp_efetivo` (o percentual equivalente quando o usuário digita em R$; 06B D18 mostra "≈ 5%" sem calcular em TypeScript, C8). Nenhum número existente muda; os cenários da §11 continuam idênticos (conferidos de novo em 08/10). (2) `app/services/marcenaria/__init__.py` passa a nascer na Spec 04A (onde ficam as permissões); aqui só se confere.

---

## 1. Objetivo

Escrever o **único** lugar do sistema que calcula preço, custo, margem, RT, desconto, sinal e saldo do orçamento de marcenaria (C8). São **funções puras**: recebem números, devolvem números, não leem banco, não gravam nada e não sabem de HTTP. Todas as outras specs (orçamento, aprovação, OS, RT, telas) usam o resultado delas e nunca refazem a conta.

Ao final desta spec, os casos de teste da §11, com valores conferidos à mão e por um protótipo, passam.

## 2. Escopo

**Dentro do escopo**
- Tipos de entrada e saída (dataclasses imutáveis).
- Cálculo por móvel, por linha, por ambiente e do orçamento.
- Desconto global (C9), RT nos dois modos (C5c), repartição do RT por linha (C5d), sinal (C7).
- Avisos (insumo sem custo, horas sem custo/hora, margem negativa).
- Validações de entrada com mensagens em português.
- Testes de unidade, de exemplo e de propriedades.

**Fora do escopo**
- Ler o orçamento do banco e chamar o motor (Spec 06A).
- Copiar o custo do produto (O3a) e os parâmetros (04A) para o orçamento (Spec 06A).
- Gerar a OS e a conta a pagar do RT (Specs 08A e 09A).
- Exibir (Specs 06B, 07).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── app/services/marcenaria/
│   ├── __init__.py                     # CONFERIR — criado na Spec 04A (Revisão 1)
│   └── calculo.py                      # CRIAR — o motor
└── test/services/marcenaria/
    ├── __init__.py                     # CRIAR (vazio)
    └── test_calculo.py                 # CRIAR — §11
```

O pacote `app/services/marcenaria/` recebe, nas próximas specs, os serviços do orçamento. O motor fica num arquivo próprio e **não importa** nada de `app.db` nem de `fastapi` (um teste confere isso).

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Dinheiro em **centavos** (`int`); percentuais em **basis points** (`int`, 9000 = 90%); quantidade de insumo em **milésimos** (`int`, 1,4 chapa = 1400); horas em **centésimos** (`int`, 2,5 h = 250); quantidade de móvel em unidades (`int` ≥ 1) | PR4. Inteiro no banco, sem `float`. Milésimos cobrem "26,000 m de fita"; centésimos cobrem "2,25 h" |
| D2 | Contas intermediárias em `Decimal`; arredondamento **meio centavo para cima** (`ROUND_HALF_UP`) | C6 |
| D3 | **Dois** arredondamentos por móvel, e só esses: o **custo direto unitário** e o **preço unitário** | O custo unitário precisa ser inteiro (vira `custo_unitario` do item da OS, F2); o preço também (`valor_unitario`). Tudo acima disso são **somas de inteiros**, e por isso ambiente e total sempre fecham (C6) |
| D4 | A perda incide **por insumo**, só nos que têm `sofre_perda` (C2), com o percentual do orçamento | C2 |
| D5 | Mão de obra por móvel: **fixa** (centavos) ou **por horas** (centésimos de hora × custo/hora) (C4) | C4 |
| D6 | Instalação é uma **linha própria** do orçamento (C3), com o mesmo fator de preço dos móveis (C3a) | C3, C3a |
| D7 | Fator de preço: **modo MARGEM** `(1 + markup)`; **modo PRECO** `(1 + markup) ÷ (1 − RT)` | C5c. No modo PRECO, depois de pagar o RT sobre o preço, sobra o mesmo que sobraria sem arquiteto |
| D8 | **Desconto global** (C9): em % (bp) **ou** em R$ (centavos), sobre o **total bruto** das linhas incluídas. Desconto em R$ maior que o bruto é **erro** | C9 |
| D9 | **RT sobre o total líquido** (o que o cliente paga, depois do desconto), arredondado uma vez | C5b, C9 |
| D10 | O RT é **repartido entre as linhas** proporcionalmente ao preço de cada linha, pelo **método do maior resto**: a soma das partes é **exatamente** o RT total | C5d. A conta a pagar do arquiteto (09A) e a parte do RT no custo dos itens (08A) falam do mesmo número |
| D11 | Parte do RT **por unidade** (para o `custo_unitario` da OS) = parte da linha ÷ quantidade, **por baixo**. A sobra (menos de 1 centavo por unidade, no máximo `qtd − 1` centavos na linha) **não** entra no custo | O item da OS tem um só `custo_unitario`. A base da comissão do vendedor fica, no máximo, alguns centavos **maior**, que é o lado em que o sistema já escolheu errar (`relatorio.get_comissao_base`: "a favor do funcionário") |
| D12 | Sinal: em % (bp) **ou** em R$, sobre o **total líquido**; pode ser **zero** (C7). Sinal em R$ maior que o total é **erro** | C7 |
| D13 | O motor recebe **só as linhas incluídas** (móveis aprovados e, se for o caso, a instalação) | O4: a aprovação parcial recalcula tudo sobre o que foi aceito, com a mesma função |
| D14 | Margem líquida em basis points, arredondada; total zero → margem 0 (sem divisão por zero) | Exibição da margem (T3a) |
| D15 | **Avisos** não bloqueiam o cálculo; **erros** (`ValueError` com mensagem em português) bloqueiam | Um insumo sem custo é aviso (O3a); quantidade negativa é erro |

---

## 5. Contrato do motor

### 5.1. Entrada

```python
@dataclass(frozen=True)
class InsumoCalc:
    quantidade_milesimos: int        # 1,4 chapa = 1400; deve ser > 0
    custo_unit_centavos: int         # copiado do produto (O3a); >= 0
    sofre_perda: bool                # copiado do produto (04A)


@dataclass(frozen=True)
class MovelCalc:
    id: str                          # devolvido como veio, para quem chamou se achar
    quantidade: int                  # unidades do móvel; >= 1
    insumos: tuple[InsumoCalc, ...]  # pode ser vazio (móvel só de terceirizado, por exemplo)
    mao_obra_modo: Literal["FIXA", "HORAS", "NENHUMA"]
    mao_obra_centavos: int = 0       # usado em FIXA; >= 0
    mao_obra_horas_centesimos: int = 0  # usado em HORAS; >= 0
    terceirizado_centavos: int = 0   # custo do pedido externo, por unidade (E6); >= 0


@dataclass(frozen=True)
class AmbienteCalc:
    id: str
    moveis: tuple[MovelCalc, ...]    # só os incluídos (D13)


@dataclass(frozen=True)
class AjusteCalc:
    """Desconto ou sinal: percentual OU valor (D8, D12)."""
    modo: Literal["PERCENTUAL", "VALOR"]
    valor: int                       # bp em PERCENTUAL, centavos em VALOR; >= 0


@dataclass(frozen=True)
class OrcamentoCalc:
    ambientes: tuple[AmbienteCalc, ...]
    markup_bp: int                   # 0 a 100000
    perda_bp: int                    # 0 a 5000
    custo_hora_centavos: int         # >= 0
    rt_bp: int                       # 0 a 3000
    rt_modo: Literal["MARGEM", "PRECO"]
    instalacao_custo_centavos: int | None   # None = sem linha de instalação (ou não incluída)
    desconto: AjusteCalc = AjusteCalc("PERCENTUAL", 0)
    sinal: AjusteCalc = AjusteCalc("PERCENTUAL", 0)
```

### 5.2. Saída

```python
@dataclass(frozen=True)
class MovelResultado:
    id: str
    quantidade: int
    material_centavos: Decimal       # sem arredondar (exibição pode arredondar)
    perda_centavos: Decimal
    mao_obra_centavos: Decimal
    terceirizado_centavos: int
    custo_unit_centavos: int         # 1º arredondamento (D3)
    preco_unit_centavos: int         # 2º arredondamento (D3)
    custo_total_centavos: int        # custo_unit × quantidade
    preco_total_centavos: int        # preco_unit × quantidade (bruto, antes do desconto)
    rt_linha_centavos: int           # parte do RT desta linha (D10)
    rt_unit_centavos: int            # rt_linha // quantidade (D11)
    custo_os_unit_centavos: int      # custo_unit + rt_unit -> custo_unitario do item da OS (C5d)


@dataclass(frozen=True)
class AmbienteResultado:
    id: str
    moveis: tuple[MovelResultado, ...]
    subtotal_centavos: int           # soma dos preco_total (bruto); é o que a proposta mostra (T5)
    custo_centavos: int              # soma dos custo_total


@dataclass(frozen=True)
class InstalacaoResultado:
    custo_centavos: int
    preco_centavos: int
    rt_linha_centavos: int
    custo_os_centavos: int           # custo + rt_linha (quantidade 1)


@dataclass(frozen=True)
class OrcamentoResultado:
    ambientes: tuple[AmbienteResultado, ...]
    instalacao: InstalacaoResultado | None
    bruto_centavos: int              # soma dos subtotais + instalação
    desconto_centavos: int
    total_centavos: int              # bruto − desconto (o que o cliente paga)
    custo_total_centavos: int        # soma dos custos + custo da instalação
    margem_bruta_centavos: int       # total − custo_total
    rt_total_centavos: int           # arred(total × RT) (D9)
    margem_liquida_centavos: int     # margem_bruta − rt_total
    margem_liquida_bp: int           # D14
    sinal_centavos: int
    saldo_centavos: int              # total − sinal
    desconto_bp_efetivo: int         # Revisão 1: arred(desconto / bruto × 10000); 0 se bruto = 0. Só exibição
    sinal_bp_efetivo: int            # Revisão 1: arred(sinal / total × 10000); 0 se total = 0. Só exibição
    avisos: tuple[str, ...]          # códigos da §6.7
```

### 5.3. Função pública

```python
def calcular_orcamento(orcamento: OrcamentoCalc) -> OrcamentoResultado: ...
```

Mais duas funções públicas, usadas pelas telas e testes: `arredondar(valor: Decimal) -> int` e `fator_preco(markup_bp, rt_bp, rt_modo) -> Decimal`.

---

## 6. Especificação técnica

### 6.1. Passo 1 — custo de cada insumo (por unidade do móvel)

```
qtd           = quantidade_milesimos / 1000
custo_insumo  = qtd × custo_unit
perda_insumo  = custo_insumo × perda_bp / 10000     (só se sofre_perda; senão 0)
```

Nada é arredondado aqui.

### 6.2. Passo 2 — custo direto unitário do móvel (1º arredondamento)

```
material     = Σ custo_insumo
perda        = Σ perda_insumo
mao_obra     = FIXA:     mao_obra_centavos
               HORAS:    mao_obra_horas_centesimos / 100 × custo_hora_centavos
               NENHUMA:  0
custo_unit   = arred(material + perda + mao_obra + terceirizado)
```

### 6.3. Passo 3 — preço unitário (2º arredondamento) e linha

```
fator        = MARGEM: 1 + markup_bp/10000
               PRECO:  (1 + markup_bp/10000) / (1 − rt_bp/10000)
preco_unit   = arred(custo_unit × fator)
preco_total  = preco_unit × quantidade
custo_total  = custo_unit × quantidade
```

A instalação usa o mesmo fator: `preco_instalacao = arred(instalacao_custo × fator)`.

### 6.4. Passo 4 — totais, desconto, RT e margem

```
subtotal_ambiente = Σ preco_total dos móveis do ambiente
bruto             = Σ subtotal_ambiente + preco_instalacao
desconto          = PERCENTUAL: arred(bruto × bp/10000)
                    VALOR:      valor             (erro se valor > bruto)
total             = bruto − desconto
custo_total       = Σ custo_total + instalacao_custo
margem_bruta      = total − custo_total
rt_total          = arred(total × rt_bp/10000)
margem_liquida    = margem_bruta − rt_total
margem_liquida_bp = arred(margem_liquida / total × 10000)   (0 se total = 0)
sinal             = PERCENTUAL: arred(total × bp/10000)
                    VALOR:      valor             (erro se valor > total)
saldo             = total − sinal
desconto_bp_efetivo = arred(desconto / bruto × 10000)    (0 se bruto = 0)   -- Revisão 1, só exibição
sinal_bp_efetivo    = arred(sinal / total × 10000)       (0 se total = 0)   -- Revisão 1, só exibição
```

Os dois percentuais "efetivos" **não** entram em conta nenhuma: servem para a tela mostrar o equivalente do valor digitado (no modo `PERCENTUAL`, devolvem o próprio percentual ou o mais próximo dele, por causa do arredondamento em centavos).

### 6.5. Passo 5 — repartir o RT pelas linhas (maior resto)

As "linhas" são cada móvel (com seu `preco_total`) e a instalação, nesta ordem: ambientes na ordem recebida, móveis na ordem recebida, instalação por último.

```python
def repartir_maior_resto(total: int, pesos: list[int]) -> list[int]:
    """Divide `total` centavos proporcionalmente aos `pesos`, com soma EXATA.

    1. Cada parte recebe o piso da sua fração.
    2. Os centavos que sobram vão, um a um, para as maiores frações perdidas;
       empate: a linha que vem primeiro.
    """
    soma_pesos = sum(pesos)
    if total == 0 or soma_pesos == 0:
        return [0] * len(pesos)                                      # nada a repartir
    exatas = [Decimal(total) * p / soma_pesos for p in pesos]        # fração ideal de cada linha
    partes = [int(x) for x in exatas]                                # piso (valores >= 0)
    sobra = total - sum(partes)                                      # centavos ainda sem dono
    ordem = sorted(range(len(pesos)), key=lambda i: (-(exatas[i] - partes[i]), i))
    for i in ordem[:sobra]:                                          # maiores restos primeiro
        partes[i] += 1
    return partes
```

Depois, para cada móvel: `rt_unit = rt_linha // quantidade` e `custo_os_unit = custo_unit + rt_unit` (D11). Para a instalação: `custo_os = custo + rt_linha`.

**Por que os pesos são os preços brutos e o RT é o do total líquido:** o desconto é global, então ele reduz todas as linhas na mesma proporção. Repartir o RT líquido pelo peso bruto dá o mesmo resultado que aplicar o desconto em cada linha e calcular o RT de cada uma, sem criar centavos que não existem.

### 6.6. Validações (erros)

`ValueError` com a mensagem abaixo. A Spec 06A converte em `HTTPException(422)`.

| Situação | Mensagem |
|----------|----------|
| `quantidade` do móvel < 1 | "A quantidade do móvel deve ser pelo menos 1." |
| `quantidade_milesimos` ≤ 0 | "A quantidade do insumo deve ser maior que zero." |
| Algum valor em centavos, horas ou bp negativo | "Valores não podem ser negativos." |
| `markup_bp` > 100000, `perda_bp` > 5000, `rt_bp` > 3000 | Mesmas mensagens dos limites da Spec 04A §4.1 |
| Desconto ou sinal em PERCENTUAL > 10000 | "O percentual não pode passar de 100%." |
| Desconto em VALOR > bruto | "O desconto não pode ser maior que o total do orçamento." |
| Sinal em VALOR > total | "O sinal não pode ser maior que o total do orçamento." |
| `mao_obra_modo` inválido | "Forma de mão de obra inválida." |

### 6.7. Avisos (não bloqueiam)

| Código | Quando |
|--------|--------|
| `INSUMO_SEM_CUSTO` | Algum insumo com `custo_unit_centavos = 0` (O3a) |
| `HORAS_SEM_CUSTO_HORA` | Algum móvel com `HORAS`, horas > 0 e `custo_hora_centavos = 0` (04A, D12 da 04B) |
| `MARGEM_NEGATIVA` | `margem_liquida_centavos < 0` |
| `ORCAMENTO_VAZIO` | Nenhum móvel incluído e sem instalação |

As telas (06B) traduzem o código num texto; o motor não escreve frase para o usuário nos avisos.

### 6.8. Código de referência

O protótipo usado para conferir os números da §11 segue a mesma estrutura (ver §11.1). Regras de escrita:

- Nenhum `float` em lugar nenhum do arquivo (um teste procura `float(` no código-fonte do módulo).
- Toda função pública com docstring dizendo **em que unidade** entra e sai cada número.
- Comentário em cada passo das fórmulas (PR6).
- O arquivo não importa `app.db`, `sqlalchemy` nem `fastapi` (teste de arquitetura).

---

## 7. Limitações conhecidas

- **Diferença de centavos na base de comissão (D11):** num móvel com quantidade 2 e parte de RT ímpar, 1 centavo do RT não entra no `custo_unitario` da OS. A base da comissão do vendedor fica 1 centavo maior. A conta a pagar do arquiteto usa o RT total exato.
- **Precisão de insumo em milésimos:** 0,0005 chapa não é representável. Na prática, ninguém orça abaixo de 0,001.
- **Modo PRECO com desconto:** o RT é calculado sobre o total com desconto, então o desconto também reduz o que o RT "embutido" cobria. É o comportamento esperado (o arquiteto recebe sobre o que o cliente paga), mas a tela da 06B deve mostrar a margem atualizada ao aplicar o desconto.

## 8. Entrega (PR7)

Arquivo novo no backend: entra no próximo `npm run build:sidecar`. Pequeno; sem risco para o teto do PyArmor.

---

## 9. Registro na SPEC-00

Esta spec acrescenta à SPEC-00 (Revisão 6):

- **C9 — Desconto global:** em % ou R$, sobre o total bruto; aparece na proposta; vai para o `desconto` da OS (08A); sai da margem; RT sobre o total com desconto.
- **C5d (detalhe):** a parte do RT de cada linha é calculada pelo maior resto; no item da OS, por unidade, por baixo (D10, D11).

---

## 10. Critérios de aceite

- [ ] `calcular_orcamento` reproduz exatamente os três cenários da §11.2.
- [ ] A Torre Quente do Figma, sem mão de obra, dá custo R$ 1.922,50 e preço R$ 3.652,75 (número do PDF corrigido).
- [ ] Em qualquer orçamento: soma dos subtotais + instalação = bruto; total = bruto − desconto; soma das partes do RT = RT total; margem líquida = total − custo total − RT total; saldo = total − sinal.
- [ ] Nenhum `float` no módulo; nenhum import de banco ou de HTTP.
- [ ] Todas as validações da §6.6 com as mensagens indicadas.
- [ ] Os avisos da §6.7 aparecem nas situações descritas e não impedem o cálculo.
- [ ] 100 móveis com 30 insumos cada calculados em menos de 50 ms.
- [ ] Código comentado (PR6).

## 11. Casos de teste

Arquivo: `test/services/marcenaria/test_calculo.py`.

### 11.1. Dados do exemplo

Markup 90% (9000 bp), perda 10% (1000 bp), custo/hora R$ 45,00, RT 8% (800 bp), instalação R$ 750,00, sinal 40%.

**Torre Quente** (Figma, modal "Adicionar Móvel"), quantidade 1, mão de obra **fixa R$ 300,00**, terceirizado R$ 380,00:

| Insumo | Qtd | Custo unit. | Sofre perda | Custo | Perda 10% |
|--------|-----|-------------|-------------|-------|-----------|
| MDF Branco TX 18mm | 1,400 | R$ 280,00 | sim | R$ 392,00 | R$ 39,20 |
| MDF Freijó 18mm | 0,900 | R$ 380,00 | sim | R$ 342,00 | R$ 34,20 |
| Fita PVC Freijó 22mm (m) | 26,000 | R$ 3,50 | sim | R$ 91,00 | R$ 9,10 |
| Corrediça Tandem (par) | 2,000 | R$ 195,00 | não | R$ 390,00 | — |
| Perfil gola (barra) | 2,800 | R$ 87,50 | não | R$ 245,00 | — |
| **Total** | | | | **R$ 1.460,00** | **R$ 82,50** |

Custo direto unitário = 1.460,00 + 82,50 + 300,00 + 380,00 = **R$ 2.222,50**.

**Balcão**, quantidade **2**, mão de obra **4,00 h × R$ 45,00 = R$ 180,00**, sem terceirizado:

| Insumo | Qtd | Custo unit. | Sofre perda | Custo | Perda 10% |
|--------|-----|-------------|-------------|-------|-----------|
| MDF Branco TX 18mm | 1,000 | R$ 280,00 | sim | R$ 280,00 | R$ 28,00 |
| Corrediça Tandem (par) | 3,000 | R$ 195,00 | não | R$ 585,00 | — |

Custo direto unitário = 865,00 + 28,00 + 180,00 = **R$ 1.073,00**.

Os dois móveis no ambiente "Cozinha Gourmet".

### 11.2. Cenários (valores conferidos por protótipo em 06/10/2026)

**A) RT sai da margem, sem desconto**

| Linha | Qtd | Custo unit. | Preço unit. | Linha (bruto) | Parte do RT | Custo unit. na OS |
|-------|-----|-------------|-------------|---------------|-------------|-------------------|
| Torre Quente | 1 | 2.222,50 | 4.222,75 | 4.222,75 | 337,82 | 2.560,32 |
| Balcão | 2 | 1.073,00 | 2.038,70 | 4.077,40 | 326,19 | 1.236,09 (sobra 0,01) |
| Instalação | 1 | 750,00 | 1.425,00 | 1.425,00 | 114,00 | 864,00 |

| Resultado | Valor |
|-----------|-------|
| Subtotal Cozinha Gourmet | R$ 8.300,15 |
| Bruto | R$ 9.725,15 |
| Desconto | R$ 0,00 |
| **Total** | **R$ 9.725,15** |
| Custo total | R$ 5.118,50 |
| Margem bruta | R$ 4.606,65 |
| RT total | R$ 778,01 |
| Margem líquida | R$ 3.828,64 (3937 bp = 39,37%) |
| Sinal 40% | R$ 3.890,06 |
| Saldo | R$ 5.835,09 |

**B) RT sai da margem, desconto de 5%**

| Linha | Parte do RT | Custo unit. na OS |
|-------|-------------|-------------------|
| Torre Quente | 320,93 | 2.543,43 |
| Balcão | 309,88 | 1.227,94 |
| Instalação | 108,30 | 858,30 |

| Resultado | Valor |
|-----------|-------|
| Bruto | R$ 9.725,15 |
| Desconto 5% | R$ 486,26 |
| **Total** | **R$ 9.238,89** |
| Custo total | R$ 5.118,50 |
| Margem bruta | R$ 4.120,39 |
| RT total | R$ 739,11 |
| Margem líquida | R$ 3.381,28 (3660 bp) |
| Sinal 40% | R$ 3.695,56 |
| Saldo | R$ 5.543,33 |

**C) RT embutido no preço, desconto de 5%**

| Linha | Preço unit. | Linha (bruto) | Parte do RT | Custo unit. na OS |
|-------|-------------|---------------|-------------|-------------------|
| Torre Quente | 4.589,95 | 4.589,95 | 348,83 | 2.571,33 |
| Balcão | 2.215,98 | 4.431,96 | 336,83 | 1.241,41 (sobra 0,01) |
| Instalação | 1.548,91 | 1.548,91 | 117,72 | 867,72 |

| Resultado | Valor |
|-----------|-------|
| Bruto | R$ 10.570,82 |
| Desconto 5% | R$ 528,54 |
| **Total** | **R$ 10.042,28** |
| Margem bruta | R$ 4.923,78 |
| RT total | R$ 803,38 |
| Margem líquida | R$ 4.120,40 (4103 bp) |
| Sinal 40% | R$ 4.016,91 |
| Saldo | R$ 6.025,37 |

### 11.3. Unidade e bordas

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Torre Quente do Figma **sem** mão de obra (PDF §7) | Custo R$ 1.922,50; preço R$ 3.652,75 |
| 02 | `arredondar(Decimal("10.5"))`, `("10.4999")`, `("-0")` | 11, 10, 0 |
| 03 | Custo unitário que dá exatamente meio centavo no preço | Arredonda para cima |
| 04 | `repartir_maior_resto(10, [1, 1, 1])` | `[4, 3, 3]` (empate: o primeiro) |
| 05 | `repartir_maior_resto(0, [5, 5])` e `(7, [0, 0])` | `[0, 0]` nos dois |
| 06 | Aprovação parcial: só a Torre Quente, sem instalação, cenário A | Total R$ 4.222,75; RT R$ 337,82; tudo recalculado só com ela |
| 07 | Desconto em VALOR igual ao bruto | Total 0; margem_bp 0; sem erro |
| 08 | Desconto em VALOR maior que o bruto | `ValueError` "O desconto não pode ser maior…" |
| 09 | Sinal em VALOR R$ 1.000,00 no cenário A | Sinal R$ 1.000,00; saldo R$ 8.725,15 |
| 10 | Sinal 0 | Saldo = total |
| 11 | Insumo com custo 0 | Aviso `INSUMO_SEM_CUSTO`; cálculo normal |
| 12 | Móvel em HORAS com custo/hora 0 | Aviso `HORAS_SEM_CUSTO_HORA`; mão de obra 0 |
| 13 | Markup 0 e desconto 10% | Aviso `MARGEM_NEGATIVA` |
| 14 | Orçamento sem móveis e sem instalação | Tudo zero; aviso `ORCAMENTO_VAZIO` |
| 15 | Móvel com `quantidade = 0`; insumo com quantidade 0; valor negativo | `ValueError` com as mensagens da §6.6 |
| 16 | RT 30% (limite) no modo PRECO | Calcula sem erro (fator = (1+m)/0,7) |
| 17 | Móvel sem insumos, só terceirizado | Custo = terceirizado; preço = arred(custo × fator) |
| 17a | Revisão 1: cenário B | `desconto_bp_efetivo = 500`; `sinal_bp_efetivo = 4000` |
| 17b | Revisão 1: cenário A com desconto em VALOR R$ 1.000,00 | `desconto_bp_efetivo = arred(100000 / 972515 × 10000) = 1028` |
| 17c | Revisão 1: orçamento vazio | Os dois efetivos = 0 (sem divisão por zero) |

> **Nota da implementação (09/10/2026):** os três cenários batem centavo a centavo com as tabelas acima. Duas validações sem mensagem na §6.6 ganharam uma: modo de desconto/sinal desconhecido ("Forma de desconto ou sinal inválida.") e modo de RT desconhecido ("Modo do RT inválido."). As propriedades 18–25 rodam em **dois** testes que percorrem os 500 orçamentos (e dizem a semente que falhou), para não inflar a contagem da suíte com 600 itens.

### 11.4. Propriedades (geradas aleatoriamente, 500 orçamentos por execução, semente fixa)

| # | Propriedade |
|---|-------------|
| 18 | Σ subtotais dos ambientes + preço da instalação = bruto |
| 19 | total = bruto − desconto ≥ 0 |
| 20 | Σ partes do RT = RT total |
| 21 | margem líquida = total − custo total − RT total |
| 22 | saldo = total − sinal ≥ 0 |
| 23 | Para cada móvel: `custo_os_unit × qtd ≤ custo_unit × qtd + rt_linha`, e a diferença é menor que `qtd` centavos |
| 24 | Mesma entrada, mesma saída (função pura; sem estado entre chamadas) |
| 25 | Trocar a ordem dos ambientes não muda nenhum total (só a ordem das linhas e, em empate, quem recebe o centavo) |

### 11.5. Arquitetura e desempenho

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 26 | Código-fonte de `calculo.py` | Não contém `float(`, `import sqlalchemy`, `from app.db`, `fastapi` |
| 27 | 100 móveis × 30 insumos | Menos de 50 ms |
