# Plano: vender quantidade quebrada no PDV (3,5 kg)

Escrito em 07/10/2026, na branch `feat/fiscal-ativacao`, depois do achado do
erro 500 no PDV (`995147d`). Pedido do Alan: "ele teria que ter a inteligência
de vender 3,5 kg".

**Por que plano separado:** a quantidade da linha da venda é inteira desde
sempre, e muda o que todas as lojas usam todo dia — subtotal, estoque, nota
fiscal, cupom, orçamento, devolução e relatórios. Errar aqui cobra valor
errado no caixa ou faz a SEFAZ rejeitar nota.

**Nada começa a ser codado antes de as decisões da §3 estarem aceitas.**

> **Execução (branch `feat/venda-fracionada`, 07/10/2026):** decisões D1–D8
> aceitas pelo Alan; a branch saiu antes do canário do fiscal (D9), mas o
> instalador do canário continua saindo da `feat/fiscal-ativacao`. F0–F4
> feitas (§7). Falta: homologação da NF-e/NFC-e de 3,5 kg e o canário (F5).

---

## 0. O que "pronto" significa

| # | Critério de aceite | Hoje |
|---|---|---|
| Q1 | Produto em KG com 1,5 kg em estoque aparece na busca do PDV | ✅ desde `995147d` (antes: erro 500) |
| Q2 | Digitar **3,5** na linha de um produto em KG cobra 3,5 × preço, arredondado no centavo | recusado (o schema exige inteiro) |
| Q3 | O estoque baixa **3,5** e o cancelamento/devolução devolve **3,5** | só inteiro |
| Q4 | Produto em **UN** continua recusando 1,5 — com mensagem clara, não erro 500 | recusa com 422 genérico |
| Q5 | NF-e e NFC-e de 3,5 kg **autorizadas em homologação** (`qCom = 3.5000`) | nunca emitida |
| Q6 | Cupom, A4 e DANFE NFC-e mostram "3,5 kg" (vírgula, unidade) | mostram inteiro |
| Q7 | Orçamento aceita 3,5 kg e a conversão para venda leva 3,5 | só inteiro |
| Q8 | Relatórios de quantidade vendida (curva ABC, extratos) somam 3,5 sem erro | quebrariam com 500 (`relatorio.py:129` é `int`) |
| Q9 | **Quem não vende fracionado não vê nada mudar** — venda, nota, estoque e relatório idênticos | cláusula de não-regressão |

Q9 é a mais importante.

---

## 1. Como está hoje (conferido no código, 07/10/2026)

| Onde | O que existe | O que falta |
|---|---|---|
| `db/models/estoque.py`, `movimentacao_estoque.py` | `quantidade` **Float** desde `f97d3c1` (10/08, serigrafia), sem migration — o SQLite guarda `real` numa coluna `INTEGER` | — |
| `db/models/ordem_servico_item.py` | **Float**; valor = `round(qtd × unitário)` (`services/ordem_servico.py:343,923,962`) | — (é o modelo a copiar) |
| `db/models/venda_produto.py:78` / `orcamento_produto.py:80` | `quantidade` **Integer**; `quantidade_base -> int` | Float |
| `schemas/vendas.py:16,92,126` / `orcamentos.py:14,56,87` | `quantidade: int` | float, com a regra da §3 |
| `services/venda.py:381-446` / `orcamento.py:126-168` | `subtotal = quantidade × valor_unitario` (int × int) | `round()` como na OS |
| `services/produto.py:406,434` | baixa/estorno com `quantidade: int` na assinatura (aceita float na prática) | tipo e teste |
| `services/regras_preco.py` | faixas "a partir de N" e **leve-pague** (inteiros) | decidir com fracionado (D5) |
| `services/fiscal/payload_itens.py:55` | `quantidade_comercial = float(item.quantidade)` — **já decimal** | — |
| `payload_itens.py:85` (motor de impostos) | `Decimal(item.quantidade)` — com float vira `Decimal('0.29999…')` | `Decimal(str(...))` |
| `services/fiscal/snapshot.py` / devolução | **milésimos** (`quantidade_milesimos`) — já fracionado | — |
| `schemas/documento_fiscal.py:18` (itens do drawer) | `quantidade: int` | float (senão 500 no drawer da nota) |
| `schemas/relatorio.py:129` (curva ABC) | `quantidade: int` | float |
| `crud/relatorio.py:293,383,686,952`, `relatorio_custo.py:194` | `SUM(quantidade × …)` | conferir arredondamento do custo |
| `frontend/.../SaleItemsTable.vue:248` | o campo **já aceita "3,5"** (troca vírgula por ponto) | `inputmode="decimal"`, `+`/`−` sem zerar a fração, mostrar com vírgula e unidade |
| `frontend/.../productSale.schema.ts:11,151` | `min(1)` | `> 0` para fracionado |
| `sales/components/print/*` (`SalePrintTemplate.vue`, `nfceToEscPos.ts`) | imprimem inteiro | formatar 3,5 / 3,500 |

