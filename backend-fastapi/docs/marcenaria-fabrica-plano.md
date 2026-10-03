# Plano: Marcenaria-fábrica (projeto → orçamento → produção → compra → instalação)

Escrito em 04/10/2026, na branch `feat/compras`. Junta três fontes:

1. o **resumo do Alan** — "Módulo de Compras para Marcenaria — Especificação de
   Requisitos" (RC01–RC20, RNC01–RNC05, DC1–DC7, OS em 11 estados);
2. o **plano do segmento** (`docs/segmento-marcenaria-plano.md`, 16/09) e as
   decisões que o dono da fábrica tomou naquele dia;
3. o **código de hoje**, incluindo o módulo de Compras (fases 1–6,
   `docs/compras-plano.md`).

**Nada começa a ser codado antes da §2 (o conflito) e da §4 (decisões)
estarem respondidas pelo dono da fábrica.**

---

## Resumo em uma página

A marcenaria de hoje no StartBig é uma **OS de balcão bem vestida**: tipo de
trabalho (Planejados / Reforma), ambiente, módulos em texto, endereço da obra,
adiantamento, aprovação por item e um campo **Etapa** só informativo. O preço
vem do catálogo. Funciona para a marcenaria de bairro.

A **fábrica de planejados** precisa de outra coisa: orçar **por móvel, com a
lista de material** (chapa, fita, ferragem) e o fator de perda; aprovar e
**congelar** o orçamento; **comprar** o que falta só depois do sinal; separar,
produzir, instalar — com **travas** entre as etapas e a **margem real**
comparada com a orçada.

A boa notícia: metade disso já existe. O "item da OS congelado" do resumo é o
`OrdemServicoItem` de hoje (produto, quantidade, custo congelado), e o módulo
de Compras (fase 6) **já reserva, sugere a compra, liga o pedido à OS e mostra
o painel "Compras desta OS"** em cima dele. O que falta é o **começo**
(projeto e orçamento por móvel com lista de material) e o **trilho** (as 11
etapas com travas).

| Já existe | Falta (este plano) |
|---|---|
| Segmento Marcenaria: tipos, ambiente, endereço da obra, Etapa (informativa) | **Projeto (PRJ)** e **orçamento em árvore**: ambiente → móvel → lista de material |
| Adiantamento (valor), aprovação por item | **Sinal** que libera a compra e a produção (RC04) |
| OS com itens de produto e custo congelado | **Aprovar o orçamento gera a OS**, já com a perda na quantidade (RC01) |
| Compras: reserva calculada, necessidade por OS, pedido × OS, painel, recebimento, contas | **Unidade de consumo × compra** (m² × chapa) no insumo (RC02) |
| Baixa de estoque ao fechar a OS | **11 etapas com travas** e log (RC20, RC18) |
| — | **Margem orçada × real** (RC14), **central de corte** (RC15/16), **separação com bipagem** |

**Custo estimado: 4 a 6 semanas de código**, em 6 entregas que já servem uma de
cada vez (§8). A primeira entrega útil (orçamento por móvel que gera a OS) sai
em ~1,5 semana.

---

## 0. O que "pronto" significa

| # | Critério de aceite | Hoje |
|---|---|---|
| F1 | Cadastrar **insumos** (chapa, fita, ferragem) com unidade de consumo e de compra (m² × chapa) e a marca "sofre perda" | o produto não sabe converter m² em chapa |
| F2 | Abrir um **Projeto PRJ-000123** do cliente, com endereço da obra | o endereço é campo da OS |
| F3 | Montar o **orçamento**: ambientes → móveis (com medidas) → lista de material, com o custo puxado do cadastro | só itens soltos do catálogo |
| F4 | Ter **versões** do orçamento e aprovar uma só | não existe |
| F5 | Aprovar **gera a OS** com os insumos já com a perda (só em quem "sofre perda") e os valores **congelados** | a OS é montada à mão |
| F6 | A compra só libera **depois do sinal pago**; o gestor pode liberar antes, com justificativa no histórico | não há trava |
| F7 | As Necessidades mostram o que falta **por OS**, em chapas inteiras | **já funciona** (Compras fase 6), falta só a conversão m² → chapa |
| F8 | O almoxarife **separa bipando**; a baixa acontece na separação, não só no fechamento | a baixa é no fechamento |
| F9 | A OS segue as **11 etapas** e o botão de avançar diz **o que trava** | Etapa é campo livre |
| F10 | A Visão Geral mostra **margem orçada × real** | não existe |
| F11 | A **central de corte** é um pedido de serviço ligado ao móvel | não existe |
| F12 | **Oficina, assistência, serigrafia, PDV e a marcenaria de bairro continuam idênticos** | cláusula de não-regressão |

