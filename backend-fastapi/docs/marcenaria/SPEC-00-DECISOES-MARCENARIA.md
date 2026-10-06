# Spec 00 — Registro de Decisões do Segmento Marcenaria

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                       |
| Camada       | Documento                                                             |
| Dependências | Nenhuma                                                               |
| Bloqueia     | Todas as specs da marcenaria (01 a 14)                                |
| Referência   | Conversa de 05–06/10/2026; Figma (7 telas); PDF "Módulo Marcenaria: Plano de Implementação"; `docs/segmento-marcenaria-plano.md` (16/09) |
| Branch       | `feat/segmento-marcenaria` @ `f040e8d`                                |

---

## 1. Objetivo

Registrar, em um só lugar, **tudo o que foi combinado** sobre o segmento marcenaria antes de escrever qualquer spec de código. Toda spec seguinte cita as decisões deste documento pelo código (ex.: "C3", "O4") em vez de repetir o raciocínio.

Este documento **substitui** o `docs/segmento-marcenaria-plano.md` de 16/09/2026. Aquele plano descrevia um segmento simples (só campos na OS, preço pelo catálogo) e partia da premissa de "duas lojas esperando". As duas premissas mudaram (§3).

O PDF de requisitos e o Figma foram usados **só como inspiração**. Onde eles divergem do padrão do StartBig, vale o padrão do StartBig.

## 2. Escopo

**Dentro do escopo**
- Princípios que valem para todas as specs (§4).
- Decisões de negócio e de experiência do usuário, por bloco (§6).
- O que fica fora da fase 1 (§7).
- Lista de specs, ordem e dependências (§8).

**Fora do escopo**
- Código, contratos de API e telas: cada spec cuida do seu.
- Textos jurídicos do Termo de Entrega e da proposta comercial (redigidos com o dono da fábrica nas Specs 07 e 13B).

---

## 3. Contexto: o que existe hoje e o que mudou

**O que já existe na branch** (e continua valendo):

| Peça | Onde | Uso nesta fase |
|------|------|----------------|
| Segmento `marcenaria` ligado no registry, com os tipos "Móveis planejados" e "Reforma de móveis" | `app/core/segmentos/definicoes/marcenaria.py` | Base; ajustado na Spec 03 |
| Identificador gerado `PRJ-AAAA-NNNNNN` | registry (`identificador`) | Código do projeto nas etiquetas |
| Objeto de serviço "Projeto" (nome + endereço da obra) | registry + `objeto_servico` | É o "Projeto" do orçamento (O5) |
| Abas da OS ligadas por capacidade (ex.: Vistoria da oficina) | `OSFormTabsContent.vue` + `capacidades.py` | Mecanismo das abas novas (T1) |
| Livro-razão único do estoque | `services/movimentacao_estoque.registrar_movimentacao` | Baixa da separação (E2) |
| Comissão por funcionário sobre o **lucro** dos itens de serviço | `db/crud/relatorio.get_comissao_base` | Comissão do vendedor sem código novo (C5) |
| Contas a pagar | `db/models/conta_pagar.py` | RT do arquiteto, terceirizados (C5, E6) |
| Permissões por cargo (JSON) | `db/models/cargo.py` | "Ver custos" (P4) |
| `produto.localizacao_estoque`, `produto.fornecedor_id`, `produto.codigo_barras` | `db/models/produto.py` | Endereço no almoxarifado, lista de compras, leitor |
| Consulta de CNPJ (BrasilAPI, só frontend) | `modules/enterprise/composables/useConsultaCNPJ.ts` | Levada ao cadastro de cliente (Spec 02) |

**O que mudou desde 16/09:**

| Antes | Agora |
|-------|-------|
| "Duas lojas esperando", instalador em andamento | **Nenhuma loja usa o segmento.** Não há OS de marcenaria gravada em banco de cliente. O `marcenaria.py` pode mudar sem migração de dados |
| Preço só pelo catálogo; "nenhum motor de chapa" | **Orçamento técnico** por ambiente e móvel, com BOM, perda, markup e margem |
| Etapa é campo informativo | **Etapas por móvel** na produção |

---

## 4. Princípios (valem para todas as specs)

