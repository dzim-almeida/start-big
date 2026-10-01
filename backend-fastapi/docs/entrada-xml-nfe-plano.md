# Plano: entrada de mercadoria pela XML da NF-e do fornecedor

Escrito em 01/10/2026, na branch `embalagens`. É o primeiro dos "próximos
planos" combinados no `produto-embalagens-plano.md` (§10).

**O problema:** hoje a mercadoria entra produto a produto, digitando
quantidade e custo (Estoque › Entrada). Uma nota de bebida tem 30, 40 itens,
em caixa ou fardo, com IPI, ST e frete em cima. É lento, e o custo digitado à
mão costuma esquecer o ST e o frete, o que deixa o lucro do relatório maior do
que o real.

**A ideia:** o lojista abre o arquivo XML que o fornecedor manda por e-mail
(ou que baixa do portal), confere a tela e confirma. O sistema:
1. acha cada item no cadastro (ou ajuda a cadastrar);
2. dá entrada na quantidade certa, já convertendo caixa/fardo em unidade;
3. congela o **custo real** por unidade (com IPI, ST, frete e desconto);
4. sugere o cadastro fiscal dos produtos novos (NCM, CEST, ST);
5. lança as **parcelas a pagar** da nota no Financeiro;
6. não deixa importar a mesma nota duas vezes.

> **Execução (01/10/2026, branch `embalagens`):** fases 1, 2 e 3 feitas — §7.

---

## 0. O que "pronto" significa

| # | Critério de aceite |
|---|---|
| X1 | Abrir o XML de uma NF-e (com ou sem o `nfeProc`) e ver fornecedor, número, data, itens e parcelas **antes** de gravar qualquer coisa |
| X2 | Item cujo código de barras já está no cadastro é reconhecido sozinho, inclusive pelo código da **embalagem** (fardo de 12 → entra 12 un por fardo) |
| X3 | Item que o sistema não reconhece pode ser **vinculado** a um produto existente, **cadastrado** ali mesmo ou **ignorado** |
| X4 | O vínculo é **lembrado**: na próxima nota do mesmo fornecedor, o item vem reconhecido (De-Para) |
| X5 | O custo por unidade inclui IPI, ST, frete, seguro e outras despesas, menos o desconto; recalcula a média ponderada como qualquer compra |
| X6 | A mesma chave de acesso não entra duas vezes (recusa clara, com a data da primeira importação) |
| X7 | As duplicatas da nota viram contas a pagar do fornecedor, com o vencimento e o valor de cada uma, se o lojista marcar |
| X8 | Produto novo nasce com NCM, CEST e a **sugestão** de ST/monofásico tirada da nota; produto existente com fiscal preenchido **não** é alterado |
| X9 | Quem não usa a importação não vê nada mudar (entrada manual idêntica) |

---