**Compras e Fábrica ficam inteiras por decisão** (compras-plano D3 e
`schemas/fabrica.py:156`): compra-se saco, chapa e rolo inteiros.

---

## 2. Princípios

1. **Aditivo.** Nada muda para produto em UN; o tipo da coluna muda, o
   comportamento só muda onde a quantidade vier quebrada.
2. **Sem migration**, pelo mesmo motivo de `f97d3c1`: o SQLite já guarda
   `real` numa coluna `INTEGER`, e recriar `produtos_venda` no banco vivo das
   lojas, sem backup automático, é risco sem ganho. Coberto por teste que
   grava 3,5 num banco com o schema antigo.
3. **Dinheiro continua inteiro (centavos)**: `subtotal = round(qtd × unitário)`,
   como a OS já faz.
4. **Nota fiscal com fotografia** (F0.3 do fiscal): nenhum payload inteiro
   pode mudar um byte.

---

## 3. Decisões (para o Alan aceitar)

| # | Pergunta | Recomendação |
|---|---|---|
| D1 | **Quem pode vender quebrado?** | Pela **unidade de medida**: KG, G, L, ML, M, M2, M3. UN, CX, PC, FD e as demais só inteiro. Sem campo novo no cadastro: a unidade já diz. (Alternativa: uma chave "vende fracionado" por produto — mais flexível, mas é mais um campo para o lojista esquecer.) |
| D2 | **Quantas casas?** | **3** (grama, mililitro). A NF-e aceita 4; 3 casam com os milésimos que o snapshot fiscal já usa. 3,5 kg vira 3,500. |
| D3 | **Produto em UN com 1,5** | Recusa com mensagem: "Este produto é vendido em unidade inteira (UN)". |
| D4 | **Botões + e −** | Somam/tiram 1 mantendo a fração (3,5 → 4,5). O − não deixa passar de zero. |
| D5 | **Regras de preço (embalagens §6.1)** | Faixa "a partir de 6" vale com fração (6,2 kg entra). **Leve-pague** e **embalagem** não se aplicam a produto fracionado (fardo de 12 kg não existe no caixa). |
| D6 | **Orçamento** | Entra junto: ele vira venda, e uma conversão que trunca 3,5 para 3 é perda silenciosa. |
| D7 | **Balança** (EAN-13 prefixo 2, peso/preço no código) | **Fora deste plano** (como já decidido em `pdv-profissional-plano.md` §10), mas fica **destravado** por ele: com a quantidade fracionada pronta, a balança vira só ler o código. |
| D8 | **Multiplicador** (`3,5 *` antes de bipar) | Fora; é a "primeira coisa da próxima rodada" do PDV. Digitar na linha resolve. |
| D9 | **Onde nasce** | Branch própria `feat/venda-fracionada`, a partir da `feat/fiscal-ativacao` **depois do canário do fiscal**, para não misturar riscos no instalador que vai para o Celso. |

---

## 4. Fases