| # | Princípio | Consequência prática |
|---|-----------|----------------------|
| PR1 | **Não quebrar o que funciona.** Oficina, informática e serigrafia continuam idênticas | Toda spec que toca código compartilhado (marcada com ⚠️) tem a seção "Prova de não regressão": impressão antes × depois e suíte de testes dos três segmentos |
| PR2 | **Arquitetura escolhida: "opção 3".** O orçamento de marcenaria é um documento novo; ao ser aprovado, **gera a OS que já existe** | Nenhum status novo de OS, nenhuma tabela de OS duplicada. Pagamentos, reabertura e impressão da OS seguem como estão |
| PR3 | **Padrões do StartBig acima do PDF e do Figma** | SQLite síncrono, id inteiro, `HTTPException` com `detail`, camadas `endpoints → services → crud → models`, VeeValidate + Zod, TanStack Query |
| PR4 | **Dinheiro em centavos (`int`), percentual em basis points (`int`, 500 = 5,00%)** | Mesmo padrão do `cargo.comissao_*`. Nada de `float` em dinheiro. Conversão para R$ e % só na tela |
| PR5 | **Uma camada por spec** | Specs que têm backend e tela viram "A" (backend) e "B" (frontend) |
| PR6 | **Código em português** (CLAUDE.md) e **trechos das specs comentados linha a linha** | Os desenvolvedores do time incluem iniciantes |
| PR7 | **Backend mexeu → sidecar de novo** | Toda spec de backend termina lembrando `npm run build:sidecar` e o teto de bytecode do PyArmor |
| PR8 | **Migrações decidem pela presença do schema antigo** (CLAUDE.md) | O `create_all()` do startup cria tabelas novas vazias antes do Alembic |

---

## 5. Glossário

Os termos abaixo têm o mesmo nome no banco, na API e na tela.

| Termo | Definição |
|-------|-----------|
| Orçamento de marcenaria | Proposta técnica de preço de um projeto. Tabela `marcenaria_orcamento`. **Não confundir** com a tabela `orcamento` do PDV |
| Versão | Cópia de um orçamento para alteração. A anterior fica "Substituído" |
| Projeto | Objeto de serviço da OS de marcenaria (nome + endereço da obra). Código `PRJ-…` |
| Ambiente | Cômodo do orçamento (Cozinha, Suíte…). Agrupa móveis |
| Móvel | Peça planejada com L × A × P em mm. **Vira um item de serviço da OS** na aprovação |
| Insumo | Um **Produto** do cadastro usado num móvel (MDF, fita, ferragem) |
| BOM / ficha técnica | Lista de insumos e quantidades de um móvel |
| Sofre perda | Flag do produto: se marcada, o insumo recebe o fator de perda |
| Markup | Percentual aplicado sobre o custo para chegar ao preço de venda |
| RT (Reserva Técnica) | Comissão do arquiteto ou parceiro externo |
| Sinal | Valor adiantado combinado na aprovação (pode ser zero) |
| Separação | Retirada e conferência dos insumos de um móvel no almoxarifado |
| Etapa | Passo de produção de um móvel (corte, borda, furação…) |
| Termo de entrega | Documento impresso, por ambiente, assinado pelo cliente na obra |
| Pendência | Problema registrado no termo que impede a entrega 100% conforme |

---

## 6. Decisões

Legenda da coluna **Status**: ✅ decidida pelo usuário · 🟡 assumida (recomendação aceita em bloco; confirmar na revisão desta spec).