## 1. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | **Duas chamadas:** `ler` (só lê e sugere, não grava) e `importar` (grava tudo numa transação) | O lojista precisa conferir antes; e se algo falha no meio, nada fica pela metade |
| D2 | O `importar` recebe **o XML de novo** + as decisões da tela, e relê no servidor | Não confiar em quantidade/custo vindos da tela: o que vale é o que está na nota |
| D3 | Leitura com `defusedxml` | O XML vem de fora; recusa entidades (ataque "billion laughs"/XXE) |
| D4 | Ordem para reconhecer o item: (1) vínculo salvo fornecedor + código do fornecedor; (2) `cEAN` no código de barras do produto ou de uma embalagem; (3) `cEANTrib` no código da unidade | O vínculo é a escolha que o lojista já fez; o EAN é o padrão do mercado |
| D5 | **Fator** (unidades por item da nota): da embalagem reconhecida; senão `qTrib ÷ qCom` quando der inteiro e as unidades forem diferentes (CX 1 → UN 12); senão 1. Sempre editável | É como a nota diz "caixa com 12" |
| D6 | **Custo** = (`vProd` − `vDesc` + `vFrete` + `vSeg` + `vOutro` + `vIPI` + `vICMSST` + `vFCPST`) ÷ (`qCom` × fator) | Custo de aquisição de quem é do Simples (não aproveita crédito). Regime normal com crédito de ICMS fica fora (§6) |
| D7 | Fiscal **só sugere e só preenche vazio**: produto novo nasce com NCM/CEST da nota; ST sugerido se o item veio com ICMS-ST (CST 10/30/60/70/90 com `vICMSST`/`vICMSSTRet`, ou CSOSN 201/202/203/500) → CSOSN 500 ou CST 60 + CFOP 5405; PIS/COFINS CST 02/03/04 na compra → 04 na revenda | O sistema não decide ST (ver `derivacao/situacao.py`); a nota do fornecedor é a melhor pista, e o contador confere |
| D8 | Contas a pagar: uma por `<dup>`, com o `nDup` na descrição; sem `<dup>`, nenhuma (o lojista lança à mão) | Nota à vista não tem duplicata; inventar vencimento seria pior |
| D9 | Fornecedor pelo CNPJ/CPF do emitente; se não existe, é criado com nome, fantasia, IE e endereço da nota | Mesma lógica de qualquer ERP |
| D10 | Movimento de estoque com origem nova `NFE_ENTRADA` e o vínculo `nota_entrada_id` | O livro responde "de que nota veio esta entrada?" |
| D11 | Destinatário diferente do CNPJ da loja: **aviso**, não bloqueio | Filial, nota em nome do sócio — acontece; o lojista decide |
| D12 | Só NF-e modelo 55 de **saída do fornecedor** (`tpNF=1`). NFC-e (65) e nota de entrada própria são recusadas | NFC-e é venda a consumidor, não compra de revenda |

---

## 2. Modelo de dados

```
notas_entrada (nova)
├── id, empresa_id
├── chave           VARCHAR(44) UNIQUE   ← trava a dupla importação (X6)
├── numero, serie, emissao (data), valor_total (centavos)
├── fornecedor_id   FK fornecedores
├── itens_lancados  INT
├── usuario_nome, importada_em

produto_codigos_fornecedor (nova) — o De-Para (X4)
├── id, fornecedor_id FK, codigo_fornecedor VARCHAR(60)
├── produto_id FK, embalagem_id FK nulo, fator INT
└── UNIQUE (fornecedor_id, codigo_fornecedor)

movimentacoes_estoque
└── + nota_entrada_id  FK nulo (SET NULL)
```

Migration só acrescenta; decide pela ausência de cada tabela/coluna.

---

## 3. API

- `POST /api/v1/estoque/nfe-entrada/ler` — arquivo XML (multipart) → prévia:
  nota, fornecedor (existente ou "será criado"), itens com a sugestão de cada
  um (produto, embalagem, fator, custo por unidade, fiscal sugerido, como foi
  reconhecido), duplicatas, avisos (destinatário, nota já importada).
- `POST /api/v1/estoque/nfe-entrada/importar` — `{xml, itens: [{indice, acao:
  vincular|criar|ignorar, produto_id, embalagem_id, fator, novo: {nome,
  codigo_produto, codigo_barras, valor_varejo}}], lancar_contas_pagar}`.
- `GET /api/v1/estoque/nfe-entrada` — notas já importadas.

Permissão: a mesma da entrada manual (`produto`). Contas a pagar só com o
módulo Financeiro liberado; sem ele, a opção não aparece e o backend ignora.

---

## 4. Tela

