# Plano: embalagens do produto (fardo, caixa, DUN-14)

Escrito em 27/09/2026, na branch `etiquetas` (depois da Central de Etiquetas).
É o "plano próprio" prometido na §8 do `etiquetas-plano.md`: vender e receber
um produto em **embalagem fechada** (fardo com 12, caixa com 24) sem perder o
controle da unidade.

**Por que plano separado:** isto não mexe só na etiqueta. Mexe no **PDV** (o
que o leitor bipa), no **estoque** (quanto baixa), na **entrada** (quanto
entra e a que custo) e na **NF-e/NFC-e** (unidade comercial × tributável) de
lojas em produção. Errar aqui baixa estoque errado em silêncio ou faz a SEFAZ
rejeitar nota.

**Nada começa a ser codado antes de as decisões da §4 estarem aceitas.**

> **Status (27/09/2026):** o Alan respondeu as perguntas (§9) pensando no
> primeiro cliente, uma **adega de bebidas**. As respostas entraram nas decisões
> (D14–D20) e trouxeram uma parte nova: as **regras de preço por quantidade**
> (§6.1). Princípio que ele deixou claro: **quem define a regra de venda é o
> dono da loja** — o sistema oferece as opções, a loja liga as que usa.

> **Execução (27/09/2026, branch `embalagens`):** **fases 1 e 2 entregues** —
> ver §13. As fases 3 (venda), 4 (NF-e/NFC-e) e 5 (regras de preço) esperam:
> sobem juntas, com homologação e loja canário.

---

## 0. O que "pronto" significa

| # | Critério de aceite | Hoje |
|---|---|---|
| B1 | Cadastrar no produto "Fardo com 12 — código X" sem criar um produto novo | só dá criando outro produto, com estoque separado |
| B2 | Bipar o código do fardo no PDV lança **1 FD** e baixa **12 UN** | o código do fardo não existe no sistema |
| B3 | Bipar o fardo duas vezes soma na mesma linha ("2 FD"); bipar a unidade vai para outra linha | — |
| B4 | Dar entrada de "3 CX" lança 36 UN, com o custo da caixa dividido pela unidade | a entrada é sempre em unidade |
| B5 | A NF-e da venda do fardo sai com `uCom=FD`, `qCom=1`, `uTrib=UN`, `qTrib=12` — **autorizada** | o payload não envia `qTrib`/`vUnTrib` (§1) |
| B6 | Cancelar ou devolver o fardo devolve **12 UN** ao estoque | — |
| B7 | Imprimir a etiqueta do fardo com o DUN-14 em **ITF-14** e "Contém 12 un" | a etiqueta só conhece o produto |
| B8 | Quem **não** usa embalagem não vê nada mudar — venda, nota e estoque idênticos | cláusula de não-regressão |
| B9 | Bipar 17 latas avulsas de um produto com "fardo de 15 por R$ 50" cobra 1 fardo + 2 unidades — **se o dono ligou essa regra** | não existe |
| B10 | "A partir de 6 un, R$ 3,80 cada" aplicado sozinho no caixa — **se o dono ligou** | o preço de atacado existe no cadastro, mas a venda não usa |
| B11 | Fardo sem código do fornecedor ganha código interno e etiqueta pela Central de Etiquetas | — |
| B12 | NF-e **e** NFC-e com fardo autorizadas em homologação | — |

B8 é a mais importante: nenhuma venda antiga e nenhum produto sem embalagem pode
mudar de comportamento. Tudo novo nasce com `fator = 1`.

---

## 1. Como está hoje (27/09/2026)

| Onde | O que existe | O que falta para embalagem |
|---|---|---|
| `db/models/produto.py` | **um** `codigo_barras`, `unidade_medida` | lista de embalagens com código e fator |
| `db/models/produto_fiscal.py` | `gtin_tributavel`, `unidade_tributavel` | — (já é o lado "unidade" da nota) |
| `db/models/estoque.py` | `quantidade` (**float**), `custo_medio` por unidade | — (continua em unidade base) |
| `db/models/venda_produto.py` | `quantidade` (**inteiro**), `valor_unitario`, `custo_unitario` congelados | saber que a linha é "FD × 12" |
| `db/models/orcamento_produto.py` | igual à venda | idem |
| `services/produto.py` → `decrease_product_in_stock` / `restore_product_to_stock` | baixa e devolve `quantidade` | multiplicar pelo fator |
| `sales/leitorCodigoBarras.util.ts` | código exato em `codigo_barras` **ou** `sku` | procurar também nos códigos de embalagem |
| `sales/composables/flows/useProductSearch.ts` | bipar de novo **soma na linha do mesmo produto** | somar na linha da mesma **embalagem** |
| `services/fiscal/payload_builder.py` | `cEAN` = `cEANTrib` quase sempre; `uTrib` cai para `uCom`; **não envia `qTrib`/`vUnTrib`** (o comentário em `validators.py` assume uTrib = uCom) | enviar `qTrib` e `vUnTrib` quando a linha é embalagem |
| `services/fiscal/snapshot.py` / devolução | congela a unidade comercial do item | congelar também o fator |
| `MovimentacaoModal.vue` (entrada) | quantidade + custo por unidade | escolher a embalagem |
| Central de Etiquetas | fonte `produto`; ITF-14 já sai para 14 dígitos | fonte `embalagem` (reservada na §8 do plano de etiquetas) |

O preço de atacado (`estoque.valor_atacado`) existe no cadastro mas **nenhuma
venda usa** — não serve de atalho para "preço do fardo".

---

## 2. As regras de fora (fiscal e GS1)

- **DUN-14 / GTIN-14** identifica a embalagem com várias unidades iguais e é
  impresso em **ITF-14**.
