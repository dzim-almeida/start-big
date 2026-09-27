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
estoque. É o mesmo desenho deste plano.

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
| D3 | **Fator inteiro ≥ 2.** | Cobre fardo, caixa, pacote, display. Fator decimal (caixa de piso com 2,5 m²) muda o tipo de `venda_produto.quantidade` (inteiro) e fica para depois (§8). |
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
├── ativo               Boolean
└── datas

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

---

## 7. Fases

| Fase | Entrega | Risco |
|---|---|---|
| **1. Cadastro + etiqueta** | Tabela, API, seção no formulário, unicidade do código, fonte `embalagem` na Central de Etiquetas | Baixo: nada vende nem baixa ainda |
| **2. Entrada por embalagem** | Movimentação de entrada em FD/CX, custo convertido | Médio: custo médio |
| **3. Venda e orçamento** | PDV bipa a embalagem, linha por embalagem, baixa/cancelamento/reabertura por fator | **Alto**: estoque de lojas em produção |
| **4. NF-e e NFC-e** | uCom/uTrib/qTrib/vUnTrib, cEAN/cEANTrib, validação 629/630/885/886, devolução | **Alto**: rejeição na SEFAZ |
| **5. Relatórios** | Quantidade vendida na unidade base | Baixo |

**As fases 3 e 4 sobem juntas para as lojas que emitem nota:** vender fardo
sem a nota saber do fator é exatamente o erro clássico do §2. Loja sem módulo
fiscal pode receber a 3 antes.

**Liberação:** homologação primeiro (testar 629/630/885/886/894 de propósito),
depois **uma loja canário com backup** antes de todas.

---

## 8. Fora de escopo (por enquanto)

- **Embalagem de embalagem** (palete de caixas): um nível só (D3).
- **Fator decimal** (caixa de piso com 2,5 m², rolo com 50 m): exige mudar
  `venda_produto.quantidade` de inteiro para decimal.
- **OS vendendo embalagem** (D11).
- **Gerar DUN-14** para a loja: o DUN precisa estar no Cadastro Centralizado
  de GTIN (rejeição 894) — quem gera é o fabricante na GS1.

---

## 9. Perguntas em aberto

1. **Quem vai usar primeiro?** Qual loja (e segmento) pediu fardo/caixa? Define
   se a fase 3 vai com ou sem nota.
2. **Preço do fardo:** as lojas praticam preço próprio do fardo (mais barato por
   unidade)? Se sempre for "fator × unidade", o campo de preço pode esperar.
3. **Fator decimal** (piso, tecido, fio) é necessidade real de alguma loja
   agora? Se for, a fase 3 muda de tamanho.
4. **Na tela do estoque**, mostrar "120 un · 20 FD" ajuda ou polui?

---

## Fontes

- Bling — rejeições 612, 630, 885, 886 e 894 (cEANTrib, GTIN tributável, CCG): <https://ajuda.bling.com.br/hc/pt-br/articles/1500001500302-Rejei%C3%A7%C3%A3o-885-GTIN-informado-mas-n%C3%A3o-informado-o-GTIN-da-unidade-tribut%C3%A1vel>, <https://ajuda.bling.com.br/hc/pt-br/articles/360060144114-Rejei%C3%A7%C3%A3o-630-Valor-do-Produto-difere-do-produto-Valor-Unit%C3%A1rio-de-Tributa%C3%A7%C3%A3o-e-Quantidade-Tribut%C3%A1vel>, <https://ajuda.bling.com.br/hc/pt-br/articles/16647254094487-Rejei%C3%A7%C3%A3o-894-GTIN-da-unidade-tribut%C3%A1vel-inexistente-no-Cadastro-Centralizado-de-GTIN-CCG>
- Tecnospeed — rejeições 629 e 630: <https://atendimento.tecnospeed.com.br/hc/pt-br/articles/360010451513-NF-e-Como-resolver-a-Rejei%C3%A7%C3%A3o-629-Valor-do-Produto-difere-do-produto-Valor-Unit%C3%A1rio-de-Comercializa%C3%A7%C3%A3o-e-Quantidade-Comercial>
- Oobj — rejeição 886: <https://oobj.com.br/bc/rejeicao-886-como-resolver/>
- Guinzo — unidade comercial × tributável (exemplo do leite em caixa): <https://site.guinzo.com.br/ucomeutrib/>
- Unidade de medida na NF-e (uCom, uTrib, erro do qTrib): <https://www.notafiscal.cnt.br/unidade-de-medida/>
- WK — taxa de conversão (uTrib/qTrib/vUnTrib): <https://ajuda.wk.com.br/78/wk/Cadastros/Produtos/Cadastros_Produtos_Taxa_de_Conversao.htm>
- GS1 Brasil — ITF-14 / DUN-14: <https://www.gs1br.org/itf-14>
- `etiquetas-plano.md` §3 e §8 (pesquisa inicial e o contrato que este plano cumpre)