### 6.1. Fundação — como o orçamento se liga ao sistema

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| F1 | Todas as tabelas novas com prefixo `marcenaria_` (`marcenaria_orcamento`, `marcenaria_ambiente`, `marcenaria_movel`, `marcenaria_movel_insumo`…). Nenhuma tabela existente é alterada, exceto as colunas citadas em F6 | Já existe `orcamento` (PDV). Prefixo evita colisão e deixa claro de quem é a tabela | ✅ |
| F2 | Na aprovação, **cada móvel vira um item de serviço da OS**: `nome` = nome do móvel, `valor_unitario` = preço de venda, `custo_unitario` = custo direto (+ parte do RT, C5d). Os insumos **não** viram itens da OS | Se os insumos virassem itens, entrariam no total e o cliente pagaria duas vezes | ✅ |
| F3 | O "congelamento" é o **orçamento aprovado ficar somente leitura**. Os preços já estão gravados nos itens da OS. Mudança = nova versão (O2) | Evita duplicar 4 tabelas em `os_*` como o PDF propunha | ✅ |
| F4 | Itens da OS que vieram do orçamento ficam **travados** na OS, com o aviso "altere pelo orçamento". Itens adicionados à mão na OS continuam editáveis | Se o preço do móvel mudasse só na OS, OS e orçamento passariam a discordar e o dono perderia a confiança nos números | ✅ |
| F5 | Insumo **é** um Produto do cadastro existente (estoque, fornecedor, localização). Não há cadastro novo de insumo | Reaproveita estoque, compras e livro-razão | ✅ |
| F6 | Coluna nova `produto.sofre_perda` (`bool`, padrão `false`), exibida no cadastro de produto **só no segmento marcenaria** | A categoria do produto é texto livre (não há tabela de categorias), então a flag não pode ficar nela como o PDF sugeria | ✅ |

### 6.2. Cálculo

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| C1 | O markup incide sobre o **custo total**: material + perda + terceirizado + mão de obra | É o que o Figma já faz | ✅ |
| C2 | A perda é calculada **por insumo**, só nos produtos com `sofre_perda` | O total do ambiente fecha com a soma dos móveis (inconsistência do Figma corrigida) | ✅ |
| C3 | A **instalação** é uma linha própria do orçamento (e um item próprio da OS), **não** rateada entre os móveis | Com rateio, adicionar um móvel no quarto mudaria o preço da cozinha | ✅ |
| C3a | O markup **incide** sobre a instalação | Coerência com C1 (markup sobre todo o custo) | 🟡 |
| C4 | Mão de obra de fábrica por móvel, em uma de duas formas, à escolha do usuário em cada móvel: **valor fixo** (R$) ou **horas × custo/hora** (custo/hora nos Parâmetros) | Pedido do usuário: as duas formas | ✅ |
| C5 | Comissão do **vendedor/responsável**: módulo existente, sem código novo. Como o móvel é item de serviço com `custo_unitario`, a comissão já sai sobre a margem | Reaproveita a decisão do dono de 05/09 ("comissão sobre o lucro") | ✅ |
| C5a | O **arquiteto** é cadastrado como **Fornecedor** | Cadastro existente, com CPF/CNPJ; evita um cadastro novo de "Parceiro" | ✅ |
| C5b | O RT é calculado sobre o **preço de venda** e gera uma **conta a pagar** ao arquiteto **na finalização da OS** | Não se paga RT de obra cancelada | ✅ |
| C5c | Parâmetro "modo do RT": **sai da margem** (padrão) ou **embutido no preço** | O padrão reproduz o Figma; o outro modo é comum no mercado | 🟡 (padrão) |
| C5d | O `custo_unitario` de cada móvel na OS inclui a parte do RT daquele móvel (`preço × RT%`) | Sem isso, o vendedor recebe comissão sobre um lucro que já foi para o arquiteto. Não é rateio: cada móvel carrega exatamente o seu percentual | ✅ |
| C6 | Arredondamento **uma única vez**, no preço de cada móvel (meio centavo para cima). Ambiente e total são somas. Sinal = `arred(total × sinal%)`; saldo = total − sinal | Elimina o erro de 1 centavo do Figma (9.695,81 × 9.695,82) | ✅ |
| C7 | Sinal **livre**, decidido pelo usuário em cada orçamento; pode ser **zero**. O campo aceita **% ou R$** (digitar em um preenche o outro). Não há trava "aguardando sinal" | Pedido do usuário. A OS já registra o adiantamento (`valor_entrada`) | ✅ |
| C8 | **Um só motor de cálculo, no backend** (funções puras). A tela mostra os valores devolvidos pela API; não recalcula em TypeScript | Dois motores (Python e TS) acabariam discordando em centavos. Com o banco local, a resposta é imediata | 🟡 (decisão técnica) |