- **`cEAN`** (GTIN da unidade comercial) aceita GTIN-8/12/13/**14** — o DUN-14
  do fardo vai aqui.
- **`cEANTrib`** (GTIN da unidade tributável) é o da **menor unidade vendida no
  varejo**: GTIN-8/12/13, **nunca GTIN-14**. Exemplo clássico: caixa de 12
  leites → `cEAN` = GTIN-14 da caixa, `cEANTrib` = GTIN-13 do litro.
- **Os dois andam juntos:** informar um sem o outro é rejeição (**885/886**).
  Quando a unidade comercial e a tributável são diferentes, os códigos também
  são diferentes.
- **`qCom × vUnCom = vProd`** (rejeição **629**) e **`qTrib × vUnTrib = vProd`**
  (rejeição **630**). Erro clássico: vender em caixa e repetir a quantidade da
  caixa em `qTrib`, sem converter para a unidade.
- **GTIN tem de existir no Cadastro Centralizado de GTIN** (rejeição **894**).
  Dígito verificador certo não basta: um "DUN-14" inventado pela loja, com
  checksum válido, é rejeitado.

Como o mercado faz: Bling e Tiny separam GTIN e GTIN tributável e calculam
`qTrib`/`vUnTrib` pelo **fator de conversão** do produto; WK e Conta Azul
chamam de "taxa/fator de conversão" entre a unidade de compra/venda e a do
estoque. É o mesmo desenho deste plano. O detalhe por sistema está na §2.1.

### 2.1 O que os sistemas profissionais já usam (pesquisa de 27/09/2026)

| Sistema | Como resolve | O que aproveitamos |
|---|---|---|
| **Winthor (TOTVS)** — referência em distribuição e atacarejo | Cadastro de **embalagens por produto** (rotinas 2014/292): cada uma com **quantidade (fator)**, **código auxiliar** (código de barras da embalagem), **descrição PDV** e preço. Preço da embalagem de três jeitos: **preço próprio**, **"fator preço"** (1,05 = +5%, 0,95 = −5% sobre a unidade) ou **atacado por quantidade** ("Qt. mínima atacado" + "Pr. venda atacado"). Opção de **gerar o código da embalagem automaticamente** quando o fornecedor não manda, e de **validar EAN-13/EAN-8/DUN-14**. No caixa, a conversão segue o código bipado: bipou a caixa, usa o fator da caixa. | É o desenho deste plano (D2, D5, D6, D7). O "fator preço" e o código gerado entram como perguntas (§9). |
| **TOTVS Supermercados (Consinco/RMS)** — frente de caixa | Reconhece preço de **embalagem fechada**, com valor diferente no pack ou na unidade. | Confirma D5 (preço próprio da embalagem). |
| **Bling** | "Variação composta": o kit com 2 ou 10 consome o estoque da unidade; campo "Itens por caixa". | Mesmo princípio de D1 (estoque na unidade), mas como kit — pensado para e-commerce, não para o leitor do caixa. |
| **Sistemas de adega/distribuidora** (SisFood, Nex, DistribuidorPro, MBM…) | Venda por **unidade e fardo** com **preço atacado/varejo automático**, **estoque pela XML de compra**, **combos** (cerveja + gelo) e **vasilhame retornável**. | Unidade/fardo é este plano. XML de compra, combo e vasilhame são planos próprios (§8). |
| **PDVs de atacarejo** (ex.: Datacaixa) | **Preço por quantidade:** "a partir de N unidades, cada uma sai por X", aplicado sozinho no caixa. | É o caso "bipou 12 latas avulsas" — pergunta 2 da §9. |

---

## 3. A ideia

```
Produto: Refrigerante 2L        unidade base: UN   código: 7891000100103 (EAN-13)
 ├── Embalagem: FD  "Fardo com 6"    fator 6    código: 17891000100100 (DUN-14)   preço: R$ 51,00
 └── Embalagem: CX  "Caixa com 24"   fator 24   código: 27891000100107 (DUN-14)   preço: (6 × fardo)

Estoque: 120 UN   (a tela pode mostrar "120 un · 20 FD")
```

- O **estoque é sempre na unidade base**. Embalagem é só uma forma de vender
  e de receber.
- Uma venda de "2 FD" é **uma linha com quantidade 2 e fator 6**: o cupom e a
  nota mostram "2 FD", o estoque baixa 12 UN.
- **Um nível só** (embalagem → unidade). Palete de caixas fica de fora (§8).

---

## 4. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | **Estoque, custo médio e CMV continuam na unidade base.** | Um lugar só para a verdade. Estoque "em fardos" e "em unidades" ao mesmo tempo nunca fecha. |
| D2 | **Tabela nova `produto_embalagens`**, filha do produto (não um produto novo). | Produto novo por embalagem é o que as lojas fazem hoje por falta de opção — e é o que separa o estoque. |
| D3 | **Fator inteiro ≥ 1.** Fator **1** é um **código de barras adicional da unidade** (ver A1, §11); fator ≥ 2 é embalagem de verdade. | Cobre fardo, caixa, pacote, display — e o produto com dois EANs. Fator decimal (caixa de piso com 2,5 m²) muda o tipo de `venda_produto.quantidade` (inteiro) e fica para depois (§8). |
| D4 | **O código de barras é único no sistema inteiro** — embalagem não pode repetir código de produto, SKU nem outra embalagem. | O PDV recusa código ambíguo (`leitorCodigoBarras.util.ts`); a colisão viraria "não achei" no caixa. |
| D5 | **Preço da embalagem opcional.** Vazio = fator × preço da unidade. | Fardo costuma ser mais barato por unidade; mas obrigar preço em toda embalagem é mais um campo para esquecer desatualizado. |
| D6 | **A linha da venda congela embalagem e fator** (`embalagem_id`, `fator_embalagem`, sigla). Linhas antigas ficam com `fator = 1`. | Mudar o fator do cadastro amanhã não pode reescrever a baixa, a devolução nem a nota de ontem — mesma regra do `custo_unitario` congelado. |
| D7 | **Bipar a mesma embalagem soma na linha dela**; unidade e fardo do mesmo produto são **linhas diferentes**. | Hoje soma por `produto_id` (`useProductSearch.ts`). "3 UN + 1 FD" numa linha só esconderia o que o cliente levou. |
| D8 | **NF-e/NFC-e de linha com embalagem:** `cEAN` = código da embalagem, `uCom` = sigla, `qCom` = qtd de embalagens, `vUnCom` = preço da embalagem; `cEANTrib` = GTIN da **unidade**, `uTrib` = unidade base, `qTrib` = qCom × fator, `vUnTrib` = vProd ÷ qTrib. | É a regra do §2. Linha sem embalagem continua exatamente como hoje (B8). |
| D9 | **Se a embalagem ou a unidade não tiver GTIN válido, os dois vão como "SEM GTIN".** | 885/886: um sem o outro é rejeição. Mandar o DUN e deixar a unidade sem GTIN recusaria a nota. |
| D10 | **Entrada por embalagem:** "3 CX a R$ 120,00 a caixa" → +72 UN a R$ 5,00. | É assim que a nota do fornecedor chega; converter de cabeça é onde o custo médio se perde. |
| D11 | **OS continua em unidade.** Orçamento ganha embalagem junto com a venda. | OS vende peça solta; orçamento vira venda e precisa carregar a embalagem. |
| D12 | **Relatório de quantidade vendida soma na unidade base** (qtd × fator); faturamento e comissão não mudam (são por valor). | "Vendeu 3" sem dizer 3 o quê é pior que não dizer. |
| D13 | **Etiqueta:** fonte `embalagem` na Central (produto + tipo, "Contém 12 un", código da embalagem, preço da embalagem). O DUN-14 sai em ITF-14 pela simbologia automática que já existe. | Fecha o B7 e a §8 do plano de etiquetas. |
| D14 | **Preço próprio por embalagem**, com a sugestão "fator × unidade" já preenchida. *(resposta 1)* | É o que o caixa e o dono entendem; o Winthor e a frente de caixa TOTVS fazem assim. |
| D15 | **A quantidade da embalagem é a de cada produto** (6, 12, 15, 24…), nunca fixa. | Cada fornecedor monta o fardo de um jeito. |
| D16 | **As regras de preço por quantidade entram NESTE plano, como opções que o dono liga** (§6.1). *(resposta 2)* | "Quem dita a regra de venda é quem está vendendo." |
| D17 | **O que vale quando duas regras servem é escolha do dono** (menor preço ao cliente, ou uma ordem de prioridade que ele define). Padrão ao ligar: menor preço. *(resposta ao conflito)* | Idem. O padrão é o que evita reclamação no balcão enquanto ele não escolhe. |
| D18 | **Fardo sem código do fornecedor ganha código interno** (EAN-13 de uso interno, prefixo 2), com etiqueta impressa pela Central. Na nota sai **"SEM GTIN"** — código interno não está no Cadastro Centralizado. *(resposta 3)* | O Winthor gera o código da embalagem quando o fornecedor não manda; sem código, o fardo volta a ser digitado à mão. |
| D19 | **NF-e e NFC-e ficam prontas juntas** (fase 4 cobre as duas). *(resposta 4)* | A adega vende no balcão (NFC-e) e para CNPJ (NF-e). |
| D20 | **Sem quantidade quebrada** (meio fardo, granel): a quantidade da venda continua inteira. *(resposta 5)* | Mantém o tipo de `venda_produto.quantidade` e o risco baixo. |
| D21 | **Estoque em unidade, com o fardo discreto no card** ("120 un" em destaque; "= 10 FD" pequeno, em cinza). *(resposta 7)* | É o que os grandes fazem: o saldo vive na unidade (Winthor, Omie, Bling) e a embalagem aparece como conversão. |

---

## 5. Modelo de dados

```
produto_embalagens
├── id
├── produto_id          FK produtos (CASCADE)
├── sigla               String(6)   "FD", "CX", "PCT", "DP"   → vai no uCom da nota
├── descricao           String(60)  "Fardo com 12"             → cupom, PDV, etiqueta
├── fator               Integer ≥ 2
├── codigo_barras       String(20)  único no sistema (D4), opcional
├── preco               Integer (centavos), nulo = fator × preço da unidade (D5)
├── vende_no_pdv        Boolean  — aparece e é bipável no caixa (A2)
├── usa_na_entrada      Boolean  — oferecida na entrada de estoque (A2)
├── aplica_as_avulsas   Boolean  — regra R1 da §6.1
├── peso_kg             Decimal, opcional — alimenta a etiqueta de envio (A5)
├── ativo               Boolean
└── datas

produtos           + so_embalagem_fechada (Boolean, default falso) — A3

venda_produto      + embalagem_id (FK, nulo) + fator_embalagem (int, default 1) + sigla_embalagem (nulo)
orcamento_produto  + os mesmos três
documento_fiscal_item (snapshot da nota) + fator_embalagem (default 1)
```

`quantidade`, `valor_unitario` e `custo_unitario` da linha continuam como hoje,
mas **na embalagem**: 2 FD a R$ 51,00, custo = custo médio × 6. A baixa é
`quantidade × fator_embalagem`.

**Migrações** (regra do CLAUDE.md): a tabela nova decide pela ausência da
tabela; as colunas novas decidem pela **ausência da coluna** e nascem com
`fator_embalagem = 1` — toda linha antiga continua significando exatamente o
que significava. Nenhum dado existente é reescrito.

---

## 6. Fluxos

**Cadastro** — seção "Embalagens" no formulário de produto: sigla, descrição,
fator, código (com a mesma validação de EAN/DUN da etiqueta: dígito verificador
e aviso se não bater), preço opcional com a sugestão "6 × R$ 8,90 = R$ 53,40".

**PDV** — o leitor procura o código em produto, SKU **e** embalagem. Achou
embalagem: lança a linha "1 FD" com o preço da embalagem. A regra de estoque
(permitir ou não vender sem saldo) compara `qtd × fator` com o saldo em unidade.

**Finalizar / cancelar / reabrir venda** — `decrease_product_in_stock` e
`restore_product_to_stock` passam a receber a quantidade já convertida
(`qtd × fator`). É o ponto mais sensível: todo lugar que chama essas funções
precisa converter, ou o estoque fica errado em silêncio.

**Entrada** — o `MovimentacaoModal` ganha "em: UN | FD (6) | CX (24)"; converte
quantidade e custo antes de chamar o registro central.

**NF-e / NFC-e** — D8 e D9 no `payload_builder`; o validador fiscal passa a
conferir `qTrib × vUnTrib = vProd` antes de mandar (rejeição 630 nunca chega à
SEFAZ). Devolução usa o fator congelado no snapshot.

**Etiqueta** — fila aceita "produto + embalagem"; "Etiqueta" no card do produto
pergunta qual (unidade ou fardo) quando houver embalagens.

### 6.1 Regras de preço por quantidade (o dono escolhe)

Três mecanismos, os mesmos dos PDVs profissionais. **Todos nascem desligados**;
o dono liga em *Configurações › Regras de Vendas* (vale para a loja) e ajusta
em cada produto. Quem não liga nada vende exatamente como hoje (B8).

| Regra | Como funciona | Onde se configura | Quem já usa |
|---|---|---|---|
| **R1 — Embalagem por múltiplo** | Avulsas que completam a quantidade de uma embalagem cobram o preço dela; o resto fica na unidade. Fardo de 15 por R$ 50: 17 latas = 1 × R$ 50 + 2 × unidade. As **linhas continuam UN** e o estoque baixa 17 — só o preço muda. | Liga na loja; em cada embalagem, "aplicar às avulsas" (sim/não) | Winthor (preço entre embalagens), frente de caixa TOTVS (pack) |
| **R2 — Faixas "a partir de N"** | Preço por unidade escalonado, com várias faixas por produto: a partir de 6 un = R$ 3,80; a partir de 24 un = R$ 3,50. | Liga na loja; faixas no produto | TOTVS Supermercados ("Preço a partir de"), Omie.PDV, Datacaixa, atacarejos |
| **R3 — Leve X, pague Y** | Promoção com **data de início e fim**: leve 3, pague 2 (o item de menor valor sai de graça). | Liga na loja; promoção no produto, com vigência | TOTVS Supermercados ("Leve X Pague Y"), VTEX |

**Quando mais de uma serve** (D17): o dono escolhe na mesma tela —
*"cobrar o menor preço ao cliente"* (padrão) ou *"seguir esta ordem"* (ele
arrasta R1, R2, R3). O caixa **mostra na linha qual regra aplicou** ("preço de
fardo", "a partir de 6", "leve 3 pague 2") — sem isso, preço que muda sozinho
vira discussão no balcão.

**Regras que valem para as três:**
- O preço é recalculado a cada item bipado, e a linha mostra o preço cheio
  riscado quando a regra baixou o valor.
- **Desconto manual do operador** continua existindo e é aplicado **depois** da
  regra (a tela de Regras de Vendas pode proibir desconto manual em item com
  regra ativa — a TOTVS tem essa trava).
- **O que foi aplicado fica congelado na linha** (regra, preço de referência),
  pela mesma razão de D6: mudar a regra amanhã não reescreve a venda de hoje.
- **Na nota**, o preço já com a regra vai como `vUnCom`; a diferença não vira
  desconto (`vDesc`) — é preço praticado. O "leve 3 pague 2" é a exceção: o item
  gratuito sai como **desconto** na linha, que é o jeito aceito pela SEFAZ de
  dizer "levou 3, pagou 2".
- **Comissão e relatórios** usam o valor efetivamente cobrado.

---

## 7. Fases

| Fase | Entrega | Risco |
|---|---|---|
| **1. Cadastro + etiqueta** | Tabela, API, seção no formulário, unicidade do código, código interno (D18), códigos adicionais (A1), fonte `embalagem` e preço duplo na Central de Etiquetas (A6) | Baixo: nada vende nem baixa ainda |
| **2. Entrada por embalagem** | Movimentação de entrada em FD/CX, custo convertido | Médio: custo médio |
| **3. Venda e orçamento** | PDV bipa a embalagem, linha por embalagem, baixa/cancelamento/reabertura por fator | **Alto**: estoque de lojas em produção |
| **4. NF-e e NFC-e** | uCom/uTrib/qTrib/vUnTrib, cEAN/cEANTrib, validação 629/630/885/886, devolução | **Alto**: rejeição na SEFAZ |
| **5. Regras de preço por quantidade** (§6.1) | R1, R2 e R3 como opções do dono, com a escolha do que vale no conflito e a linha mostrando a regra aplicada | **Alto**: preço no caixa |
| **6. Relatórios** | Quantidade vendida na unidade base; vendas por regra de preço | Baixo |

**As fases 3 e 4 sobem juntas para as lojas que emitem nota** — e a adega emite
NF-e e NFC-e (D19): vender fardo sem a nota saber do fator é exatamente o erro
clássico do §2. A fase 5 pode vir logo depois: ela só mexe no preço, não no
estoque nem na unidade da nota.

**Liberação:** homologação primeiro (testar 629/630/885/886/894 de propósito),
depois **uma loja canário com backup** antes de todas.

---

## 8. Fora de escopo (por enquanto)

- **Embalagem de embalagem** (palete de caixas): um nível só (D3).
- **Fator decimal** (caixa de piso com 2,5 m², rolo com 50 m): exige mudar
  `venda_produto.quantidade` de inteiro para decimal.
- **OS vendendo embalagem** (D11).
- **Gerar DUN-14** para a loja: o DUN precisa estar no Cadastro Centralizado
  de GTIN (rejeição 894) — quem gera é o fabricante na GS1. (Um código
  **interno** só para o leitor do caixa é outra coisa — pergunta 3 da §9.)
- **Entrada pela XML da nota do fornecedor** (o que os sistemas de adega vendem
  como "estoque por XML"): a nota já traz o DUN, a caixa e o `qTrib`, e é o que
  mais poupa digitação numa adega. Plano próprio — depende deste.
- **Vasilhame retornável** (casco de 600 ml/litrão, engradado): controle de
  casco emprestado/devolvido. Plano próprio, se a adega usar.
- **Combo** (cerveja + gelo, kit festa): produto composto que baixa vários
  produtos. Plano próprio.

---

## 9. Respostas do Alan (27/09/2026) — primeiro cliente: adega de bebidas

| # | Pergunta | Resposta | Virou |
|---|---|---|---|
| 1 | Como a adega cobra o fardo? | **Preço próprio** | D14 |
| 2 | 12 latas avulsas viram preço de fardo sozinhas? | **Sim, já nesta entrega** — e a quantidade é a de cada produto, não 12 fixo | D15, D16, §6.1 (R1) |
| 3 | Fardo sem código: gerar código interno? | **Sim** | D18 |
| 4 | A adega emite nota? | **NF-e e NFC-e — deixar as duas prontas** | D19 |
| 5 | Vende quantidade quebrada? | **Não** | D20 |
| 6 | Próximos planos | **Entrada pela XML, vasilhame retornável e combo/kit** — pensados para **PDV em geral**, não só adega, com as opções completas | §10 |
| 7 | Fardo na tela do estoque? | **Como os grandes fazem, discreto no card** | D21 |
| — | Quais regras de preço entram? Qual vale no conflito? | **"Quem dita a regra é quem está vendendo"; "a forma de venda quem sabe é o dono"** | D16, D17: as três regras como **opções do dono**, e ele escolhe o que vale no conflito |

**Não há mais pergunta que trave a implementação.** O que falta decidir é do
dono de cada loja, na tela de configuração.

---

## 10. Próximos planos (pedido do Alan: servir a qualquer PDV)

Ficam fora deste, cada um com plano próprio, e todos pensados para o varejo em
geral — a adega é o primeiro caso, não o único:

1. **Entrada pela XML da nota do fornecedor** — lê a NF-e de compra (arquivo ou
   chave), casa cada item com o produto pelo GTIN/DUN (ou pelo código do
   fornecedor, aprendido na primeira vez), converte caixa em unidade pelo fator
   da embalagem (este plano), atualiza custo e estoque. É o que os sistemas de
   adega e o Omie vendem como "recebimento da NF-e".
2. **Combo / kit** — um item de venda que baixa vários produtos (cerveja + gelo,
   cesta, kit festa), com preço próprio e a nota discriminando os itens.
3. **Vasilhame retornável** — casco e engradado emprestados e devolvidos por
   cliente, com saldo por cliente e cobrança do casco não devolvido.

---

## 11. O plano × o mercado (revisão de 27/09/2026)

Cruzamento do plano com o que os sistemas profissionais pesquisados fazem
(§2.1 e §6.1). **Onde o plano já está no padrão**, **onde o mercado vai além**
e **o que ajustei** por causa disso.

### 11.1 Já no padrão

| Recurso | Mercado | Plano |
|---|---|---|
| Embalagens dentro do produto, com fator, código e preço | Winthor (rotinas 2014/292), frente de caixa TOTVS | D2, D5, D14 |
| Estoque sempre na unidade, embalagem como conversão | Winthor, Omie, Bling | D1, D21 |
| O código bipado decide a embalagem no caixa | Winthor (conversão pelo código lido) | D7, §6 |
| Validar EAN-13/EAN-8/DUN-14 no cadastro | Winthor ("validar código auxiliar") | §6 (cadastro) |
| Gerar código para embalagem sem código do fornecedor | Winthor ("gerar código auxiliar automático") | D18 |
| Nota com `uCom`/`uTrib`/`qTrib`/`vUnTrib` calculados pelo fator | Omie, Bling, WK | D8, D9 |
| Preço "a partir de N" e "leve X pague Y" | TOTVS Supermercados, Omie.PDV, Datacaixa | §6.1 (R2, R3) |
| Travar desconto manual em item com regra de preço | TOTVS Supermercados PDV 24.01 | §6.1 |
| Congelar na venda o que foi aplicado | prática geral (custo e preço congelados) | D6, §6.1 |

**Vantagem do desenho sobre o Winthor:** lá existe uma rotina de "conversão de
estoque entre produto pai e filho", para quando o fardo e a unidade viram
estoques separados. Aqui isso não é necessário: o estoque nunca se divide (D1).

### 11.2 Onde o mercado vai além — e o ajuste no plano

| # | O mercado faz | Quem | Ajuste |
|---|---|---|---|
| **A1** | **Vários códigos de barras para a mesma unidade** (o mesmo refrigerante com EAN de duas fábricas, embalagem nova do fabricante) | Winthor ("códigos auxiliares") | Embalagem com **fator 1** vira código adicional da unidade (D3 mudou de "≥ 2" para "≥ 1"). Resolve o "bipei e não achou" com código novo do fabricante, sem cadastrar produto novo. Na nota, fator 1 = unidade: nada muda. |
| **A2** | **Embalagem de compra ≠ embalagem de venda** (compra em caixa de 24, vende em fardo de 12 e unidade) | Winthor ("unidade de compra master" × unidade de venda) | Cada embalagem ganha **"vende no PDV"** e **"usa na entrada"**. A caixa de 24 do fornecedor pode existir só para a entrada. |
| **A3** | **Vender só em múltiplo da embalagem** (distribuidora que não abre fardo) | Winthor ("Qt. múltipla") | Opção no produto **"só vende embalagem fechada"**: o caixa recusa a unidade avulsa daquele produto. Desligada por padrão. |
| **A4** | **Preço da embalagem por percentual** sobre a unidade ("fator preço") | Winthor | Fica como **alternativa** ao preço próprio (D14): no cadastro, "preço fixo" ou "X% sobre a unidade". O dono escolhe (D16). |
| **A5** | **Peso e dimensões por embalagem** | Winthor, Bling ("itens por caixa", volumes) | **Peso opcional** na embalagem; a etiqueta de envio soma o peso dos volumes sozinha. Dimensões ficam para quando houver cálculo de frete. |
| **A6** | **Etiqueta de gôndola com dois preços** (unidade e fardo/atacado) | VR (modelos de gôndola com vários preços), atacarejos | Campos novos na Central de Etiquetas: **preço do fardo**, **preço "a partir de N"** e **preço por unidade dentro do fardo** ("R$ 3,33 a lata"). |
| **A7** | **O mesmo produto chega em embalagens diferentes conforme o fornecedor** | Winthor ("entrada de produto com fornecedores de diferentes embalagens") | Entra no plano da **entrada pela XML** (§10.1): o casamento "item do fornecedor → embalagem" é aprendido por fornecedor. |
| **A8** | **Centenas de regras de preço combináveis** | TOTVS Supermercados (~450 regras) | **Não seguimos.** Três regras (§6.1) cobrem o varejo pequeno e médio; um motor de promoções é outro produto. Registrado para não virar escopo escondido. |

### 11.3 O que o mercado tem e continua fora (de propósito)

- **Motor de promoções completo** (A8), **cashback** e **clube de fidelidade**.
- **Balança** (código de peso variável no EAN com prefixo 2): a loja com balança
  usa a mesma faixa de código de D18. **Antes de implementar D18, conferir se o
  PDV já lê código de balança** — os dois não podem colidir.
- **Dimensões e cálculo de frete** (A5).

---

## 12. Auditoria de cobertura (27/09/2026)

Pergunta do Alan: *"tem certeza que contemplou todas as áreas?"*. Resposta
honesta: **não tinha**. O plano nasceu olhando PDV, estoque, entrada, nota e
etiqueta; faltava varrer o código inteiro. A varredura procurou todo arquivo que
usa item de venda/orçamento (quantidade, custo, preço unitário) ou código de
barras/unidade do produto — **42 arquivos no backend e 23 telas/impressões no
frontend** — e comparou com o plano.

### 12.1 Áreas e situação

| Área | Onde (principais) | Situação |
|---|---|---|
| Cadastro do produto | `produto.py`, `useProductForm.ts`, `DadosProdutoSection` | coberto (§6) |
| Busca e leitor no PDV | `leitorCodigoBarras.util.ts`, `useProductSearch.ts`, `crud/produto.py` | coberto (§6, D7) |
| **Adicionar produto à mão** (sem leitor) | `AddProductModal.vue`, `ProductOption.vue`, `useItemSaleForm.ts` | **faltava → G1** |
| Linha da venda e totais | `venda_produto.py`, `schemas/vendas.py`, `SaleItemsTable.vue` | coberto (D6) |
| **Aviso de estoque negativo** | `AvisoEstoqueNegativoModal.vue`, `services/venda.py` | citado de passagem → **G2** |
| Baixa, cancelamento e reabertura | `services/produto.py` (`decrease/restore_product_in_stock`), `services/venda.py` | coberto (§6) |
| Orçamento e **conversão em venda** | `services/orcamento.py` (`converter_orcamento` copia os itens) | citado → **G3** |
| **Impressões da venda** | `SalePrintCupom.vue`, `SalePrintTemplate.vue`, `saleToEscPos.ts`, `nfceToEscPos.ts` | **faltava → G4** |
| Entrada de estoque | `MovimentacaoModal.vue`, `movimentacao_estoque.py` | coberto (D10) |
| **Ajuste de inventário** (contagem) | movimentação `AJUSTE` = quantidade final contada | **faltava → G5** |
| **CMV e comissão sobre lucro** | `crud/relatorio_custo.py` (Σ quantidade × custo congelado), `crud/relatorio.py` | implícito → **G6** |
| Relatórios de quantidade e estoque | `crud/relatorio.py`, `EstoqueSection.vue`, `dashboard.py`, `EstoqueBaixoTable.vue` | coberto (D12, D21) |
| NF-e/NFC-e: payload, validação, pendências | `payload_builder.py`, `validators.py`, `verificacao_fiscal.py`, `campos_produto.py` | coberto (D8, D9) |
| **Motor de impostos** | `tax_engine/resolver.py` (usa quantidade × valor unitário por item) | **faltava → G7** |
| **Emissão de NF-e a partir da venda e correção** | `FiscalEmitirNFeModal.vue`, `FiscalEditarVendaModal.vue`, `FiscalDocumentoDetailsDrawer.vue` | **faltava → G8** |
| Devolução | `devolucao.py`, `snapshot.py`, `FiscalEmitirDevolucaoModal.vue`, `useDevolucaoItens.ts` | coberto (D6, §6) |
| OS | `ordem_servico_item.py`, `adaptador_os.py` | fora, de propósito (D11) |
| Central de Etiquetas | fila, **Entradas recentes**, envio | parcial → **G9** |
| **Liga/desliga do recurso** | Configurações › Produtos e Estoque | **faltava → G10** |
| Permissões | cargo "Produtos" (cadastro), Configurações (regras de preço) | **faltava → G11** |
| Backup em nuvem | `services/cloud` (copia o banco inteiro) | sem impacto: a tabela nova vai junto |
| Leitor de balança | — (não existe hoje no PDV) | sem conflito hoje com D18; ver §11.3 |

### 12.2 Lacunas encontradas e como ficam

| # | Lacuna | Como fica no plano |
|---|---|---|
| **G1** | O modal "adicionar produto" e a lista de opções do PDV só conhecem o produto | Produto com embalagens abre a escolha **UN / FD 12 / CX 24** (com preço de cada); sem embalagem, nada muda. **Fase 3.** |
| **G2** | O aviso de estoque negativo compara quantidade da linha com o saldo | Compara **quantidade × fator** com o saldo, e a mensagem fala em unidade e em fardo ("faltam 8 un, menos de 1 FD"). **Fase 3.** |
| **G3** | A conversão de orçamento em venda copia os itens campo a campo | Copia também embalagem, fator e sigla — senão o orçamento "2 FD" vira venda "2 UN" em silêncio. **Fase 3.** |
| **G4** | Cupom, via A4 e as duas impressões ESC/POS mostram quantidade e unidade do produto | Mostram a **sigla da embalagem** ("2 FD") e, embaixo, "(24 un)" em letra menor. **Fase 3.** |
| **G5** | O ajuste de inventário recebe a contagem só em unidade | A contagem aceita **fardos + unidades** ("10 FD + 3 un" = 123 un). **Fase 2.** |
| **G6** | CMV e comissão sobre lucro calculam **quantidade × custo congelado** da linha | Regra explícita: a **linha da venda guarda o custo da embalagem** (custo médio × fator); a **movimentação de estoque fica sempre em unidade, com custo por unidade**. Assim as duas contas continuam certas sem mudar os relatórios. Teste de CMV com venda de fardo. **Fase 3.** |
| **G7** | O motor de impostos calcula item a item com quantidade × valor unitário | Recebe a linha **na embalagem** (quantidade de fardos × preço do fardo): o total é o mesmo. Para o `qTrib` da nota, a conversão fica no payload (D8). **Ponto a confirmar com o contador da adega:** bebida quase sempre tem **ICMS-ST**; se a adega compra com ST retida, a venda não calcula ST e nada muda; se algum estado cobrar ST por **pauta/PMPF por unidade**, o motor precisaria usar `qTrib` — hoje ele não tem pauta. **Fase 4.** |
| **G8** | Emitir NF-e a partir da venda e a correção fiscal da venda editam os itens | Mostram e preservam embalagem e fator; a correção não pode trocar "2 FD" por "2 UN". **Fase 4.** |
| **G9** | "Entradas recentes" da Central de Etiquetas conta etiquetas em unidade | Entrada de "3 CX" oferece **3 etiquetas de caixa ou 72 de unidade**. **Fase 2.** |
| **G10** | O recurso aparece para todo mundo | **"Usar embalagens (fardo/caixa)"** em Configurações › Produtos e Estoque, **desligado por padrão**. Desligado, nem a seção do cadastro aparece — é o que garante o B8 na tela, não só no banco. **Fase 1.** |
| **G11** | Não estava dito quem mexe em quê | Cadastrar embalagem: permissão de **Produtos**. Ligar as regras de preço (§6.1): permissão de **Configurações**. Etiqueta de fardo: linha **Etiquetas**. **Fase 1.** |

**O que ainda pode estar faltando:** a varredura foi por nome de campo. Um
cálculo que use a quantidade sem citar esses nomes (uma soma montada em SQL
bruto, por exemplo) escaparia. Por isso cada fase fecha com um **teste de
ponta a ponta com fardo** — vender, cancelar, devolver, emitir — e não só com
os testes da parte alterada.

---

## 13. Entrega das fases 1 e 2 (27/09/2026)

Tudo atrás da chave **"Vender e receber em fardo, caixa ou pack"**
(Configurações › Produtos e Estoque), **desligada por padrão**. Desligada, o
sistema fica exatamente como antes — cadastro, card, estoque e etiquetas.

**Fase 1 — cadastro e etiqueta**
- Tabela `produto_embalagens` e `GET/PUT /produtos/{id}/embalagens`
  (replace-all, permissão de Produtos); as embalagens voltam na leitura do produto.
- Código **único no sistema inteiro** (produto, SKU, outras embalagens); o
  produto também não pode usar o código de uma embalagem.
- **Código interno** para fardo sem código: EAN-13 com prefixo **29** (faixa
  restrita GS1), pelo id — o "29" fica longe do "2" + código que as balanças
  usam (§11.3).
- Seção **Embalagens** no produto (só em edição), componente independente do
  formulário, fora do `<form>` (Enter num campo dela não salva o produto).
- Card do estoque com **"= 10 FD"** discreto.
- Central de Etiquetas: cada linha escolhe **Unidade / FD / CX**; etiqueta do
  fardo com código, preço e nome dele; **fardo sem código nunca imprime o
  código da unidade**.

**Fase 2 — entrada e inventário**
- Entrada em embalagem: "3 CX a R$ 120,00" → **72 un a R$ 5,00** no registro
  central, que continua recebendo unidade (custo médio e CMV intactos — G6).
  A movimentação guarda sigla, fator e quantidade de embalagens, congelados.
- Ajuste de inventário contando **"10 FD + 3 un"**.
- Histórico mostra "(3 CX de 24)"; Entradas recentes das etiquetas oferecem a
  etiqueta da embalagem (padrão continua unidade).

**Migrations:** `a0b1c2d3e4f5` (tabela + chave) e `e7b2c9d41f60` (colunas da
movimentação), só criam o que falta; nada existente é reescrito. (A segunda
nasceu com um id que já existia — `b1c2d3e4f5a6`, da cor do tema — e o Alembic
acusou ciclo; renomeada antes do commit.)

**Regressão:** a suíte INTEIRA do backend rodou num banco temporário
(`DATABASE_URL` apontado para a pasta de rascunho — a fixture padrão sobe o app
contra o banco real): **1792 passam; 17 falham, e as mesmas 17 já falhavam no
código de antes das etiquetas** (`test_emissao_ponta_a_ponta.py` — pendência
"numeração confirmada" — e `test_inutilizacao_recusa_local.py`). Nenhuma
regressão das embalagens. Frontend: 121 testes, `vue-tsc` e build limpos.

---

## Fontes

- TOTVS Varejo Supermercados PDV 24.01 (trava de desconto em item com regra de incentivo): <https://produtos.totvs.com/totvs-varejo-supermercados-pdv/varejo/totvs-varejo-supermercados-pdv-24-01/>
- Winthor — unidade de venda × unidade de compra master, e fornecedores com embalagens diferentes: <https://centraldeatendimento.totvs.com/hc/pt-br/articles/360026400192-WINT-Qual-a-diferen%C3%A7a-de-unidade-de-vendas-para-unidade-de-compra-master>, <https://centraldeatendimento.totvs.com/hc/pt-br/articles/360028355671-WINT-O-que-fazer-para-realizar-entrada-de-um-produto-com-fornecedores-de-diferentes-embalagens>
- VR Software — modelos de etiqueta de gôndola com vários preços: <https://vrsystem.info/publico/post/layout-de-etiquetas-modelos/8befdc57-ea95-4ce1-92db-bfb54a212206>
- TOTVS Varejo Supermercados PDV — "Preço a partir de": <https://tdn.totvs.com/pages/releaseview.action?pageId=806777930>
- TOTVS Varejo Supermercados — "Leve X Pague Y": <https://centraldeatendimento.totvs.com/hc/pt-br/articles/4411287331223-Varejo-Supermercados-Cadastro-Como-configurar-pre%C3%A7o-promocional-do-tipo-pague-x-leve-y>
- Omie.PDV — preço de atacado: <https://ajuda.omie.com.br/pt-BR/articles/8627615-omie-pdv-configurando-o-preco-de-atacado-no-omie-pdv>
- Winthor — conversão da embalagem master na entrada: <https://centraldeatendimento.totvs.com/hc/pt-br/articles/360026253631-WINT-Como-funciona-a-convers%C3%A3o-de-embalagem-master-para-venda-na-entrada-de-mercadorias>
- Omie — recebimento da NF-e do fornecedor (fator de conversão, unidade tributável): <https://ajuda.omie.com.br/pt-BR/articles/1419039-recebimento-da-nf-e-de-fornecedor>

- TOTVS Winthor — embalagens (rotinas 2014/292), código auxiliar, validação EAN/DUN, fator preço e atacado por embalagem: <https://centraldeatendimento.totvs.com/hc/pt-br/articles/4570383682199-WINT-Como-incluir-cadastrar-embalagem-na-rotina-2014>, <https://centraldeatendimento.totvs.com/hc/pt-br/articles/360028430431-WINT-Como-utilizar-o-fator-pre%C3%A7o-entre-atacado-e-varejo-atrav%C3%A9s-da-rotina-2014-utilizando-precifica%C3%A7%C3%A3o-por-embalagem>, <https://centraldeatendimento.totvs.com/hc/pt-br/articles/360026950151-WINT-Como-trabalhar-com-pre%C3%A7o-de-Atacado-e-varejo-utilizando-precifica%C3%A7%C3%A3o-por-embalagem>
- TOTVS Varejo Supermercados PDV (preço de embalagem fechada): <https://produtos.totvs.com/ficha-tecnica/tudo-sobre-o-totvs-varejo-supermercados-pdv/>
- Bling — variação composta (kit consome a unidade): <https://ajuda.bling.com.br/hc/pt-br/articles/34016549651095-Como-cadastrar-produtos-com-varia%C3%A7%C3%A3o-composta-no-Bling>
- Sistemas de adega/distribuidora: <https://sisfood.com.br/segmentos/sistema-para-distribuidora-bebida>, <https://www.nextar.com.br/segmento/loja-de-bebidas>, <https://mbmsolutions.com.br/sistema-para-distribuidora-de-bebidas>
- Datacaixa — preço de atacado por quantidade mínima no PDV: <https://www.datacaixa.com.br/ajuda/pdv/pdv-cadastros/como-configurar-o-preco-de-atacado-do-produto-no-pdv/>

- Bling — rejeições 612, 630, 885, 886 e 894 (cEANTrib, GTIN tributável, CCG): <https://ajuda.bling.com.br/hc/pt-br/articles/1500001500302-Rejei%C3%A7%C3%A3o-885-GTIN-informado-mas-n%C3%A3o-informado-o-GTIN-da-unidade-tribut%C3%A1vel>, <https://ajuda.bling.com.br/hc/pt-br/articles/360060144114-Rejei%C3%A7%C3%A3o-630-Valor-do-Produto-difere-do-produto-Valor-Unit%C3%A1rio-de-Tributa%C3%A7%C3%A3o-e-Quantidade-Tribut%C3%A1vel>, <https://ajuda.bling.com.br/hc/pt-br/articles/16647254094487-Rejei%C3%A7%C3%A3o-894-GTIN-da-unidade-tribut%C3%A1vel-inexistente-no-Cadastro-Centralizado-de-GTIN-CCG>
- Tecnospeed — rejeições 629 e 630: <https://atendimento.tecnospeed.com.br/hc/pt-br/articles/360010451513-NF-e-Como-resolver-a-Rejei%C3%A7%C3%A3o-629-Valor-do-Produto-difere-do-produto-Valor-Unit%C3%A1rio-de-Comercializa%C3%A7%C3%A3o-e-Quantidade-Comercial>
- Oobj — rejeição 886: <https://oobj.com.br/bc/rejeicao-886-como-resolver/>
- Guinzo — unidade comercial × tributável (exemplo do leite em caixa): <https://site.guinzo.com.br/ucomeutrib/>
- Unidade de medida na NF-e (uCom, uTrib, erro do qTrib): <https://www.notafiscal.cnt.br/unidade-de-medida/>
- WK — taxa de conversão (uTrib/qTrib/vUnTrib): <https://ajuda.wk.com.br/78/wk/Cadastros/Produtos/Cadastros_Produtos_Taxa_de_Conversao.htm>
- GS1 Brasil — ITF-14 / DUN-14: <https://www.gs1br.org/itf-14>
- `etiquetas-plano.md` §3 e §8 (pesquisa inicial e o contrato que este plano cumpre)