F12 manda em todo o resto.

---

## 1. Onde estamos (04/10/2026)

**Segmento Marcenaria** (`core/segmentos/definicoes/marcenaria.py`): tipos
*Planejados* e *Reforma de móveis*; campos `nome_projeto`, `endereco_obra`,
`ambiente` (lista fechada), `modulos` (lista de texto), `etapa` com as
palavras do dono (*Aguardando aprovação → Aguardando material → Separação →
Corte → Montagem interna → Montagem externa → Concluído*). Capacidades:
aprovação por item, garantia por prazo, imagem na entrada.

**Decisões do dono em 16/09** (plano do segmento, §3):
1. dois tipos de trabalho;
2. **Etapa é campo, não workflow** — sem automação, sem trava;
3. "Aguardando Peças" fica como status (a Etapa diz "Aguardando material");
4. adiantamento em valor;
5. **preço vem do catálogo** — "nenhum motor de m² ou de chapa".

**Módulo de Compras** (fases 1–6, `feat/compras`): fornecedores do produto,
necessidades (mínimo, venda e **OS**), pedido, recebimento com bipagem e
parcial, XML × pedido, contas a pagar, previsão no fluxo, relatórios,
**reserva calculada pelas OS abertas** (peça aprovada = estoque com dono),
**pedido ligado à OS** e **painel "Compras desta OS"** (RC03, RC06, RC08).

**OS hoje:** 7 status comuns a todos os segmentos (ABERTA, EM_ANDAMENTO,
AGUARDANDO_PECAS, AGUARDANDO_APROVACAO, AGUARDANDO_RETIRADA, FINALIZADA,
CANCELADA); itens com produto, quantidade (decimal), valor e
`custo_unitario` congelado; baixa do estoque ao **finalizar**.

---

## 2. O conflito a resolver ANTES de tudo

O resumo do Alan e as decisões do dono em 16/09 **dizem coisas diferentes**:

| Tema | Dono, 16/09 | Resumo do Alan |
|---|---|---|
| Etapas | Informação para o dono; "não avança sozinha, não trava" | 11 estados com **travas** e log obrigatório |
| Preço | Do catálogo ("cozinha — metro linear"); **sem motor de chapa** | Orçamento em árvore com **lista de material por móvel** e perda |
| Compra | — | Só depois do **sinal**; necessidade por insumo × OS |

Não é erro de ninguém: 16/09 foi a **marcenaria de balcão** (as duas lojas
começando), o resumo é a **fábrica** funcionando de verdade. Mas as duas não
cabem na mesma tela sem uma escolha.

**Recomendação (D0): "Modo fábrica", ligado POR LOJA.**
- Desligado (padrão): a marcenaria fica **exatamente** como está — o que a
  marcenaria de bairro usa hoje e o que o dono decidiu em 16/09.
- Ligado (a fábrica de planejados): aparecem Projetos/Orçamento por móvel, as
  11 etapas com travas, a separação bipada e a margem.
- É uma configuração da loja (como "usar embalagens"), não um segmento novo —
  o cadastro, a OS e os relatórios continuam os mesmos.

**Pergunta ao dono da fábrica:** *"Hoje você quer o sistema travando a etapa
(não deixa ir para Produção sem o material separado) ou só mostrando onde cada
móvel está?"* A resposta decide se este plano começa.

---

## 3. A ideia