### 6.3. Ciclo de vida do orçamento

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| O1 | Status do orçamento: `RASCUNHO → ENVIADO → APROVADO`, finais `RECUSADO`, `VENCIDO` e `SUBSTITUIDO`. Os status da OS não mudam. A "Medição" do PDF **não** é status: vira anexos do orçamento (fotos e medidas) | Separar o ciclo comercial do ciclo de produção | ✅ |
| O2 | "Nova versão" copia o orçamento inteiro; a anterior vira `SUBSTITUIDO` (somente leitura). Número `ORC-AAAA-NNNNNN` + rótulo "v2". Só uma versão pode ser aprovada | Histórico do que foi oferecido ao cliente | ✅ |
| O3 | Validade padrão nos Parâmetros (15 dias), editável por orçamento. O custo do insumo é **copiado** quando entra no móvel. Ao renovar ou criar versão, o sistema avisa "N insumos mudaram de preço — atualizar?", com a diferença no total. **Nunca** muda preço sem avisar | Vendedor que já passou o valor ao cliente não pode ser surpreendido | ✅ |
| O4 | A aprovação acontece **só no orçamento**, escolhendo quais móveis o cliente aceitou. Os recusados ficam como histórico. A OS nasce só com os aprovados; o sinal é recalculado sobre o total aprovado. `CAP_APROVACAO_ITENS` sai da marcenaria | Aprovar em dois lugares faria os documentos discordarem | ✅ |
| O5 | O "Projeto" do Figma é o **objeto de serviço "Projeto"** que já existe (nome + endereço da obra) | A OS exige objeto; o cliente que volta encontra o projeto | ✅ |
| O6 | Cliente: busca ou cadastro pelo **modal de cliente que já existe**. A consulta de CNPJ entra no cadastro de cliente em **spec separada** (Spec 02), logo no início | Melhoria útil a todos os segmentos | ✅ |
| O7 | A aprovação preenche a OS: responsável = vendedor do orçamento; `valor_entrada` = sinal; previsão = data da aprovação + "Prazo de entrega (dias)" (campo do orçamento, padrão nos Parâmetros); status inicial `ABERTA` | Nada de status especial | ✅ |
| O8 | "Desfazer aprovação": só enquanto a OS estiver `ABERTA` **e** sem pagamento registrado. Cancela a OS (fica no histórico) e devolve o orçamento a `ENVIADO` | Corrige aprovação por engano sem mexer em dinheiro já recebido | ✅ |

