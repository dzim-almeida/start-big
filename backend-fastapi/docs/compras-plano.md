# Plano: módulo de Compras

Escrito em 03/10/2026, na branch `feat/compras` (saída da `embalagens`, `f40349e`).

**O problema:** hoje a loja só registra a compra **quando a mercadoria chega**
(entrada manual ou pela XML). Não há registro do que foi **pedido**, de quando
vai chegar nem de quanto falta chegar. Também não há quem avise **o que precisa ser
comprado**. O dono descobre que acabou quando o cliente pede e não tem.

**A ideia:** um módulo que cobre o caminho inteiro — *o que comprar → pedido
ao fornecedor → recebimento → estoque e contas a pagar* — servindo **todos os
segmentos**. A marcenaria (o resumo do Alan, "Módulo de Compras para
Marcenaria — Especificação", RC01–RC20) entra depois como **mais uma origem de
necessidade**, sem que o módulo dependa dela (§10).

**Comercial:** módulo **contratável** `COMPRAS`, como NF-e, NFC-e e Financeiro
PRO. Quem não contrata não vê nada mudar.

**Nada começa a ser codado antes de as decisões da §4 estarem aceitas.**

> **Status (03/10/2026):** o Alan respondeu as perguntas (§11). Núcleo
> primeiro, marcenaria na fase 6; piloto em loja **PDV**; módulo no plano
> **Business** e avulso por cliente; contas a pagar **como o mercado faz**
> (D8, pesquisado); divergência **só avisa**; sem cotação, mas com **aviso de
> fornecedor mais barato** (D18). Prazo: no nosso ritmo. Liberado para a fase 1.

> **Execução (branch `feat/compras`):** fase 1 em 03/10/2026 (§12); fase 2 em 03/10/2026 (§13); fase 3 em 03/10/2026 (§14); fase 4 em 04/10/2026 (§15).

---

## 0. O que "pronto" significa

| # | Critério de aceite | Hoje |
|---|---|---|
| C1 | Cadastrar no produto "compro da Ambev, em fardo de 12, código 4471, prazo 3 dias" | só o De-Para da XML guarda código, e só depois da 1ª nota |
| C2 | A tela **Necessidades** lista o que está abaixo do mínimo, **já descontando o que está pedido**, agrupado por fornecedor, na unidade de compra (fardo) | o mínimo existe no cadastro, mas nada usa |
| C3 | Gerar o pedido a partir das necessidades com um clique por fornecedor, com o último preço pago já preenchido | não existe pedido |
| C4 | Mandar o pedido ao fornecedor em **PDF** e por **WhatsApp** | — |
| C5 | Receber **parte** do pedido hoje e o resto amanhã; o pedido fica "Parcialmente recebido" até chegar tudo | — |
| C6 | No recebimento, bipar o produto (ou o fardo) confere a linha; o que chegou entra no estoque com o **custo real** e recalcula a média | a entrada manual faz isso, mas sem pedido |
| C7 | A **Entrada por XML** reconhece o pedido em aberto do mesmo fornecedor, casa os itens e mostra **divergência** de quantidade e preço | a XML entra solta |
| C8 | Contas a pagar nascem **no recebimento**, proporcionais ao que chegou — e **nunca em dobro** quando a nota já trouxe duplicatas | — |
| C9 | Toda mudança de situação do pedido fica num histórico que **não se edita nem se apaga** | — |
| C10 | Almoxarife recebe e confere **sem ver preço** | — |
| C11 | Loja sem o módulo `COMPRAS`: menu, cadastro de produto, entrada manual e XML **idênticos** a hoje | cláusula de não-regressão |
| C12 | Necessidade calculada por **função pura** com testes (como `nfe_xml.py`) | — |

C11 é a mais importante (nada novo quebra fluxo existente): todas as tabelas são
novas, as colunas novas em tabela existente são opcionais, e o caminho antigo de
entrada (manual e XML) continua funcionando sem pedido.

---

## 1. Como está hoje (03/10/2026)

O que Compras **reaproveita**, sem reinventar:

| Peça | Onde | Uso em Compras |
|---|---|---|
| Fornecedor | `db/models/fornecedor.py` (com `tipo`: produto, transportadora, entregador) | Destino do pedido |
| Livro de estoque | `movimentacoes_estoque` — imutável, com `origem` e `custo_unitario` | Recebimento é uma ENTRADA com origem nova `COMPRA` |
| Custo médio | `estoque.custo_medio` recalculado só em entrada de compra (`services/movimentacao_estoque`) | O recebimento passa pelo **mesmo** serviço |
| Último preço | `estoque.valor_entrada` (referência) | Atualizado no recebimento |
| Estoque mínimo e ideal | `estoque.quantidade_minima`, `quantidade_ideal` | Base da necessidade (fase 2) |
| Embalagens | `produto_embalagens` (`fator` inteiro, `usa_na_entrada`) | Unidade de compra = embalagem |
| De-Para da XML | `produto_codigos_fornecedor` (fornecedor + `cProd` → produto, embalagem, fator) | Lido e alimentado pelo cadastro de fornecedores do produto |
| Entrada por XML | `core/nfe_xml.py`, `notas_entrada`, endpoints `nfe_entrada.py` | Ganha o passo "casar com pedido" (fase 4) |
| Contas a pagar | `contas_pagar` (valor em centavos, `fornecedor_id`, parcelamento) | Geradas no recebimento |
| Trava de módulo | `core/modulos.py` → `requer_modulo`; front `MODULOS` + `requiredModule` no menu | `COMPRAS` |
| Permissão por cargo | `check_permission([...])`, linha própria na tela de Cargos (como "Etiquetas") | Linha "Compras" |

O que **não existe** e o resumo da marcenaria supõe: insumo, categoria com
"sofre perda", BOM, OS em 11 estados, `os_item` congelado, reserva no
estoque, saldo livre. Ver §10.

**Atenção — quantidade fracionada:** `estoque.quantidade` e
`movimentacoes_estoque.quantidade` são `Float` (produto vendido por kg). O
RNC01 do resumo ("tudo inteiro") vale **dentro do módulo** (D3); o estoque
atual não muda.

---

## 2. O mercado (pesquisa de 03/10/2026)

| Sistema | Fluxo | O que vale copiar |
|---|---|---|
| **Bling** | Pedido de compra → "lançar estoque" e "lançar contas" | Transição de situação dispara estoque e contas; a XML ajusta os valores |
| **Olist/Tiny** | Necessidades → Ordem de compra → recebimento | Situações *Em aberto, Em andamento, Atendido, Cancelado*; **recebimento parcial**; sugestão por **estoque mínimo e vendas dos últimos meses** (cobertura até 3 meses) |
| **Omie** | Requisição → Cotação → Pedido → Recebimento, em **Kanban** | Casa a NF-e com o pedido item a item; "Recebido parcialmente"; várias notas por pedido |
| **Sankhya / TOTVS** | O mesmo, com **alçada de aprovação** | **Tolerância de divergência** nota × pedido; acima dela, a nota fica bloqueada |
| **Promob ERP** | Lista de compras sai do projeto/plano de corte (MRP) | É o que a extensão marcenaria (§10) imita, sem o 3D |

**Básico (todos têm):** pedido com situação, parcial, entrada no estoque, contas
a pagar, último preço. Está nas fases 1–3.
**Diferencial:** sugestão de compra, XML × pedido, divergência, aprovação,
Kanban, cotação. Os três primeiros estão nas fases 2–5; os demais ficam
para depois (§9).

---

## 3. A ideia, em uma linha por peça

```
                 ┌───────────── origens de necessidade ─────────────┐
                 │ estoque mínimo (F2) · média de vendas (F5) ·     │
                 │ manual (F2) · OS da marcenaria (F6)              │
                 └──────────────────────┬───────────────────────────┘
                                        ▼
  Fornecedores do produto ──►   NECESSIDADES   (consulta, não tabela)
  (preço, prazo, embalagem)             │ gerar por fornecedor
                                        ▼
                               PEDIDO DE COMPRA ──► PDF / WhatsApp
                    rascunho → enviado → parcial → recebido   (cancelado)
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
          RECEBIMENTO manual (bipa)            ENTRADA POR XML casada
                     └──────────────────┬──────────────────┘
                                        ▼
            movimentacoes_estoque (COMPRA, custo real) · custo médio ·
            último preço · contas a pagar proporcionais · compras_log
```

---

## 4. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | **Núcleo genérico primeiro; marcenaria é uma origem a mais** (fase 6) — *confirmado pelo Alan* | Um módulo que depende de BOM, OS em 11 estados e reserva só sai depois que a marcenaria virar fábrica. O resumo pede isso mesmo (RNC03) |
| D2 | Módulo `COMPRAS` **negado sem resposta** (entra em `MODULOS_NEGADOS_SEM_RESPOSTA`, no back e no front) | Recurso novo, ninguém tem hoje — "não sei" significa NÃO, como NF-e. Precisa a plataforma web emitir a chave |
| D3 | **Inteiros dentro do módulo:** dinheiro em centavos, percentual em pontos-base, quantidade do pedido **inteira na unidade de compra**. O estoque (Float) não muda; a conversão é `qtd × fator` no recebimento — *decisão técnica (segue o RNC01 do resumo do Alan)* | Cumpre o RNC01 sem mexer no PDV dos segmentos em produção |
| D4 | Produto vendido por kg sem embalagem: compra em **kg inteiro**; a diferença de pesagem entra como quantidade recebida real (o recebimento aceita fração só nesse caso) | Raro no varejo atual; evita milésimos em todo o módulo |
| D5 | Situações do pedido: `RASCUNHO → ENVIADO → PARCIAL → RECEBIDO`, e `CANCELADO`. Parcial pode ser **encerrado** ("não vem mais o resto"), virando `RECEBIDO` com saldo cancelado | Padrão Olist/Omie; o encerramento é o que o Bling chama de "atendido" |
| D6 | Só `RASCUNHO` se edita livremente. `ENVIADO` aceita mudar previsão e observação; mudar item exige voltar a rascunho, **com motivo no log** | O pedido é um compromisso com o fornecedor |
| D7 | Cancelar pedido com recebimento é proibido; o caminho é encerrar o saldo (D5) | O que entrou no estoque já está no livro e nas contas |
| D8 | **Como o mercado (Bling, Omie):** (a) o pedido tem **parcelas** pela condição ("30/60/90" → gerar parcelas, editáveis), mas elas **não são conta a pagar**; (b) a conta **real** nasce no **recebimento**: das duplicatas da XML, se houver, senão das parcelas do pedido **proporcionais ao recebido**; (c) a tela mostra as parcelas e deixa **ajustar antes de confirmar**; (d) pedido em aberto aparece como **previsão** no Fluxo de Caixa (só com `FINANCEIRO_PRO`, fase 5) — *decidido: "fazer igual ao mercado"* | Omie: parcelas no pedido, previsão no relatório até receber tudo, parcelas da nota ajustáveis no recebimento. Bling: "lançar contas" na transição para *Atendido*. O "nunca em dobro" é a regra que mais pega em produção |
| D9 | Sem o módulo `FINANCEIRO`, o recebimento não gera contas (a opção some e o backend ignora) — igual à XML hoje | Não criar dependência entre módulos |
| D10 | Recebimento é ENTRADA no livro com origem nova `COMPRA` e `recebimento_compra_id`; passa pelo **mesmo serviço** da entrada manual (custo médio, `valor_entrada`) | Um caminho só para custo; relatório de lucro continua honesto |
| D11 | **Divergência** nota × pedido (quantidade ou preço acima da tolerância, padrão 2%): **aviso** com destaque, não bloqueio, na fase 4 — *confirmado: só avisa* | Loja pequena não tem "liberador"; Sankhya/TOTVS bloqueiam porque têm |
| D12 | Necessidade é **consulta + função pura**, nunca tabela. Gatilho: `saldo + em_pedido ≤ mínimo`. Alvo: `ideal` se houver, senão `mínimo`. Sugestão: `⌈(alvo − saldo − em_pedido) ÷ fator⌉` | Igual ao §8 do resumo, sem a perda (que é da marcenaria) |
| D13 | Fornecedores do produto em **tabela nova** (`produto_fornecedores`); o De-Para da XML **continua como está** e alimenta a tabela nova quando importa uma nota | O De-Para exige `cProd`; o cadastro manual muitas vezes não tem. Mexer nele arrisca a XML que já funciona |
| D14 | Almoxarife: permissão `receive_purchases` **sem** `view_purchase_costs` → recebe e confere, não vê preço nem total | RC19 / DC5 do resumo |
| D15 | Pedido de **serviço** (central de corte, montador) existe no modelo desde a fase 1 (`tipo`), mas a tela só abre na fase 6 | Evita migration depois; não atrasa o núcleo |
| D16 | Cotação formal entre fornecedores e aprovação por alçada: **fora** — *confirmado*; no lugar, o aviso da D18 | O resumo deixa para depois; o Omie tem, mas é processo de empresa média |
| D18 | **Aviso de fornecedor mais barato:** ao pôr um produto no pedido (e na tela de Necessidades), se outro fornecedor do produto tem **último preço menor por unidade**, aparece "Fulano vendeu por R$ X em dd/mm (−N%)". Comparação **por unidade** (custo ÷ fator), para fardo de 12 × caixa de 24 baterem. Só aviso, um clique troca o fornecedor — *pedido do Alan* | Dá o principal ganho da cotação sem o processo. Os preços vêm de graça: todo recebimento e toda XML atualizam `produto_fornecedores.ultimo_preco` |
| D19 | **Comercial:** chave `COMPRAS` no plano **Business** e concedida **avulsa** por cliente, como os demais módulos (cadastro na plataforma web) | Resposta do Alan |
| D17 | Telas de Necessidades e Pedidos só desktop; **Recebimento também em tela estreita** (celular/tablet na LAN, não offline) | RNC05 do resumo. Offline (RNC02) fica fora: o app não tem sincronização |

---

## 5. Modelo de dados

Tudo novo, migration aditiva que decide **pela ausência** de cada tabela/coluna
(modelo: `965c71a2da9a`). Nomes em português, como o resto do banco.

```
produto_fornecedores (nova)                      — C1, D13
├── id, produto_id FK, fornecedor_id FK   (sem empresa_id: produto não tem)
├── codigo_fornecedor   VARCHAR(60) nulo
├── embalagem_id        FK produto_embalagens nulo   ← unidade de compra
├── fator               INT ≥ 1                      ← unidades por unidade de compra
├── ultimo_preco        INT nulo  (centavos por UNIDADE DE COMPRA)
├── ultima_compra_em    DATE nulo
├── prazo_dias          INT nulo
├── ativo, criado_em, atualizado_em
└── UNIQUE (produto_id, fornecedor_id)   ← principal = produtos.fornecedor_id (§12)

pedidos_compra (nova)
├── id, empresa_id, numero INT (sequencial por empresa; exibido "PC-000123")
├── fornecedor_id FK, tipo  MATERIAL | SERVICO
├── situacao  RASCUNHO | ENVIADO | PARCIAL | RECEBIDO | CANCELADO
├── previsao_entrega DATE nulo, enviado_em, recebido_em
├── condicao_pagamento  VARCHAR (ex.: "30/60/90"), forma_pagamento_id nulo
├── frete, desconto, valor_total   INT (centavos)
├── observacao, motivo_cancelamento
└── criado_por_id/criado_por_nome, criado_em, atualizado_em

pedido_compra_itens (nova)
├── id, pedido_id FK
├── produto_id FK nulo (nulo = serviço), descricao  ← nome no momento do pedido
├── embalagem_id nulo, fator INT
├── quantidade           INT   (unidade de compra)
├── quantidade_recebida  INT   (soma dos recebimentos)
├── quantidade_cancelada INT   (saldo encerrado, D5)
└── custo_unitario       INT   (centavos por unidade de compra)

pedido_compra_parcelas (nova) — condição combinada (D8a); NÃO é conta a pagar
├── id, pedido_id FK, numero INT
├── dias INT (a partir do recebimento), valor INT (centavos)
└── forma_pagamento_id nulo

pedido_compra_origens (nova) — de onde veio a demanda (RC06)
├── id, pedido_item_id FK
├── origem   ESTOQUE_MINIMO | VENDAS | MANUAL | OS   (extensível)
├── origem_id INT nulo   (ex.: id do item da OS na fase 6)
└── quantidade INT

recebimentos_compra (nova)
├── id, pedido_id FK, nota_entrada_id FK nulo (fase 4)
├── numero_nota VARCHAR nulo  (recebimento manual com nota em papel)
├── recebido_por_id/nome, recebido_em, observacao

recebimento_compra_itens (nova)
├── id, recebimento_id FK, pedido_item_id FK
├── quantidade INT (unidade de compra), quantidade_unidades FLOAT (D4)
├── custo_unitario INT (real, centavos por unidade de compra)
└── divergencia  VARCHAR nulo (QUANTIDADE | PRECO | ITEM_FORA_DO_PEDIDO)

compras_log (nova) — só INSERT (RC18)
├── id, objeto (PEDIDO | RECEBIMENTO | ITEM), objeto_id
├── situacao_anterior, situacao_nova, motivo
└── usuario_id/usuario_nome, ocorrido_em

movimentacoes_estoque
└── + recebimento_compra_id FK nulo (SET NULL)      origem nova: COMPRA

contas_pagar
└── + recebimento_compra_id FK nulo (SET NULL)      ← "de que recebimento veio?"
```

**Em pedido** (o que está a caminho) = `Σ (quantidade − recebida − cancelada) × fator`
dos itens em pedidos `ENVIADO` ou `PARCIAL`. Rascunho **não** conta — senão
um rascunho esquecido some com a necessidade.

---

## 6. Regras de cálculo (`services/compras/necessidade.py`, função pura)

```python
def sugerir_compra(saldo: float, em_pedido: int, minimo: int | None,
                   ideal: int | None, fator: int) -> int:
    """Unidades de compra a pedir; 0 = não precisa."""
    if minimo is None or saldo + em_pedido > minimo:
        return 0
    alvo = ideal if ideal and ideal > minimo else minimo
    falta = alvo - saldo - em_pedido
    return dividir_para_cima(falta, fator) if falta > 0 else 0
```

Exemplos que viram teste:

| Caso | saldo | em pedido | mín. | ideal | fator | Sugestão |
|---|---|---|---|---|---|---|
| Lata, fardo de 12 | 5 | 0 | 24 | 60 | 12 | ⌈55 ÷ 12⌉ = **5 fardos** |
| Já pedido cobre | 5 | 24 | 24 | 60 | 12 | 5+24 > 24 → **0** |
| Sem ideal | 3 | 0 | 10 | — | 1 | **7** |
| Sem mínimo | 0 | 0 | — | — | 1 | **0** (produto não participa) |
| Kg | 2,5 | 0 | 10 | 20 | 1 | ⌈17,5⌉ = **18 kg** |

Custo no recebimento: `custo por unidade = custo_unitario ÷ fator`, arredondado
**meio para cima** em centavos; rateio de frete e desconto do pedido
proporcional ao valor de cada linha, **resto no último item** (o total fecha
exato). Mesma regra da XML (D6 de lá).

---

## 7. API (`/api/v1/compras`, todo o router com `requer_modulo("COMPRAS")`)

| Método e rota | Permissão | Fase |
|---|---|---|
| `GET/POST/PUT/DELETE /compras/produtos/{id}/fornecedores` | `manage_purchases` | 1 |
| `GET /compras/necessidades?fornecedor_id=` | `view_purchases` | 2 |
| `POST /compras/necessidades/gerar-pedidos` — `{itens:[{produto_id, fornecedor_id, quantidade}]}` → um rascunho por fornecedor | `manage_purchases` | 2 |
| `GET /compras/pedidos?situacao=&fornecedor_id=&busca=` (paginado) | `view_purchases` | 2 |
| `GET/POST/PUT /compras/pedidos[/{id}]` | `manage_purchases` | 2 |
| `POST /compras/pedidos/{id}/enviar` · `/voltar-rascunho` · `/cancelar` · `/encerrar` (motivo) | `manage_purchases` | 2 |
| `GET /compras/pedidos/{id}/pdf` · `/whatsapp` (texto pronto) | `view_purchases` | 2 |
| `GET /compras/pedidos/{id}/log` | `view_purchases` | 2 |
| `POST /compras/pedidos/{id}/recebimentos` — `{itens:[{pedido_item_id, quantidade, custo_unitario?}], numero_nota?, lancar_contas_pagar}` | `receive_purchases` | 3 |
| `POST /estoque/nfe-entrada/ler` → passa a devolver `pedidos_sugeridos` e o casamento por item | (a da XML) | 4 |

Respostas para quem tem só `receive_purchases` saem **sem** campos de preço
(o schema corta no backend, não a tela — D14).

---

## 8. Telas e pastas (padrão do `modules/financeiro/`)

```
frontend/src/modules/compras/
├── routes.ts                         auto-carregado; meta.requiredModule = MODULOS.COMPRAS
├── views/
│   └── ComprasLayout.vue             abas: Necessidades · Pedidos · Recebimento
├── necessidades/
│   ├── views/NecessidadesView.vue
│   └── components/                   tabela agrupada por fornecedor, botão Gerar pedido
├── pedidos/
│   ├── views/PedidosView.vue         lista com filtros (situação, fornecedor), paginação de 3
│   └── components/                   PedidoFormModal, PedidoDetalhePainel (lateral), PedidoLog
├── recebimento/
│   ├── views/RecebimentoView.vue     desktop + layout estreito
│   └── components/                   conferência com bipagem, linha com divergência
└── shared/
    ├── components/                   SituacaoPedidoBadge, FornecedorProdutoTab
    ├── composables/                  queries/mutations (TanStack Query)
    ├── constants/                    queryKeys, situações, rótulos
    ├── schemas/                      Zod (VeeValidate)
    ├── services/compras.service.ts
    └── types/

backend-fastapi/app/
├── api/v1/endpoints/compras.py
├── db/models/  pedido_compra.py, recebimento_compra.py, produto_fornecedor.py, compras_log.py
├── db/crud/compras.py
├── schemas/compras.py
└── services/compras/  necessidade.py (pura), pedido.py, recebimento.py, log.py
test/api/v1/compras/  + test/services/compras/test_necessidade.py
```

- **Menu:** item "Compras" vizinho de Produtos/Estoque, `requiredModule:
  MODULOS.COMPRAS` + `requiredPermission`. Constante nova em
  `shared/constants/modulos.constants.ts` e em `MODULOS_NEGADOS_SEM_RESPOSTA`
  do `modulos.store.ts`.
- **Cadastro do produto:** aba **Fornecedores** só aparece com o módulo
  (`FornecedorProdutoTab` vem de `compras/shared`, carregado sob demanda —
  conferir na fase 1 como a aba Fiscal do produto faz e seguir igual).
- **Cargos:** linha própria "Compras" (`compra`, `view_purchases`,
  `manage_purchases`, `receive_purchases`, `view_purchase_costs`), como foi feita a
  de Etiquetas (`cf11adb`).
- **Visual:** BaseInput/BaseSelect/BaseButton, painel lateral para detalhe (como a
  fila de etiquetas), azul padrão nos ícones, paginação de 3 números. Nada de
  componente novo de base sem necessidade.

---

## 9. Fases

| Fase | Entrega | Pronto quando |
|---|---|---|
| **1 — Base** | Chave `COMPRAS` (back e front), permissões e linha em Cargos; tabelas + migration; `necessidade.py` com os testes da §6; aba Fornecedores no produto; a XML passa a alimentar `produto_fornecedores` | Testes passam; loja sem o módulo não vê diferença (C11) |
| **2 — Pedido** | Necessidades por estoque mínimo; gerar pedidos por fornecedor; CRUD do pedido com parcelas (D8a); situações e log; PDF e WhatsApp; aviso de fornecedor mais barato (D18) | Produto abaixo do mínimo vira pedido e **não** é sugerido de novo enquanto o pedido está aberto |
| **3 — Recebimento** | Conferência com bipagem (produto ou embalagem), parcial, encerrar saldo; entrada `COMPRA` com custo real e média; último preço; contas a pagar proporcionais | Pedido de 10 fardos recebido em 6 + 4 fecha certo no estoque, no custo médio e nas contas |
| **4 — XML × pedido** | A Entrada por XML sugere o pedido aberto do fornecedor, casa itens, mostra divergência; duplicatas da nota no lugar das do pedido | Nota com 1 item a menos e 1 preço 5% acima mostra os dois avisos e não duplica contas |
| **5 — Inteligência** | Sugestão por média de vendas (cobertura = prazo + N dias); alerta de pedido atrasado; pedidos em aberto como previsão no Fluxo de Caixa (D8d, só com `FINANCEIRO_PRO`); relatórios: compras por fornecedor, variação de preço, prazo real × prometido | Sugestão confere com conta feita à mão em 3 produtos da loja piloto |
| **6 — Marcenaria** | Origem `OS` + pedido de serviço (central de corte) — **depende do plano do segmento** (§10) | ver §10 |

Ao fim de cada fase que mexer no backend: `npm run build:sidecar`. Liberação:
homologação, **loja canário com backup**, depois a plataforma concede a chave.

**Fora, por enquanto:** cotação entre fornecedores, aprovação por alçada, Kanban,
devolução ao fornecedor, baixar NF-e pela chave (DF-e — plano próprio já
combinado), recebimento offline, portal do fornecedor.

---

## 10. A marcenaria: o que do resumo entra onde

O resumo do Alan (RC01–RC20) é **o segmento marcenaria virando fábrica** mais
compras. Separando:

| Do resumo | Entra em |
|---|---|
| RC02 unidade de consumo × compra, fator por fornecedor | **Núcleo, fase 1** (`produto_fornecedores`) |
| RC05 pedido agrupado por fornecedor, último preço | **Núcleo, fase 2** |
| RC06 pedido ligado à origem | **Núcleo** (`pedido_compra_origens`), origem `OS` na fase 6 |
| RC08 previsão de entrega | **Núcleo, fase 2**; alerta "passa da instalação" na fase 6 |
| RC10 recebimento com bipagem e parcial | **Núcleo, fase 3** |
| RC11 custo real no livro, sem mexer no que está congelado | **Núcleo, fase 3** |
| RC13 / DC4 título a pagar no recebimento | **Núcleo, fase 3** (D8) |
| RC18 log imutável | **Núcleo, fase 2** |
| RC19 / DC5 almoxarife sem preço | **Núcleo, fase 1** (D14) |
| RNC01 inteiros | **Núcleo** (D3), sem mexer no estoque atual |
| RNC04 cálculo como função pura com testes | **Núcleo, fase 1** |
| RC15/RC16 pedido de serviço da central de corte | **Fase 6** (o `tipo` já nasce na fase 1, D15) |
| RC01 reserva com perda · RC03 necessidade por OS · RC04 trava do sinal · RC07 status no `os_item` · RC09 cancelar OS libera reserva · RC12 alocação por data de instalação · RC14 margem orçada × real · RC20 trava de "Separação e compra" | **Fase 6 — exigem antes, no plano do segmento:** insumo/categoria com "sofre perda", BOM, OS congelada (`os_item`), máquina de 11 estados e reserva no estoque |
| RC17 montador terceirizado | A decidir com a loja piloto (DC6) |
| RNC02 offline | Fora (D17) |

**Ponto de encaixe:** a marcenaria entra por uma **capacidade** do Segment
Registry (ex.: `CAP_COMPRA_POR_OS`), que só registra a origem `OS` no cálculo
de necessidades. Nenhum `if segmento == "marcenaria"` dentro de Compras.

**Reserva** (RC01) é a peça mais delicada: hoje o estoque não tem esse
conceito, e criá-lo mexe no "saldo disponível" que o PDV de todos os segmentos
usa. Fica no plano da marcenaria, com cláusula de não-regressão própria.

---

## 11. Respostas do Alan (03/10/2026)

| # | Pergunta | Resposta | Onde entrou |
|---|---|---|---|
| 1 | Núcleo primeiro, marcenaria na fase 6? | Sim, começar pelo núcleo | D1 |
| 2 | Loja piloto? | Uma loja **PDV** — o módulo serve a qualquer segmento que contratar | §9 (canário) |
| 3 | Contas a pagar no recebimento pela condição do pedido? | "Pesquisar o que o mercado faz e fazer igual" | D8 (Bling/Omie) |
| 4 | Divergência nota × pedido: avisa ou bloqueia? | Só avisa | D11 |
| 5 | Cotação agora? | Não; mas **avisar se outro fornecedor tem mais barato** | D16, D18 |
| 6 | Planos e preço? | Plano **Business** + avulso por cliente, como os outros módulos | D19 |
| 7 | Prazo das fases 1 a 3? | No nosso ritmo | — |

**Pendente fora do ERP:** cadastrar a chave `COMPRAS` na plataforma web
(plano Business e concessão avulsa) antes de liberar para a loja piloto. Até
lá, o módulo fica invisível (D2).

---

## 12. Entrega da fase 1 — Base (03/10/2026)

**Backend**
- Trava: `COMPRAS` em `MODULOS_NEGADOS_SEM_RESPOSTA` (`core/modulos.py`) — sem
  resposta da licença, nega.
- Tabela `produto_fornecedores` (model `produto_fornecedor.py`), migration
  `a1c4e7b20d93` (revisa `f6b3d82a1c47`; só cria a tabela, decide pela
  ausência dela, idempotente).
- `services/compras/`: `necessidade.py` (puro: `sugerir_compra`,
  `preco_por_unidade`, `mais_barato`, `economia_percentual`), `permissoes.py`,
  `fornecedores_produto.py`.
- Rotas (`endpoints/compras.py`, router inteiro com `requer_modulo("COMPRAS")`):
  `GET /compras/fornecedores`, `GET|PUT /compras/produtos/{id}/fornecedores`.
- Entrada por XML: cada item lançado grava o último preço pago ao fornecedor
  (`registrar_compra`) — **com ou sem o módulo**, para o histórico já existir
  quando a loja contratar.

**Frontend**
- `MODULOS.COMPRAS` (nega sem resposta, como no backend); permissões
  `compra`, `view_purchases`, `manage_purchases`.
- Linha **Compras** na tela de Cargos (Visualizar / Gerenciar), só visível com
  o módulo. Suas caixas **não entram no nível do cargo** (`PERMISSION_KEYS`
  continua só com as de sempre; `ALL_PERMISSION_KEYS` tem todas): sem isso a
  atualização rebaixaria o "Gestor" de toda loja.
- `modules/compras/` com `shared/` (types, services, constants, composables) e
  `fornecedores-produto/components/FornecedoresProdutoSection.vue`, carregada
  sob demanda no cadastro do produto (só com módulo + permissão).

**O que mudou em relação ao papel**
- **Sem coluna `padrao`.** O produto já tinha `fornecedor_id` ("fornecedor
  principal"); guardar outro "padrão" criaria duas verdades. Marcar principal
  na aba muda `produtos.fornecedor_id`; o principal aparece na aba mesmo sem
  linha própria (`id` nulo). Tirar a marca não apaga o do cadastro.
- **UNIQUE (produto, fornecedor)**, sem a embalagem: com NULL na embalagem o
  SQLite aceitaria duplicatas. Um fornecedor por produto, na embalagem em que
  a loja compra dele.
- **Sem `empresa_id`**: produto e fornecedor não têm (banco por loja).
- **Só a tabela desta fase.** Pedido, recebimento e log nascem cada um com a
  sua migration, na fase que os usa — tabela sem código que a use é schema
  para errar depois.
- **Cancelar pedido (`delete_purchases`)** fica para a fase 2, junto do pedido.
- **Achado no cálculo:** o estoque é Float, e um saldo de 0,8 kg guardado como
  0,7999999999999999 fazia a sugestão pedir 13 em vez de 12. A quantidade é
  arredondada no grama (3 casas) antes da conta — teste
  `test_resto_de_ponto_flutuante_nao_compra_um_fardo_a_mais`.

- **Achado na revisão:** o formulário do produto guarda o `fornecedor_id` de
  quando abriu; trocar o principal na aba e depois clicar "Salvar Alterações"
  do produto desfaria a troca. A aba avisa o formulário (`principalAlterado`)
  e o campo passa a ter o novo valor.

**Verificado:** 18 testes do cálculo; 25 de API/serviço/migração
(`test/api/v1/compras/`); 6 do frontend (`acessoCompras.spec.ts`). Suíte
do backend: 1901 antes → 1944 depois (as 43 novas), com a trava
`test_a_lista_de_excecao_e_estreita` atualizada de propósito para incluir
COMPRAS. Frontend: 137 testes; `vue-tsc` limpo; `vite build`.
**Não verificado:** a aba num app rodando (exige licença com `COMPRAS`, que a
plataforma ainda não emite). **Falta:** `npm run build:sidecar` antes de
qualquer instalador; cadastrar `COMPRAS` na plataforma web.

---

## 13. Entrega da fase 2 — Pedido (03/10/2026)

**Backend**
- Migration `b7d2f4a9c315` (revisa `a1c4e7b20d93`): `pedidos_compra`
  (`numero` único → "PC-000123"), `pedido_compra_itens`,
  `pedido_compra_parcelas`, `compras_log`. Só cria; decide pela ausência de
  cada tabela; idempotente.
- `services/compras/parcelas.py` (puro): "30/60/90", "28 dd", "à vista" →
  parcelas; o resto dos centavos vai na última; o que não dá para entender é
  recusado em vez de adivinhado.
- `services/compras/pedidos.py`: criar/editar rascunho, enviar, mudar
  previsão/observação (rascunho e enviado), voltar a rascunho (motivo),
  cancelar (motivo), texto do WhatsApp, histórico.
- `services/compras/necessidades.py`: abaixo do mínimo, descontando o que está
  a caminho; rascunho avisa mas não desconta; fornecedor sugerido (principal →
  mais barato → primeiro); `alternativa` mais barata (D18); gerar um rascunho
  por fornecedor com preço, embalagem e prazo do cadastro.
- Rotas novas em `/compras`: `necessidades`, `necessidades/gerar-pedidos`,
  `parcelas/simular`, `produtos?busca=` (busca do próprio módulo: o comprador
  não precisa da permissão de Produtos), `pedidos` (GET/POST),
  `pedidos/{id}` (GET/PUT/PATCH), `pedidos/{id}/enviar|voltar-rascunho|cancelar|whatsapp`.
- Permissão nova: `delete_purchases` (caixa **Excluir** da linha Compras) =
  cancelar pedido.

**Frontend**
- Menu **Compras** (Necessidades, Pedidos), rotas `/compras/necessidades` e
  `/compras/pedidos` com `exigeModulo: COMPRAS`.
- `modules/compras/necessidades/views/NecessidadesView.vue`;
  `modules/compras/pedidos/` (`PedidosView`, `PedidoFormModal`,
  `PedidoDetalheModal`, `PedidoCompraPrint`); `shared/` ganhou `useCompras`,
  `situacoes`, `SituacaoPedidoBadge`, `MotivoModal`.
- WhatsApp abre `wa.me` pelo `plugin-opener` com o texto pronto; sem celular
  no fornecedor, copia o texto. "Imprimir / PDF" usa a folha A4 do pedido.

**O que mudou em relação ao papel**
- **Menu por `featureFlag`, não cadeado.** `requiredModule` mostraria o item
  travado para TODA loja, contra o C11 e anunciando algo que a plataforma
  ainda não vende. Igual à NF-e. Para vender pelo cadeado depois: trocar por
  `requiredModule: MODULOS.COMPRAS` no item (comentado no código).
- **Sem `pedido_compra_origens` ainda.** Na fase 2 a única origem é o estoque
  mínimo; a tabela nasce com a origem `OS` na fase 6, quando ela importa.
- **Parcelas não se digitam na tela.** Saem da condição; o backend aceita
  lista explícita (que precisa fechar o total) para quando a tela pedir.
- **"Marcar como enviado" é separado do WhatsApp:** mandar a mensagem não
  prova que o fornecedor recebeu, e há quem peça por telefone ou e-mail.
- **Número do pedido:** `max + 1` com `UNIQUE`; dois terminais criando no mesmo
  instante fariam um deles receber erro (raro; tratar se aparecer).

**Verificado:** 125 testes de compras e vizinhos (pedido, necessidades,
parcelas, busca, migrações, entrada por XML, trava do módulo). Suíte do backend:
2004 passaram, 1 pulado, nenhuma falha. Frontend: 137 testes, `vue-tsc` limpo,
`vite build`.
**Não verificado:** as telas num app rodando (exige licença com `COMPRAS`).
**Falta:** `npm run build:sidecar`; a plataforma emitir `COMPRAS`.

---

## 14. Entrega da fase 3 — Recebimento (03/10/2026)

**Backend**
- Migration `c3e8a1f5d927` (revisa `b7d2f4a9c315`): `recebimentos_compra`,
  `recebimento_compra_itens`, e as colunas nulas
  `movimentacoes_estoque.recebimento_compra_id` (FK) e
  `contas_pagar.recebimento_compra_id` (sem FK, como `parcelamento_id`). Só
  acrescenta; decide pela ausência de cada tabela e coluna.
- Origem nova no livro de estoque: `COMPRA` (texto, sem migration).
- `services/compras/recebimentos.py`:
  - entrada pelo MESMO `registrar_movimentacao` (unidades = qtd × fator; custo
    real por unidade, meio para cima) → recalcula o custo médio;
  - pedido PARCIAL/RECEBIDO; "encerrar saldo" junto do recebimento ou depois
    (`POST /pedidos/{id}/encerrar`, só PARCIAL);
  - último preço do fornecedor atualizado;
  - contas a pagar (só com FINANCEIRO): as parcelas do pedido proporcionais ao
    que chegou; o frete/desconto vai proporcional e a ÚLTIMA chegada (ou a que
    encerra o saldo) leva o resto — a soma fecha o pedido ao centavo;
  - histórico `RECEBIDO` / `SALDO_ENCERRADO`.
- Pedido passou a trazer `pendente` e `codigos_barras` por item e a lista de
  `recebimentos`; listagem ganhou `a_receber=true`.
- Permissões: linha **Recebimento** (`recebimento_compra`, `view_receiving`,
  `receive_purchases`) para o almoxarife — vê pedidos SEM preço e dá entrada;
  o custo que ele mandar é ignorado (vale o do pedido). Quem gerencia compras
  também recebe.

**Frontend**
- `modules/compras/recebimento/` (`RecebimentoView` + `ConferenciaRecebimento`),
  rota `/compras/recebimento`, item **Recebimento** no menu.
- Conferência em cartões (balcão e celular): leitor soma 1 por bipe; bipar a
  UNIDADE num item comprado em fardo AVISA em vez de somar (somar 1 fardo por
  uma lata daria entrada em 11 que não vieram); +/−; custo real só para quem
  vê custo, com aviso quando difere do pedido.
- Detalhe do pedido: coluna "Chegou", lista de recebimentos, botões
  **Receber / Receber o resto** e **Encerrar saldo**.
- Cargos: linha Recebimento grava a PRÓPRIA chave (`recebimento_compra`); se
  usasse `compra`, a segunda linha sobrescreveria a primeira.

**O que mudou em relação ao papel**
- **Não se recebe mais do que falta** (422 com a mensagem). Entrega a mais
  exige ajustar o pedido antes; tolerância de divergência fica com a XML (fase 4).
- **Sem `pedido_compra_origens`** (continua para a fase 6).
- **Recebimento NÃO é offline** (D17): celular/tablet na rede da loja.

**Verificado:** 19 testes de recebimento (estoque, custo médio, parcial +
resto fechando ao centavo, encerrar saldo, sem Financeiro, almoxarife sem
preço, erro no meio sem nada pela metade, necessidades após parcial) + a
migration. Suíte do backend: 2025 passaram, 1 pulado, nenhuma falha. Frontend:
138 testes, `vue-tsc` limpo, `vite build`.
**Não verificado:** as telas num app rodando, e o leitor de verdade.
**Falta:** `npm run build:sidecar`; a plataforma emitir `COMPRAS`.

---

## 15. Entrega da fase 4 — Nota × Pedido (04/10/2026)

**Princípio:** a entrada por XML está em produção e continua dona do estoque.
O pedido só é CONFERIDO e marcado como recebido. Sem o módulo COMPRAS, ou
sem pedido aberto do fornecedor, prévia e importação ficam idênticas (os 14
testes antigos da XML passam sem nenhuma mudança neles).

**Backend**
- `services/compras/nota_pedido.py`: `modulo_compras_ativo` (nega sem
  resposta), `pedidos_abertos`, `casar` (a menos, a mais, sobra que não fecha a
  embalagem, preço acima de 2% do combinado, o que não veio, item fora do
  pedido — tudo AVISO, D11) e `receber_pela_nota`.
- Prévia (`/estoque/nfe-entrada/ler`) ganhou campos OPCIONAIS:
  `pedidos_abertos`, `pedido_sugerido_id` (o enviado mais recente),
  `pedido_avisos` (geral) e `itens[].pedido_avisos`.
- Importação aceita `pedido_id` (opcional). Valida módulo, situação e mesmo
  fornecedor ANTES de lançar qualquer item. O estoque entra uma vez, pela XML
  (origem NFE_ENTRADA); as movimentações ganham `recebimento_compra_id`; o
  recebimento grava `nota_entrada_id` (migration `d5f1b2c8e604`, coluna nula).
- Contas (D8): nota COM duplicatas → as da nota, e as do pedido NÃO nascem;
  nota SEM duplicatas → as parcelas do pedido sobre o valor da nota para os
  itens do pedido. Nunca em dobro.
- Resultado da importação: `pedido_codigo`, `pedido_situacao`, `pedido_avisos`.

**Frontend** (`EntradaXmlModal`, módulo de produtos)
- Bloco "Ligar ao pedido" só quando a prévia traz pedidos abertos; avisos por
  item e gerais; opção "Lançar pelas parcelas do pedido" quando a nota não tem
  duplicatas; resumo com o pedido e as divergências. Tipos novos opcionais.

**O que mudou em relação ao papel**
- **Divergência só avisa** (D11): nada bloqueia; a tolerância de preço é fixa
  em 2% por enquanto (constante `TOLERANCIA_PRECO_BP`).
- **O que chega a mais entra no estoque** (é o que a nota diz), mas o pedido
  só conta até o que faltava.
- **Frete:** o custo da nota já traz frete por item; o recebimento pela nota
  grava ajuste zero. Se um pedido for recebido parte por XML e parte à mão, a
  última chegada manual leva o frete inteiro do pedido — caso raro, anotado.
- **Avisos item a item só para o pedido sugerido;** escolhendo outro, as
  diferenças aparecem no resumo depois da entrada.

**Verificado:** 13 testes novos (sem o módulo nada muda; sugere o pedido;
preço e quantidade; o que não veio; estoque uma vez; parcial; contas com e sem
duplicatas; outro fornecedor, cancelado, sem o módulo — sem gravar nada) +
migration. Suíte do backend: 2039 passaram, 1 pulado. Frontend: 138, `vue-tsc`
limpo, `vite build`.
**Não verificado:** a tela com uma nota real num app rodando.

---

## Fontes

- Bling — pedidos de compra: <https://ajuda.bling.com.br/hc/pt-br/articles/360037519134-Como-criar-pedidos-de-compra-no-Bling>
- Bling — transições de situação: <https://ajuda.bling.com.br/hc/pt-br/articles/4411995102871-Gerenciador-de-transi%C3%A7%C3%B5es-para-situa%C3%A7%C3%B5es-de-pedidos-de-compra>
- Olist — ordens de compra: <https://ajuda.olist.com/compras/ordens-de-compra>
- Olist — gestão de compras e necessidades: <https://olist.com/sistema-erp/gestao-de-compras/>
- Omie — requisição de compra: <https://ajuda.omie.com.br/pt-BR/articles/1429150-cadastrando-uma-requisicao-de-compra>
- Omie — NF-e associada ao pedido: <https://ajuda.omie.com.br/pt-BR/articles/1429543-associando-a-nf-e-do-fornecedor-com-um-pedido-de-compra>
- Sankhya — recebimento de mercadorias: <https://ajuda.sankhya.com.br/hc/pt-br/articles/360044613034-Recebimento-de-Mercadorias>
- TOTVS — tolerância de recebimento: <https://centraldeatendimento.totvs.com/hc/pt-br/articles/360006558892-Cross-Segmentos-Totvs-Backoffice-Protheus-SIGACOM-Como-utilizar-a-Toler%C3%A2ncia-de-Recebimento-no-m%C3%B3dulo-de-Compras>
- Promob — MRP e lista de compras: <https://promob.com/blog/promob-para-marcenarias-como-ele-ajuda-a-aumentar-a-capacidade-produtiva/>