```
 PROJETO PRJ-000123  (cliente, endereço da obra, medição + fotos)
   └─ ORÇAMENTO v1, v2, v3…   (perda %, sinal %, validade)   ← uma versão é aprovada
        └─ AMBIENTE  (Cozinha, Suíte…)
             └─ MÓVEL  (Armário aéreo 1800×700×350, terceirizado?)
                  └─ LISTA DE MATERIAL  (insumo, consumo em m²/m/un, custo copiado)

 APROVAR ─► gera a OS (a OS de hoje), CONGELADA:
             item da OS = cada linha da lista de material, com a PERDA na
             quantidade (só insumo que "sofre perda") e o custo do dia
         ─► Compras já faz o resto: reserva calculada, necessidade em chapas,
             pedido ligado à OS, recebimento, contas, painel da OS

 SINAL pago ─► libera a compra (RC04) e a etapa "Separação e compra"
 SEPARAÇÃO bipada ─► baixa no estoque NA HORA (não só ao fechar a OS)
 TRAVAS entre as 11 etapas (RC20) ─► log de cada transição (RC18)
 BAIXA ─► custo REAL no item ─► margem orçada × real (RC14)
```

**Por que gerar a OS de hoje, e não tabelas novas `os_ambiente/os_movel/os_item`
(como o resumo propõe):** o item da OS já tem quantidade, valor e custo
congelado, e TODO o módulo de Compras (fase 6) já trabalha em cima dele.
Tabelas paralelas obrigariam a refazer reserva, necessidade, pedido × OS e
painel — e criariam duas OS diferentes no mesmo sistema. O item da OS ganha só
duas colunas opcionais (ambiente e móvel) para agrupar a tela e a impressão.

---

## 4. Decisões

### 4.1 Do resumo do Alan (DC1–DC7), com recomendação

| # | Decisão | Recomendação |
|---|---|---|
| DC1 | Compra antes do sinal | **Proibida por padrão**; o gestor libera por OS, com justificativa no histórico (RC04) |
| DC2 | Alocação do que chega | **Data de instalação**; sem ela, data de aprovação; o gestor pode mudar (RC12). Hoje a fila de Compras é por abertura da OS — muda para instalação quando a OS tiver a data |
| DC3 | Perda na quantidade | **Na quantidade também**, para reserva e compra (RC01) — sem isso o corte para no meio |
| DC4 | Título a pagar | **No recebimento, proporcional** — já é assim no módulo de Compras (D8) |
| DC5 | Custo para o almoxarife | **Oculto** — já é assim (linha Recebimento de Cargos, D14) |
| DC6 | Montador terceirizado | Depende da loja piloto (RC17) — pergunta §11 |
| DC7 | Sobra de chapa | **Volta ao saldo livre** depois da separação da OS |

### 4.2 Novas (deste plano)

| # | Decisão | Recomendação | Por quê |
|---|---|---|---|
| D0 | Modo fábrica | **Configuração por loja**, desligada por padrão (§2) | Não quebrar a marcenaria de balcão nem a decisão de 16/09 |
| D1 | Onde mora a OS da fábrica | **A OS de hoje**, gerada pela aprovação (§3) | Reaproveita Compras inteiro; uma OS só no sistema |
| D2 | Insumo | **Produto do catálogo** com 3 campos novos: `unidade_consumo` (M2, M, UN), `consumo_por_unidade` (inteiro: mm² por chapa, mm por rolo) e `sofre_perda` | Sem cadastro paralelo; estoque, compra e XML continuam iguais |
| D3 | Unidade do estoque | **A de compra** (chapa, rolo, unidade). A lista de material fala em m²/m; a conversão é na aprovação, **arredondando para cima** | É o que se conta na prateleira e o que vem na nota |
| D4 | Inteiros (RNC01) | Dentro do orçamento: **mm, mm², centavos, pontos-base**. O estoque continua decimal (D3 do plano de Compras) | Mesma regra já usada em Compras |
| D5 | Etapas | Coluna nova `fase_fabrica` na OS (só no modo fábrica); o **status de sempre** é derivado dela | Os outros segmentos não enxergam as 11 etapas |
| D6 | Baixa na separação | No modo fábrica, **bipar na separação dá a baixa** e o fechamento não baixa de novo | É o que o resumo pede (RC14) sem mudar a OS dos outros |
| D7 | Margem real | `custo_real` no item da OS, gravado na baixa; margem real = mesma fórmula da orçada | O custo congelado nunca muda (RC11) |
| D8 | Central de corte | Pedido de **SERVIÇO** (o `tipo` já existe no pedido desde a fase 2) ligado ao **móvel** | RC15/16 sem tabela nova de pedido |
| D9 | Medição | **Vistoria** do segmento (o mecanismo da oficina) com o checklist de ambiente | Plano do segmento, 5.6 |