### 6.4. Fábrica — estoque, compras, terceirizados e produção

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| E0 | O orçamento de marcenaria vale **só para o tipo "Móveis planejados"**. "Reforma de móveis" continua como OS simples, com o campo "Etapa". Em Planejados, o campo "Etapa" sai (substituído por P1) | Reforma é conserto; não precisa de BOM | ✅ |
| E1 | **Reserva calculada**, sem tabela nova: `disponível = estoque − insumos de OS de marcenaria abertas ainda não separados` | Nenhuma tabela de estoque muda | ✅ |
| E1a | Desempenho medido em 06/10: SQLite com ~5 anos de dados (6.000 OS, 288.000 linhas de insumo) — **11 ms** sem índices, **3,6 ms** com índices. Regras: (1) índices nas FKs da árvore e em `separado`; (2) **uma** consulta agrupada por produto, nunca uma por produto em laço; (3) calcular só nas telas de separação, lista de compras e inclusão de insumo — **nunca** na lista geral de produtos nem no PDV | Pedido do usuário: verificar lentidão | ✅ |
| E2 | A baixa de estoque acontece na **separação**, via `registrar_movimentacao` com origem `ORDEM_SERVICO` e o número da OS | Mecanismo existente; sem código novo no estoque | ✅ |
| E3 | Na separação, "Qtd retirada" vem com o planejado **arredondado para cima** nas unidades inteiras (chapa, unidade, par, barra) e é editável. A baixa usa a quantidade **real**. O gestor vê orçado × real por móvel | Ninguém retira 0,4 chapa; baixar 1,4 deixaria estoque fantasma. A diferença mostra se a perda de 10% está certa | ✅ |
| E4 | Conferência por checkbox **e** por leitor de código de barras (campo opcional; leitores comuns funcionam como teclado; usa `produto.codigo_barras`) | A fábrica vai usar leitor | ✅ |
| E5 | Lista de compras: consulta dos itens "sem saldo", agrupada pelo **fornecedor principal** do produto, com impressão. **Não** gera pedido de compra | O módulo de compras não está nesta branch | ✅ |
| E6 | Móvel terceirizado: a central é um **Fornecedor**; o móvel guarda nº do pedido externo e status `ENVIADO → RECEBIDO → CONFERIDO`. Ao marcar "Recebido", o sistema **oferece** lançar a conta a pagar (não lança sozinho) | O valor da nota às vezes muda | ✅ |
| P1 | Modelos de etapas nos Parâmetros, por tipo de produção (interna: Corte → Borda → Furação → Montagem → Embalagem). Cada móvel recebe uma **cópia editável**. Etapa: Pendente / Em execução / Concluída, com responsável (funcionário) e data. **Nenhum preço** na tela | Atende oficina pequena e fábrica com CNC | ✅ |
| P2 | O status da OS **não muda sozinho**. Com todos os móveis concluídos, o sistema pergunta "Produção concluída: mover a OS para o próximo status?" | Decisão sempre do usuário | ✅ |
| P2a | **Rótulos de status por segmento** no registry (opção B). Marcenaria: `EM_ANDAMENTO` → "Em produção", `AGUARDANDO_PECAS` → "Aguardando material", `AGUARDANDO_RETIRADA` → "Aguardando instalação"; demais iguais. Os outros segmentos continuam com os textos de hoje | Móvel planejado é instalado, não retirado. ⚠️ Código compartilhado: exige prova de não regressão | ✅ |
| P3 | Na fábrica, **um computador fixo** com o app. Não há versão celular/tablet nesta fase | Realidade da fábrica piloto | ✅ |
| P4 | Permissão nova no cargo: "Ver custos e margens da marcenaria". As telas de Separação e Produção **nunca** mostram preço, com ou sem a permissão | Corrige o Figma, que mostra o preço de venda ao marceneiro | ✅ |

### 6.5. Obra — instalação e entrega

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| I1 | O montador **não usa o sistema na obra**. O sistema imprime o **Termo de Entrega A4 por ambiente** (checklist para marcar à caneta, espaço para pendências, assinaturas). De volta à fábrica, alguém registra "Conforme" ou "Com ressalvas" (+ pendências) e anexa a foto do termo assinado e as fotos da montagem (mecanismo de fotos da OS) | Consequência de P3 | 🟡 |
| I2 | Checklist de vistoria padrão nos Parâmetros, copiado para cada ambiente e editável ali | Mesmo padrão de P1 | 🟡 |
| I3 | Pendência aberta **avisa** ao finalizar a OS, mas **não trava** | Caso real: cliente pagou e aceitou com ressalva | 🟡 |
| I4 | Montador é sempre **funcionário** nesta fase. Sem conta a pagar por instalação | Resposta do usuário ("é sempre montador por agora") | ✅ |
| I5 | Agenda = campos na OS (data/hora da instalação + montadores). A Lista de OS filtra e ordena por essa data. Tela de agenda semanal fica para a fase 2 | Com um computador, a lista ordenada resolve "quem instala onde amanhã" | ✅ |
| I6 | Termo **por ambiente** (dá para entregar a cozinha antes do closet), mas a OS **finaliza uma vez**, com tudo entregue. Cobrança parcial por ambiente fica fora | Simplicidade financeira na fase 1 | 🟡 |
| I7 | Etiqueta **por móvel** (código PRJ, nº da OS, cliente, ambiente, móvel, dimensões) para os volumes embalados. Etiqueta por peça só com importação 3D | Sem plano de corte, não há peças individuais | ✅ |