Estoque › botão **Entrada por XML** → janela em três passos:
1. **Arquivo:** arrasta ou escolhe o `.xml`.
2. **Conferência:** cabeçalho da nota e do fornecedor; tabela de itens com a
   situação ("reconhecido pelo código de barras", "pelo vínculo", "não
   reconhecido"), produto, quantidade da nota → unidades que entram, custo por
   unidade (e o anterior, para ver o reajuste), ação. Item não reconhecido:
   escolher produto, cadastrar novo (nome, código e preço de venda já
   preenchidos) ou ignorar. Parcelas com a caixa "Lançar no contas a pagar".
3. **Pronto:** resumo do que entrou e atalho para as etiquetas da entrada.

---

## 5. Fases

| Fase | Entrega |
|---|---|
| 1 | Leitura do XML (conta pura) e testes com notas reais de exemplo |
| 2 | Tabelas, migration, `ler` e `importar` com testes ponta a ponta |
| 3 | Tela (upload, conferência, cadastro rápido, resumo) |

---

## 6. Fora de escopo (por enquanto)

- **Baixar a nota pela chave na SEFAZ** (Manifestação do Destinatário / DF-e):
  precisa de certificado e passa pela plataforma fiscal. Fase própria.
- **Crédito de ICMS/PIS/COFINS** no custo para o regime normal.
- **Devolução ao fornecedor** e conferência física (recebimento cego).
- **Atualizar o preço de venda** pela margem: a tela mostra o custo novo; o
  preço continua sendo do lojista.

---

## 7. Entrega (01/10/2026)

- **Leitura:** `app/core/nfe_xml.py` (conta pura, `defusedxml`). Recusa NFC-e,
  nota de entrada da própria loja, XML com entidades e nota sem chave/itens.
- **Banco:** migration `f6b3d82a1c47` — `notas_entrada` (chave única),
  `produto_codigos_fornecedor` (De-Para) e `movimentacoes_estoque.nota_entrada_id`.
  Testada numa cópia do banco local.
- **API:** `POST /estoque/nfe-entrada/ler` (multipart, não grava),
  `POST /estoque/nfe-entrada/importar` (uma transação; o XML é relido no
  servidor), `GET /estoque/nfe-entrada`.
- **Tela:** Estoque › **Entrada por XML** — arquivo, conferência item a item
  (produto existente com busca, embalagem ou fator, cadastrar novo com preço
  de venda, ou não dar entrada), parcelas, e no fim "Etiquetas desta entrada"
  (manda à fila da Central de Etiquetas). As entradas também aparecem em
  "Entradas recentes" das etiquetas, que filtram por tipo ENTRADA.
- **Fiscal:** só o produto NOVO recebe a sugestão (NCM, CEST, CSOSN/CST,
  CFOP, PIS/COFINS). Produto existente não tem o fiscal alterado. NCM/CEST
  inválidos na nota: o produto nasce sem fiscal, a entrada não trava.
- **Testes:** leitura (11), API ponta a ponta (8: prévia não grava, entrada
  com embalagem e custo da nota, produto novo com fiscal, fornecedor com
  endereço, parcelas, dupla importação recusada, rollback no erro do meio,
  item sem decisão, vínculo lembrado, aviso de CNPJ, NFC-e recusada).

**Não verificado:** a tela num navegador (só `vue-tsc` e build). Conferir com
uma nota real de fornecedor da adega antes do canário.

### 7.1 Caixa/fardo sem o fator na nota (01/10/2026)

O erro clássico: o fornecedor manda "2 CX" sem dizer quantas unidades vêm na
caixa (uCom e uTrib iguais), e a caixa entra como 2 unidades. Como o mercado
trata: o Bling tem o campo **"fator de conversão"** em cada item da importação
(o exemplo da ajuda deles é exatamente a caixa de 10 que vem como "UN"); o
Omie guarda a **unidade de compra do fornecedor e o fator** no produto, por
fornecedor. O nosso já tinha os dois (fator por item e o De-Para lembrado).
Faltavam as travas:

1. **Confirmação obrigatória:** unidade da nota de embalagem (CX, FD, PCT, DP,
   DZ, BD, ENG…) com fator 1, sem embalagem do cadastro e sem vínculo já
   confirmado → o item fica pendente até informar o fator ou clicar "É 1
   unidade mesmo". **O servidor também recusa** (422) — não é só a tela.
2. **Dúzia** (DZ) vira 12 sozinha.
3. **Custo divergente:** custo por unidade ≥ 50% diferente do custo atual do
   produto aparece em vermelho na linha. Fator errado sempre aparece assim
   (a caixa entrando como unidade fica 12× mais cara).
4. **Conversão visível:** "Na nota 2 CX → no estoque 24 un a R$ 4,33 cada".

Fontes: Bling — <https://ajuda.bling.com.br/hc/pt-br/articles/360036460513-Como-importar-o-XML-de-nota-de-entrada>;
Omie — <https://ajuda.omie.com.br/pt-BR/articles/9546171-julho-2024>,
<https://ajuda.omie.com.br/pt-BR/articles/3625872-definindo-informacoes-para-compra-de-produtos-para-cada-fornecedor>.