---

## 5. Modelo de dados

Tudo novo é aditivo; migrations decidem pela ausência (modelo `965c71a2da9a`).

```
produtos  (+3 colunas, nulas/false — nada muda para quem não usa)
├── unidade_consumo      VARCHAR(4)  nulo   M2 | M | UN
├── consumo_por_unidade  INT nulo           mm² por chapa (2750×1850 = 5.087.500), mm por rolo
└── sofre_perda          BOOL default false  MDF e fita sim, ferragem não

projetos (nova)
├── id, numero (PRJ-000123), cliente_id, endereco_obra, observacao
├── medido_por, medido_em, fotos (via anexos existentes)
└── criado_em, atualizado_em

orcamentos_projeto (nova) — versões
├── id, projeto_id, versao INT, situacao  RASCUNHO | ENVIADO | APROVADO | RECUSADO | VENCIDO
├── perda_bp INT (1000 = 10%), sinal_bp INT (5000 = 50%), validade DATE
├── total INT (centavos, calculado), aprovado_em, aprovado_por
└── os_id FK nulo  ← a OS gerada na aprovação

orcamento_ambientes (nova): id, orcamento_id, nome, ordem
orcamento_moveis (nova): id, ambiente_id, nome, largura_mm, altura_mm, profundidade_mm,
                         terceirizado BOOL, custo_terceiro INT, preco_venda INT, ordem
orcamento_materiais (nova): id, movel_id, produto_id, consumo INT (na unidade de consumo),
                            custo_unitario INT (copiado do cadastro ao incluir)

ordens_servico (+ colunas nulas, só modo fábrica)
├── projeto_id, orcamento_id
├── fase_fabrica  VARCHAR(30)  ← as 11 etapas (D5)
├── data_instalacao  DATE      ← alocação (DC2) e alerta de atraso (RC08)
└── compra_liberada_por / compra_liberada_em / compra_liberada_motivo  (RC04)

ordem_servico_itens (+ colunas nulas)
├── ambiente, movel        VARCHAR — agrupar tela e impressão
├── movel_orcamento_id     FK nulo
├── separado_em            DATETIME nulo  ← baixa na separação (D6)
└── custo_real             INT nulo        ← margem real (D7)

os_fases_log (nova) — só INSERT (RC18)
└── os_id, fase_anterior, fase_nova, usuario, ocorrido_em, motivo
```

**Cálculo da quantidade na aprovação (RC01 + RC02 + D3), puro e testado:**

```
consumo_com_perda = ⌈ consumo × (10000 + perda_bp) ÷ 10000 ⌉   (só se sofre_perda)
quantidade_os     = ⌈ consumo_com_perda ÷ consumo_por_unidade ⌉ (em chapas/rolos)
```

Exemplo do resumo: 12 m² de MDF, 10% de perda, chapa 2750×1850 →
13,2 m² → 2,59 chapas → **3 chapas** na OS. A necessidade de compra já
desconta o estoque livre e o que está a caminho (Compras fase 6).

---

## 6. As 11 etapas (modo fábrica)

| Etapa (`fase_fabrica`) | Responsável | Trava para sair | Status de sempre |
|---|---|---|---|
| Medição | Projetista | Medidas e fotos anexadas | ABERTA |
| Em elaboração | Comercial | Orçamento com ao menos 1 móvel | ABERTA |
| Aguardando aprovação | Comercial | Cliente aceita (ou vence) | AGUARDANDO_APROVACAO |
| Aprovado | Comercial | Automático: gera a OS e reserva | AGUARDANDO_APROVACAO |
| Aguardando sinal | Financeiro | Sinal liquidado no financeiro | AGUARDANDO_APROVACAO |
| Separação e compra | Almoxarife | Todos os insumos recebidos **e separados** (RC20) | AGUARDANDO_PECAS |
| Em produção | Marceneiro | Todos os móveis na última etapa de fábrica | EM_ANDAMENTO |
| Pronto para expedição | Gestor | Checklist de expedição + instalação agendada | EM_ANDAMENTO |
| Em instalação | Montador | Instalação concluída | EM_ANDAMENTO |
| Vistoria | Montador / cliente | Termo assinado; pendência volta para instalação | AGUARDANDO_RETIRADA |
| Entregue | Financeiro | Saldo coberto | FINALIZADA |