### 6.6. Telas

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| T1 | A OS continua sendo o **modal atual**. Abas novas, ligadas por capacidades que só a marcenaria declara: **Orçamento** (resumo somente leitura + link), **Separação**, **Produção**, **Entrega** | Mesmo mecanismo da Vistoria da oficina; os outros segmentos não enxergam nada | ✅ |
| T2 | Item de menu **"Orçamentos"**, só na marcenaria. Lista com filtros por status, cliente e "vence em até X dias" | — | ✅ |
| T3 | Editor de orçamento em **página inteira** | Grande demais para modal | ✅ |
| T3a | Painel de custos **recolhível**, só com a permissão P4, e botão **"Visão do cliente"** que esconde tudo o que é interno | O vendedor vira a tela para o cliente | ✅ |
| T3b | O bloco de **importação 3D sai** da tela | É fase 2; mostrar função que não funciona confunde | ✅ |
| T3c | Editar um orçamento `ENVIADO` mostra o aviso "o cliente recebeu R$ X; editar volta para Rascunho" | O valor já está com o cliente | ✅ |
| T3d | **Salvamento automático** do rascunho | Orçamento de 3 ambientes leva ~1 hora; fechar o app não pode perder o trabalho | ✅ |
| T4 | Modal "Adicionar Móvel": busca de insumo no cadastro de produtos, **cadastro rápido** de produto, botão **"Duplicar móvel"**, mão de obra fixa ou por horas. O campo **"Categoria" do móvel sai** nesta fase | Categoria não era usada em cálculo nem filtro | ✅ |
| T5 | **Proposta comercial em PDF** obrigatória na fase 1. Mostra ambientes, móveis com descrição e medidas, **total por ambiente** (sem preço por móvel), condições (sinal, prazo, validade). **Nunca** mostra custos | Sem proposta não há como "Enviar". Total por ambiente é o padrão de mercado | ✅ |
| T6 | Seção **"Marcenaria"** em Configurações: markup, perda, validade, prazo de entrega, custo/hora, RT padrão e modo do RT, modelos de etapas, checklist de vistoria | Padrões editáveis pelo dono | ✅ |
| T7 | **Histórico** só de inclusão (nada é apagado): mudanças de status do orçamento, etapas, separação e termos, com quem fez e quando. A Spec 06A verifica se algum histórico existente da OS pode ser reaproveitado | Auditoria barata desde o primeiro projeto | ✅ |
| T8 | **Lista de OS** atual, com coluna e filtro novos de data de instalação (I5) | Sem tela nova | ✅ |

---

## 7. Fora da fase 1

| Item | Quando | Observação |
|------|--------|------------|
| Importação de projeto 3D (Promob, CorteCloud, Dinabox, UpMob) | Fase 2 | Depende de arquivos reais da fábrica |
| Aditivos após aprovação | Fase 2 | Hoje: nova versão antes de aprovar, ou cancelar e refazer |
| Kanban de produção com cronômetro | Fase 2 | Usa o histórico de etapas (T7) |
| Agenda semanal de instalação | Fase 2 | Hoje: campos na OS + filtro (I5) |
| Vários comissionados na mesma tela | Fase 2 | O modelo de dados já aceita N |
| Versão celular/tablet | Futuro | P3 |
| Etiqueta por peça / plano de corte | Futuro | Depende da importação 3D |
| Contrato em PDF, assinatura digital, WhatsApp | Futuro | — |
| Cobrança parcial por ambiente | Futuro | I6 |
| Pedido de compra gerado pela lista de compras | Futuro | Módulo de compras fora desta branch |

---

## 8. Lista de specs

⚠️ = toca código compartilhado com outros segmentos (prova de não regressão obrigatória).