| Fase | O quê | Custo |
|---|---|---|
| **F0** Rede | Testes que fotografam a venda **inteira** de hoje (subtotal, estoque, payload NF-e/NFC-e, cupom). Teste que grava 3,5 em `produtos_venda` com o schema antigo | ½ d |
| **F1** Backend da venda | `quantidade` Float no model/schemas de venda e orçamento; validação D1–D3 (3 casas, unidade); `round()` no subtotal; regras de preço D5; baixa/estorno; `quantidade_base` | 1½ d |
| **F2** Front do PDV | `inputmode="decimal"`, D4, exibição "3,5 kg", zod `> 0`, orçamento | 1 d |
| **F3** Fiscal | `Decimal(str(...))` no motor; fotografias novas (NF-e e NFC-e 3,5 kg); `DocumentoItemResumo.quantidade` float; **homologação** | 1 d |
| **F4** Saídas | Cupom, A4, DANFE NFC-e; relatórios (`relatorio.py:129`, somas de custo); devolução e cancelamento ponta a ponta | 1 d |
| **F5** Canário | Uma loja que vende por quilo (serigrafia): venda de 3,5 kg com NFC-e real de valor baixo | — |

**Total: ~5 dias de código** + homologação e canário.

---

## 5. Riscos

| Risco | Contenção |
|---|---|
| Float: `0,1 + 0,2 = 0,30000000000000004` | arredondar a quantidade em 3 casas na entrada (schema); dinheiro sempre `round()` em centavos |
| Venda inteira mudar sem querer | F0 fotografa antes; Q9 é critério de aceite |
| NF-e rejeitada por `qCom × vUnCom ≠ vProd` | o `vProd` sai do subtotal arredondado; fotografia + homologação (F3) |
| Outro schema `int` esquecido → erro 500 (foi o que aconteceu em 10/08) | varredura de `quantidade: int` nas respostas (§1) e teste de API com 3,5 em cada tela |
| Terminal novo com servidor antigo | o servidor antigo recusa 3,5 com 422 (não quebra); a tela mostra a mensagem |

---

## 6. O que NÃO entra

- **Balança** (D7) e **multiplicador** (D8).
- **Compras e Fábrica fracionadas** (decisão própria daqueles planos).
- **Unidade de venda diferente da de estoque** (vender em g e estocar em kg):
  o estoque e a venda ficam na mesma unidade do cadastro.

---

## 7. Entrega (07/10/2026)

| Fase | Commit | O que ficou |
|---|---|---|
| F0 | `bdc025a` | DDL antigo de `produtos_venda`/`orcamentos_produtos` congelado (3,5 e 0,5 sobrevivem como `real`, 3.0 volta `integer`); fotografia da venda e do orçamento em UN, com o JSON em `3` |
| F1 | `67002b6` | Float sem migration; tipo `Quantidade` (3 casas, > 0, inteiro volta inteiro); `services/quantidade_venda.py` (D1/D3/D5); centavo meio-para-cima; faixa vale, fardo e leve-pague não; saldo do estoque em 3 casas; orçamento traz `unidade_medida`. A fotografia pegou uma regressão no caminho ("Preço de 1.0 FD") |
| F2 | `7dae3b0` | PDV: campo "3,5" (teclado decimal), +/− mantêm a fração, aviso em UN; impressão A4, cupom e DANFE NFC-e com "3,5 kg" |
| F3 | `cd16c16` | Fotografias NF-e e NFC-e de 3,5 kg (rejeição 629 conferida); drawer da nota mostrava 4 em vez de 3,5 e o `int` derrubava a nota |
| F4 | (este) | Somas de custo com `ROUND` no banco (CMV, custo por funcionário/venda, custo da OS); curva ABC e regras em float. **Achado:** o relatório de estoque já quebrava em produção com qualquer estoque fracionado (valor imobilizado com centavo quebrado) |

**Unidades fracionáveis:** KG, G, L, ML, M, CM, M2, M3 — a mesma lista no
backend e no front, com teste que falha se as duas divergirem (CM entrou para
casar com o que o front já exibia como fracionado).

**Fora, por enquanto:** o drawer da nota mostra a quantidade sem vírgula
("3.5"): o arquivo tem alteração local do Alan fora dos commits, e não foi
tocado.