- O **status de sempre** é derivado: relatórios, dashboard e a lista de OS
  continuam funcionando sem saber das 11 etapas.
- **Retroceder ou cancelar exige motivo**; toda transição vai para o log.
- O botão de avançar mostra a trava que falta ("3 itens em pedido").

---

## 7. Do resumo ao código (RC01–RC20)

| RC | O que é | Onde fica | Situação |
|---|---|---|---|
| RC01 | Reserva com perda | Aprovação gera a OS com a perda | Fase F2 |
| RC02 | Consumo × compra, arredonda para cima | Produto + cálculo puro | Fase F1 |
| RC03 | Necessidade por insumo, todas as OS | **Compras fase 6** | ✅ feito |
| RC04 | Compra só após o sinal (ou liberação) | Necessidades filtram OS sem sinal | Fase F3 |
| RC05 | Pedido por fornecedor, último preço | **Compras fase 2** | ✅ feito |
| RC06 | Pedido × itens da OS | **Compras fase 6** (`pedido_compra_origens`) | ✅ feito |
| RC07 | Status de compra no item da OS | **Painel "Compras desta OS"** | ✅ feito (por peça) |
| RC08 | Previsão × instalação | Painel avisa contra a previsão; passa a usar `data_instalacao` | Fase F3 |
| RC09 | Cancelar OS libera reserva | Reserva é calculada: OS cancelada já sai | ✅ feito |
| RC10 | Recebimento bipado e parcial | **Compras fase 3** | ✅ feito |
| RC11 | Custo real no livro, sem mexer na OS | **Compras fase 3** | ✅ feito |
| RC12 | Alocação por data de instalação | Fila de Compras ordena por `data_instalacao` | Fase F3 |
| RC13 | Título a pagar no recebimento | **Compras fase 3** | ✅ feito |
| RC14 | Custo real × congelado, margem | Baixa na separação grava `custo_real` | Fase F4 |
| RC15 | Central de corte = pedido de serviço do móvel | Pedido tipo SERVIÇO ligado ao móvel | Fase F5 |
| RC16 | Custo real do serviço × orçado | Idem | Fase F5 |
| RC17 | Montador terceirizado | Depende do piloto | A decidir |
| RC18 | Log de pedido, alocação, liberação | `compras_log` (✅) + `os_fases_log` | Fase F3 |
| RC19 | Almoxarife/marceneiro sem preço | Cargos (✅ em Compras) + telas da fábrica | Fases F3–F4 |
| RC20 | Trava em "Separação e compra" | Máquina de etapas | Fase F3 |

**Já feito no módulo de Compras: 9 dos 20.**

---

## 8. Fases de entrega

| Fase | Entrega | Pronto quando | Esforço |
|---|---|---|---|
| **F0** | Este plano lido pelo dono; D0 e §11 respondidas; modo fábrica decidido | Respostas por escrito | conversa |
| **F1 — Insumo** | Unidade de consumo, consumo por unidade e "sofre perda" no produto; cálculo puro com os exemplos do resumo | Testes do cálculo passam; produto comum não muda | 2–3 dias |
| **F2 — Projeto e orçamento** | Projeto PRJ, orçamento em árvore com versões, lista de material por móvel, impressão do orçamento; **aprovar gera a OS** com perda e custo congelado | Aprovar um orçamento de cozinha gera a OS certa e as Necessidades já pedem as chapas | 1,5–2 semanas |
| **F3 — Trilho** | Modo fábrica; 11 etapas com travas e log; sinal libera a compra (com liberação antecipada); `data_instalacao` na fila e no alerta | A OS não sai de "Separação e compra" com item faltando, e o botão diz por quê | 1 semana |
| **F4 — Separação e margem** | Tela de separação bipada (desktop e celular); baixa na separação; custo real; margem orçada × real na Visão Geral | Separar todos os itens libera a produção; a margem real aparece | 1 semana |
| **F5 — Terceirizados** | Central de corte (pedido de serviço do móvel, status nas etapas); custo real × orçado; montador se DC6 pedir | Um móvel terceirizado anda pelas etapas com o pedido de serviço | 3–5 dias |
| **F6 — Depois do piloto** | Cotação, estoque mínimo de alto giro (fita, dobradiça — já existe em Compras), relatório de margem por projeto, retrabalho | Pedido da loja piloto | — |