| Spec | Camada | Título | Depende de | Decisões |
|------|--------|--------|------------|----------|
| 00 | Documento | Registro de decisões | — | Todas |
| 01A ⚠️ | Backend | Rótulos de status por segmento (registry) | 00 | P2a |
| 01B ⚠️ | Frontend | Rótulos de status por segmento (telas e impressão) | 01A | P2a |
| 02 ⚠️ | Frontend | Consulta de CNPJ no cadastro de cliente | 00 | O6 |
| 03A | Backend | Ajuste do segmento marcenaria (capacidades, tipos) | 01A | O4, E0, T1 |
| 03B | Frontend | Ajuste do segmento marcenaria (fallbacks, textos) | 03A | O4, E0 |
| 04A ⚠️ | Backend | Base: `sofre_perda`, Parâmetros, permissão "ver custos" | 03A | F6, T6, P4 |
| 04B ⚠️ | Frontend | Base: campo no produto, seção Marcenaria em Configurações, permissão no cargo | 04A | F6, T6, P4 |
| 05 | Backend | Motor de cálculo (funções puras + testes) | 04A | C1–C8 |
| 06A | Backend | Orçamento: modelo de dados, API, versões, validade, autosave, histórico | 05 | F1, O1–O3, T7 |
| 06B | Frontend | Orçamento: lista, menu, editor, modal Adicionar Móvel | 06A | T2–T4 |
| 07 | Frontend | Proposta comercial em PDF | 06B | T5 |
| 08A | Backend | Aprovação → OS (parcial, itens travados, desfazer) | 06A | F2–F4, O4, O5, O7, O8 |
| 08B ⚠️ | Frontend | Aprovação → OS (modal de aprovação, aba Orçamento, itens travados) | 08A, 06B | F4, T1 |
| 09A | Backend | RT do arquiteto (conta a pagar na finalização) | 08A | C5a–C5d |
| 09B | Frontend | RT do arquiteto (campo no orçamento) | 09A, 06B | C5a, C5c |
| 10A | Backend | Separação, reserva calculada, baixa, lista de compras | 08A | E1–E5 |
| 10B | Frontend | Aba Separação (leitor), tela Lista de compras | 10A | E3–E5 |
| 11A | Backend | Terceirizados (status do pedido, oferta de conta a pagar) | 08A | E6 |
| 11B | Frontend | Terceirizados (na aba Separação/Produção) | 11A, 10B | E6 |
| 12A | Backend | Produção: etapas por móvel | 08A | P1, P2 |
| 12B | Frontend | Aba Produção e aviso de mudança de status | 12A | P1, P2 |
| 13A | Backend | Entrega: termos, pendências, fotos, data de instalação | 08A | I1–I6, T8 |
| 13B ⚠️ | Frontend | Aba Entrega, Termo A4, filtro de instalação na Lista de OS | 13A | I1–I6, T8 |
| 14 | Frontend | Etiquetas por móvel | 08A | I7 |

**Ordem de implementação:** 00 → 01A/01B → 02 → 03A/03B → 04A/04B → 05 → 06A/06B → 07 → 08A/08B → 09 → 10 → 11 → 12 → 13 → 14. A Spec 02 não depende de nada além desta e pode andar em paralelo.

**Pronto da fase 1:** a fábrica piloto leva **um projeto real** do orçamento à assinatura do termo pelo sistema, sem planilha, e os três segmentos em produção seguem idênticos.

---

## 9. Riscos

| Risco | Mitigação |
|-------|-----------|
| Mexer em código compartilhado (status, cadastro de cliente, produto, cargo, modal de OS) | Specs ⚠️ com prova antes × depois; capacidades por segmento em vez de `if marcenaria` |
| Dois motores de cálculo divergindo | C8: um só motor, no backend |
| Estoque fantasma por chapa fracionada | E3: baixa pela quantidade real |
| Preço de insumo mudando em orçamento já enviado | O3: aviso, nunca atualização silenciosa |
| Teto de bytecode do PyArmor com módulos grandes | Medir antes de cada instalador (PR7) |
| Uso real achar o que teste não acha | Cada spec B termina com roteiro de teste no app em dev |

---

## 10. Critérios de aceite (deste documento)

- [ ] O usuário revisou e aprovou todas as decisões, inclusive as marcadas 🟡.
- [ ] `docs/segmento-marcenaria-plano.md` recebeu um aviso no topo apontando para este documento.
- [ ] A lista de specs (§8) foi aprovada com a numeração final.
- [ ] Nenhuma decisão aqui contradiz os princípios da §4.

## 11. Como usar este documento

- Cada spec cita as decisões pelo código na linha "Referência" do cabeçalho.
- Decisão nova ou alterada durante as specs **volta para cá** como revisão (bloco "> Revisão N" no topo), nunca só na spec que a mudou.
- Uma decisão 🟡 que o usuário contestar vira ✅ com o texto corrigido, e as specs que a usam recebem revisão.