Cada fase: testes, prova de que **os outros segmentos não mudaram**,
`build:sidecar`, loja canário com backup.

---

## 9. O que NÃO entra

- **Projeto 3D / importar do Promob** — outro produto (plano do segmento §6).
- **Plano de corte otimizado** (encaixar peças na chapa) — é o que o Promob Cut
  e o Corte Certo fazem; aqui a perda é o **fator %**.
- **Kanban de produção / PCP de máquinas** — a etapa é por OS, não por peça.
- **Offline no celular** (RNC02) — o app não tem sincronização; a separação
  funciona no celular **na rede da loja**.
- **Orçamento por m² automático para a marcenaria de bairro** — continua pelo
  catálogo (decisão de 16/09).

---

## 10. Riscos

- **Código compartilhado da OS.** A OS é a mesma de três segmentos em produção.
  Tudo da fábrica entra por **colunas nulas** e **modo ligado por loja**; a
  prova "antes × depois" dos outros segmentos é obrigatória em cada fase.
- **Baixa em dois lugares.** No modo fábrica a baixa passa para a separação; o
  fechamento não pode baixar de novo. Teste de "separou e finalizou = uma
  baixa só" antes de qualquer loja.
- **Status derivado.** Se a derivação errar, a OS some do filtro certo na lista
  e no dashboard. Tabela da §6 vira teste.
- **Conversão m² → chapa.** Erro aqui compra a menos ou a mais em silêncio.
  Cálculo puro, com os exemplos do resumo como teste (RNC04).
- **Sidecar e PyArmor** — como em todo o resto.

---

## 11. Perguntas para o dono da fábrica (piloto)

1. **D0:** quer **travar** as etapas ou só **ver** onde cada móvel está?
2. Qual o **prazo típico** do fornecedor de chapa? (Define se a compra
   antecipada — DC1 — vai ser exceção ou rotina.)
3. Compra o mesmo insumo de **mais de um fornecedor**? (Compras já suporta;
   é para saber o que mostrar primeiro.)
4. O pedido à **central de corte** é feito pelo software de corte ou por
   e-mail/WhatsApp? (Define o que o pedido de serviço precisa guardar.)
5. Alguém **confere a nota** na chegada do material? (Compras já liga XML ×
   pedido; é para saber se vai usar.)
6. **Sobra de chapa** é reaproveitada em outros projetos? (Confirma DC7.)
7. **Montador:** funcionário ou contratado por instalação? (DC6 / RC17.)
8. O **sinal** padrão é 50%? Muda por cliente?
9. Quem **mede** e quem **orça** são pessoas diferentes? (Perfis e etapas.)
10. A lista de **ambientes** (Cozinha, Dormitório, Closet, Banheiro, Sala,
    Escritório, Área de serviço, Outro) está certa?

---

## Fontes

- Resumo do Alan: "Módulo de Compras para Marcenaria — Especificação de
  Requisitos" (RC01–RC20, RNC01–RNC05, DC1–DC7).
- `docs/segmento-marcenaria-plano.md` (16/09/2026) — fluxo e decisões do dono.
- `docs/compras-plano.md` — módulo de Compras, fases 1–6 (§12–§17).
- Mercado (pesquisa de 16/09): Calcme, GestorMarceneiro, Planejados Pro,
  WoodOrça+, Promob (ERP/MRP, Cut Pro), Corte Certo.
