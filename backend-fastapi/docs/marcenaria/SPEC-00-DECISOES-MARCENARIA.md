# Spec 00 — Registro de Decisões do Segmento Marcenaria

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                       |
| Camada       | Documento                                                             |
| Dependências | Nenhuma                                                               |
| Bloqueia     | Todas as specs da marcenaria (01 a 14)                                |
| Referência   | Conversa de 05–06/10/2026; Figma (7 telas); PDF "Módulo Marcenaria: Plano de Implementação"; `docs/segmento-marcenaria-plano.md` (16/09) |
| Branch       | `feat/segmento-marcenaria` @ `f040e8d` (Revisões 1–14) · @ `53e5d81` (Revisão 15) |

> **Revisão 15 (08/10/2026) — Convergência com o código da branch, aprovada pelo usuário.** As Revisões 1–14 foram escritas sobre `f040e8d`. Em 08/10, às 18:30, a branch recebeu os merges de `feat/compras`, `etiquetas`, `embalagens`, `feat/venda-fracionada` e `feat/fiscal-ativacao`, que trouxeram o **módulo de Compras**, o **motor de etiquetas** e uma primeira implementação da marcenaria chamada **"fábrica"** (`docs/marcenaria-fabrica-plano.md`, fases F1–F5). Regras do usuário para esta revisão: (1) seguir as specs com o menor risco para os módulos em produção; (2) **Compras e etiquetas já implementados prevalecem** sobre o que as specs tinham planejado para esses assuntos; (3) a fábrica é **aposentada** (nenhuma loja usa a marcenaria, confirmado em 08/10). Decisões novas: **FB1** (fábrica aposentada), **FB2** (Compras e etiquetas prevalecem), **F2b** (insumos entram na OS como peças embutidas), **E3b** (separação sobre os itens da OS), **E1b**, **E5a**, **E6b**, **I5b**, **R15-CNPJ**, **R15-MIG**. Revisam F2, E1, E2a, E3a, E5, E6a e T8a. Detalhes na §6.7.
>
> **Revisão 14 (08/10/2026) — Spec 13A (entrega), aprovada pelo usuário:** **T8a** (a agenda de instalações vira uma **aba própria** em Serviços, e não coluna e filtro na Lista de OS compartilhada) e **I5a** (vários agendamentos por OS, cada um com ambientes e montadores; aviso, sem trava, de montador em duas obras no mesmo dia). Também: checklist das marcações do papel é opcional; registro sem foto do termo avisa; pendências podem ser criadas e resolvidas depois da finalização.
>
> **Revisão 13 (08/10/2026) — Spec 12A (produção), aprovada pelo usuário:** **P1a** (etapas por móvel, não por unidade; ordem não imposta; ações em lote e "concluir em todos"; concluir sem ter iniciado) e **P2b** (além do "Aguardando Entrega" no fim, o sistema sugere "Em Produção" quando a primeira etapa é marcada numa OS aberta; sempre pergunta, nunca muda sozinho).
>
> **Revisão 12 (08/10/2026) — Spec 11A (terceirizados), aprovada pelo usuário:** **E6a** (situação começa em "A pedir"; problema no recebimento; conta da central **por pedido**, com valor editável, parcelável, na categoria de despesa "Produção terceirizada"; lançar a conta exige o módulo Financeiro).
>
> **Revisão 11 (08/10/2026) — Spec 10A (separação), aprovada pelo usuário:** **E3a** (a separação e o orçado × real passam a ser **por produto da OS**, e não por móvel: a chapa é cortada para vários móveis de uma vez, e arredondar cada móvel para cima pediria chapa a mais) e **E2a** (retirada sem saldo é permitida, com aviso de estoque negativo; devolução de sobra; cancelar a OS não devolve material sozinho).
>
> **Revisão 10 (06/10/2026) — Spec 09A (RT e resultado do mês), aprovada pelo usuário:** **F2a** (o custo dos itens que vieram do orçamento serve à comissão, mas **não** entra no CMV: cada custo entra no resultado uma vez, pelo registro real — baixa de estoque, conta paga, salários); **C5e** (conta de RT por arquiteto, sobre o total aprovado, categoria própria, vencimento padrão de 30 dias configurável; reabrir/cancelar a OS cancela as pendentes e nunca mexe nas pagas).
>
> **Revisão 9 (06/10/2026) — Spec 08A (aprovação → OS), aprovada pelo usuário:** **O7a** (o sinal só entra na OS se já foi recebido; senão fica combinado no orçamento), **O4a** (aprovar direto do rascunho ou de um vencido; desconto pode ser renegociado na aprovação), **F4a** (exceção a F1: coluna genérica `origem` nos itens da OS, para a trava de F4), **O8a** (desfazer usa o cancelamento de OS de sempre, com PIN do gerente e sinal virando crédito ou devolvido). Achado registrado como **PEND-002** (comissão da OS ignora o desconto, todos os segmentos).
>
> **Revisão 8 (06/10/2026) — Spec 07 (proposta), aprovada pelo usuário:** **T5a** (o PDF sai pelo "Salvar como PDF" do diálogo de impressão, como as vias de OS e venda; o sistema não guarda o arquivo, e o evento de envio guarda os valores). A Spec 06A recebeu a Revisão 2.
>
> **Revisão 7 (06/10/2026) — Spec 06B (telas do orçamento), decisões novas, aprovadas pelo usuário:** **T3e** (criação preguiçosa), **T3f** (visão do cliente = proposta), **T4a** (cadastro rápido com preço de venda = custo quando vazio), **T4b** (prévia do preço do móvel pela API), **T3g** (aviso de margem negativa também para quem não vê custos), **O1a** (anexos fora do rascunho). A Spec 06A recebeu a Revisão 1 para atendê-las.
>
> **Revisão 6 (06/10/2026) — C9 e detalhe de C5d (Spec 05):** desconto global no orçamento (decisão do usuário); repartição do RT por linha pelo maior resto.
>
> **Revisão 5 (06/10/2026) — O3a:** custo do insumo = último preço de compra, com reserva no custo médio e aviso quando não houver nenhum (decisão do usuário).
>
> **Revisão 4 (06/10/2026) — Reforma de móveis fora da fase 1 (decisão do usuário):** a marcenaria passa a ter **um tipo só**, "Móveis planejados", e toda OS nasce da aprovação de um orçamento. A Reforma sai do registry e fica registrada como referência na §7.1, para voltar numa fase seguinte. Consequências: **O4** volta à forma original (`aprovacao_itens` sai da marcenaria); **E0/E0a** reescritas; nova **E0c** (botão de criar OS num segmento sem tipo criável à mão). A Revisão 3 abaixo fica como histórico.
>
> **Revisão 3 (06/10/2026) — Spec 03A:** novas decisões **E0a** (OS de Planejados só nasce da aprovação de um orçamento; o backend recusa a criação manual) e **E0b** (Planejados fica só com nome do projeto e endereço da obra). **O4 revisada:** `aprovacao_itens` **continua** na marcenaria, porque a capacidade é do segmento e a Reforma precisa dela; a aprovação **dos móveis** continua só no orçamento (decidido pelo usuário).
>
> **Revisão 2 (06/10/2026) — exceção ao PR1:** a Spec 01B corrige o rótulo de **desfecho** na lista e no filtro de OS, que mostravam "Sem Reparo"/"Condenado" mesmo em segmentos que declaram `rotulos_situacao`. A correção muda a lista da **serigrafia** (passa a mostrar "Não produzido"/"Perda na produção", os mesmos textos da finalização e da impressão). Aprovada pelo usuário; é a única exceção ao PR1 até aqui.
>
> **Revisão 1 (06/10/2026) — P2a:** `AGUARDANDO_RETIRADA` na marcenaria passa a se chamar **"Aguardando entrega"** (curto: "Aguard. entrega"), e não "Aguardando instalação". O rótulo vale para o segmento inteiro, e no tipo "Reforma de móveis" o cliente retira o móvel. Decidido ao escrever a Spec 01A (§8). O valor gravado continua o mesmo enum.

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
| Segmento `marcenaria` ligado no registry, com os tipos "Móveis planejados" e "Reforma de móveis" | `app/core/segmentos/definicoes/marcenaria.py` | Base; ajustado na Spec 03A (a Reforma sai da fase 1; Revisão 4) |
| Identificador gerado `PRJ-AAAA-NNNNNN` | registry (`identificador`) | Código do projeto nas etiquetas |
| Objeto de serviço "Projeto" (nome + endereço da obra) | registry + `objeto_servico` | É o "Projeto" do orçamento (O5) |
| Abas da OS ligadas por capacidade (ex.: Vistoria da oficina) | `OSFormTabsContent.vue` + `capacidades.py` | Mecanismo das abas novas (T1) |
| Livro-razão único do estoque | `services/movimentacao_estoque.registrar_movimentacao` | Baixa da separação (E2) |
| Comissão por funcionário sobre o **lucro** dos itens de serviço | `db/crud/relatorio.get_comissao_base` | Comissão do vendedor sem código novo (C5) |
| Contas a pagar | `db/models/conta_pagar.py` | RT do arquiteto, terceirizados (C5, E6) |
| Permissões por cargo (JSON) | `db/models/cargo.py` | "Ver custos" (P4) |
| `produto.localizacao_estoque`, `produto.fornecedor_id`, `produto.codigo_barras` | `db/models/produto.py` | Endereço no almoxarifado, lista de compras, leitor |
| Consulta de CNPJ (BrasilAPI, só frontend) | `shared/services/cnpj.service.ts` (o arquivo da empresa só reexporta; Revisão 15) | Já usada no cadastro de cliente PJ desde `011dff7` (06/10); a Spec 02 completa o que falta |

**O que chegou com os merges de 08/10** (Revisão 15) e passa a ser a base:

| Peça | Onde | Uso nesta fase |
|------|------|----------------|
| Módulo **fábrica** (orçamento dentro da OS, trilho de 10 fases, separação bipada, central de corte) | `app/services/fabrica/`, `modules/order-service/fabrica/`, chave `configuracoes_os.modo_fabrica` | **Aposentado** (FB1). Tabelas e colunas ficam no banco; o código fica inerte e sai numa limpeza depois do piloto |
| `produtos.sofre_perda` (+ `unidade_consumo`, `consumo_por_unidade`) | migração `f1c7a2d9e3b4` (fábrica F1) | `sofre_perda` é a coluna de F6: a Spec 04A **não** cria coluna. As outras duas ficam sem uso |
| `ordem_servico_itens.quantidade_separada` e `custo_real` | migração `c6f2d8a4b915` (fábrica F4) | Base da separação (E3b): a finalização já baixa só `quantidade − quantidade_separada` e o Compras já reserva essa diferença |
| **Peça embutida**: item `PRODUTO` com `valor_unitario = 0` e `visivel_cliente = false` | `schemas/ordem_servico.py` (`OSItemBase`), migração `c8d9e0f1a2b3` | Forma dos insumos na OS (F2b): o cliente não vê nem paga, o estoque baixa |
| Trava "item veio do orçamento" na OS | `services/ordem_servico.py` (`_assert_item_nao_gerado_pela_fabrica`), `OSServicesTab.vue` (`veioDoOrcamento`) | A Spec 08A estende a mesma trava à coluna genérica `origem` |
| **Módulo Compras**: reserva calculada das OS abertas, Necessidades, pedidos `MATERIAL`/`SERVICO`, recebimento que lança contas a pagar, painel "Compras desta OS" | `app/services/compras/` (`demanda_os.py`, `necessidades.py`, `pedidos.py`, `recebimentos.py`) | Prevalece (FB2): reserva, lista de compras e central parceira (E1b, E5a, E6b) |
| `ordens_servico.data_instalacao` | migração `b4e9c1a7d2f3` (fábrica F3) | Só o Compras lê (fila "quem instala primeiro"); a Spec 13A passa a preenchê-la (I5b) |
| **Motor de etiquetas** (modelo neutro em mm, folhas Pimaco/Avery, "pular posições", calibração, térmica nativa, etiqueta de volume) | `frontend/src/shared/etiquetas/` | Prevalece (FB2): a Spec 14 só acrescenta os campos do móvel e um modelo pronto |
| Unidades fracionáveis (`KG, G, L, ML, M, CM, M2, M3`) | `app/services/quantidade_venda.py` (`UNIDADES_FRACIONAVEIS`) e `shared/utils/quantidade.ts` | Regra única do "arredonda para cima nas unidades inteiras" (E3b). Nenhuma lista nova |
| Linhas da matriz de cargos por `segmento` ou `modulo` (ficam fora do nível de acesso dos outros) | `employees/constants/positions.constants.ts`, `PositionModal.vue` | As linhas novas da marcenaria usam `segmento: 'marcenaria'` (04B, 06B); nenhuma mudança no cálculo do nível |

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
| F2 | Na aprovação, **cada móvel vira um item de serviço da OS**: `nome` = nome do móvel, `valor_unitario` = preço de venda, `custo_unitario` = custo direto (+ parte do RT, C5d). Os insumos **não** viram itens da OS **Revista por F2b (Revisão 15):** os insumos passam a entrar na OS como peças embutidas. | Se os insumos virassem itens, entrariam no total e o cliente pagaria duas vezes | ✅ |
| F2a | **Revisão 10:** o `custo_unitario` dos itens da OS que vieram do orçamento continua servindo à **comissão** (C5d), mas o **CMV ignora** itens com `origem`. Material entra pela baixa de estoque da OS (10A), RT pela conta paga (09A), mão de obra pelos salários e terceirizado pela conta da central (11A, categoria de despesa) | Sem isso o resultado do mês contaria RT, mão de obra e material duas vezes | ✅ |
| F3 | O "congelamento" é o **orçamento aprovado ficar somente leitura**. Os preços já estão gravados nos itens da OS. Mudança = nova versão (O2) | Evita duplicar 4 tabelas em `os_*` como o PDF propunha | ✅ |
| F4 | Itens da OS que vieram do orçamento ficam **travados** na OS, com o aviso "altere pelo orçamento". Itens adicionados à mão na OS continuam editáveis | Se o preço do móvel mudasse só na OS, OS e orçamento passariam a discordar e o dono perderia a confiança nos números | ✅ |
| F4a | **Exceção a F1 (Revisão 9):** a tabela `ordem_servico_itens` ganha a coluna genérica e nula `origem`. Item com origem não é editado nem removido pela OS. Todos os itens que existem hoje ficam com origem nula (comportamento igual) | A trava de F4 precisa saber de onde o item veio; uma coluna genérica evita a palavra "marcenaria" no serviço da OS e serve a qualquer segmento futuro | ✅ |
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
| C5d+ | **Detalhe (Revisão 6):** o RT total é repartido entre as linhas pelo **maior resto** (soma exata). No item da OS, a parte por unidade é arredondada **para baixo**; a sobra (menos de `qtd` centavos por linha) não entra no custo, e a base da comissão fica no máximo alguns centavos maior | O item da OS tem um só custo unitário; o erro fica do lado que o sistema já escolheu (a favor do funcionário) | ✅ |
| C5e | **Revisão 10:** na finalização da OS, **uma conta a pagar por arquiteto**, sobre o RT do total **aprovado** (maior resto entre arquitetos), categoria "Comissão de arquitetos (RT)", vencimento = finalização + prazo configurável (padrão 30 dias). Reabrir ou cancelar a OS cancela as contas **pendentes**; as **pagas** ficam (cancelamento registra aviso). Criada com ou sem o módulo Financeiro | Completa C5b com as regras de valor, data, categoria e ciclo de vida | ✅ |
| C6 | Arredondamento **uma única vez**, no preço de cada móvel (meio centavo para cima). Ambiente e total são somas. Sinal = `arred(total × sinal%)`; saldo = total − sinal | Elimina o erro de 1 centavo do Figma (9.695,81 × 9.695,82) | ✅ |
| C7 | Sinal **livre**, decidido pelo usuário em cada orçamento; pode ser **zero**. O campo aceita **% ou R$** (digitar em um preenche o outro). Não há trava "aguardando sinal" | Pedido do usuário. A OS já registra o adiantamento (`valor_entrada`) | ✅ |
| C8 | **Um só motor de cálculo, no backend** (funções puras). A tela mostra os valores devolvidos pela API; não recalcula em TypeScript | Dois motores (Python e TS) acabariam discordando em centavos. Com o banco local, a resposta é imediata | 🟡 (decisão técnica) |
| C9 | **Desconto global** no orçamento, em % ou R$, sobre o total bruto. Aparece na proposta, vai para o `desconto` da OS e sai da margem. O **RT é calculado sobre o total com desconto** (Revisão 6) | O vendedor usa desconto para fechar; sem ele, mexeria no markup e a proposta não mostraria o desconto | ✅ |

### 6.3. Ciclo de vida do orçamento

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| O1 | Status do orçamento: `RASCUNHO → ENVIADO → APROVADO`, finais `RECUSADO`, `VENCIDO` e `SUBSTITUIDO`. Os status da OS não mudam. A "Medição" do PDF **não** é status: vira anexos do orçamento (fotos e medidas) | Separar o ciclo comercial do ciclo de produção | ✅ |
| O1a | Anexos (fotos e PDF da medição) podem entrar e sair em qualquer status, menos `SUBSTITUIDO` e `APROVADO`, sem contar como edição do orçamento (Revisão 7) | A foto do ambiente muitas vezes chega depois do envio e não muda o preço | ✅ |
| O2 | "Nova versão" copia o orçamento inteiro; a anterior vira `SUBSTITUIDO` (somente leitura). Número `ORC-AAAA-NNNNNN` + rótulo "v2". Só uma versão pode ser aprovada | Histórico do que foi oferecido ao cliente | ✅ |
| O3 | Validade padrão nos Parâmetros (15 dias), editável por orçamento. O custo do insumo é **copiado** quando entra no móvel. Ao renovar ou criar versão, o sistema avisa "N insumos mudaram de preço — atualizar?", com a diferença no total. **Nunca** muda preço sem avisar | Vendedor que já passou o valor ao cliente não pode ser surpreendido | ✅ |
| O3a | O custo do insumo copiado para o orçamento é o **último preço de compra** (`estoque.valor_entrada`). Sem ele, usa o **custo médio** (`estoque.custo_medio`); sem os dois, entra **R$ 0,00** e o orçamento mostra o aviso "insumo sem custo cadastrado" (Revisão 5) | É o que o dono vai pagar na próxima chapa. O aviso impede um móvel barato demais por falta de cadastro | ✅ |
| O4 | A aprovação acontece **só no orçamento**, escolhendo quais móveis o cliente aceitou. Os recusados ficam como histórico. A OS nasce só com os aprovados; o sinal é recalculado sobre o total aprovado. `CAP_APROVACAO_ITENS` **sai** da marcenaria (Revisão 4: a Revisão 3 a mantinha só por causa da Reforma, que saiu da fase 1) | Aprovar em dois lugares faria os documentos discordarem | ✅ |
| O4a | Aprovar também direto do **rascunho** (o envio é registrado junto) ou de um **vencido** (com confirmação). O **desconto pode ser renegociado** na aprovação e é gravado no orçamento (Revisão 9) | O cliente que fecha na loja não precisa de um "enviar" antes; o que volta dias depois da validade não pode travar a venda; aprovar só parte do projeto costuma mudar o desconto | ✅ |
| O5 | O "Projeto" do Figma é o **objeto de serviço "Projeto"** que já existe (nome + endereço da obra) | A OS exige objeto; o cliente que volta encontra o projeto | ✅ |
| O6 | Cliente: busca ou cadastro pelo **modal de cliente que já existe**. A consulta de CNPJ entra no cadastro de cliente em **spec separada** (Spec 02), logo no início | Melhoria útil a todos os segmentos | ✅ |
| O7 | A aprovação preenche a OS: responsável = vendedor do orçamento; `valor_entrada` = sinal; previsão = data da aprovação + "Prazo de entrega (dias)" (campo do orçamento, padrão nos Parâmetros); status inicial `ABERTA` | Nada de status especial | ✅ |
| O7a | **Revisão de O7 (Revisão 9):** na aprovação, o usuário diz se o sinal **já foi recebido**. Sim: entra como adiantamento da OS (valor editável, forma de pagamento obrigatória ou crédito do cliente). Não: `valor_entrada` fica 0 e o sinal combinado fica guardado no orçamento, para ser lançado depois na OS | `valor_entrada` é dinheiro recebido e é descontado na finalização. Gravar o sinal combinado como pago faria o cliente pagar menos na entrega se o PIX nunca chegasse | ✅ |
| O8 | "Desfazer aprovação": só enquanto a OS estiver `ABERTA` **e** sem pagamento registrado. Cancela a OS (fica no histórico) e devolve o orçamento a `ENVIADO` | Corrige aprovação por engano sem mexer em dinheiro já recebido | ✅ |
| O8a | O "desfazer aprovação" cancela a OS pelo cancelamento de sempre: PIN do gerente quando a loja exige, e o sinal recebido vira **crédito do cliente** (padrão) ou é marcado **devolvido**. Lista todos os motivos quando não pode desfazer (Revisão 9) | Reaproveita as regras de dinheiro do cancelamento; o crédito é usado na reaprovação | ✅ |

### 6.4. Fábrica — estoque, compras, terceirizados e produção

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| E0 | A marcenaria tem **um tipo de trabalho só: "Móveis planejados"**, que usa o orçamento técnico. "Reforma de móveis" fica **fora da fase 1** (§7.1) (Revisão 4) | Foco no fluxo da fábrica piloto; a Reforma volta depois como segundo tipo, sem orçamento técnico | ✅ |
| E0a | Toda OS da marcenaria **nasce da aprovação de um orçamento**. O tipo declara `criacao_manual=False` no registry; o backend recusa a criação manual e a troca de tipo | As abas de Separação, Produção e Entrega dependem dos móveis do orçamento | ✅ |
| E0b | Planejados fica só com **nome do projeto** e **endereço da obra**. Saem ambiente, módulos, material, acabamento, ferragens, montagem incluída e etapa (Revisão 3) | Repetiriam o orçamento (que tem vários ambientes) e chegariam vazios ou divergentes | ✅ |
| E0c | Regra genérica: num segmento **sem nenhum tipo criável à mão**, os botões "Criar OS" (atalho do menu principal e tela de OS) **somem**; a partir da Spec 06B viram **"Novo orçamento"** (Revisão 4) | Um botão que abre um formulário sem tipo possível seria um beco sem saída | ✅ |
| E1 | **Reserva calculada**, sem tabela nova: `disponível = estoque − insumos de OS de marcenaria abertas ainda não separados` **Revista por E1b (Revisão 15):** a reserva vem do Compras (`demanda_os`). | Nenhuma tabela de estoque muda | ✅ |
| E1a | Desempenho medido em 06/10: SQLite com ~5 anos de dados (6.000 OS, 288.000 linhas de insumo) — **11 ms** sem índices, **3,6 ms** com índices. Regras: (1) índices nas FKs da árvore e em `separado`; (2) **uma** consulta agrupada por produto, nunca uma por produto em laço; (3) calcular só nas telas de separação, lista de compras e inclusão de insumo — **nunca** na lista geral de produtos nem no PDV **Revista por E1b (Revisão 15):** as regras de desempenho passam a ser do Compras. | Pedido do usuário: verificar lentidão | ✅ |
| E2 | A baixa de estoque acontece na **separação**, via `registrar_movimentacao` com origem `ORDEM_SERVICO` e o número da OS | Mecanismo existente; sem código novo no estoque | ✅ |
| E2a | Retirada sem saldo **acontece** (estoque negativo, com aviso para conferir a contagem), como na OS de hoje. Sobra pode ser **devolvida** ao estoque. Cancelar a OS **não** devolve material sozinho (chapa cortada não volta); o sistema avisa o que ficou fora. Desfazer aprovação exige devolver antes (Revisão 11) **Ajustada por E3b (Revisão 15):** a mecânica passa a ser a dos itens da OS; o "cancelar não devolve" continua. | Travar a retirada pararia a fábrica por um cadastro desatualizado | ✅ |
| E3 | Na separação, "Qtd retirada" vem com o planejado **arredondado para cima** nas unidades inteiras (chapa, unidade, par, barra) e é editável. A baixa usa a quantidade **real**. O gestor vê orçado × real por móvel **Revista por E3a e E3b.** | Ninguém retira 0,4 chapa; baixar 1,4 deixaria estoque fantasma. A diferença mostra se a perda de 10% está certa | ✅ |
| E3a | **Revisão de E3 (Revisão 11):** a separação é por **OS e produto** (todos os móveis que usam o mesmo produto viram uma linha), e o sugerido é arredondado para cima **uma vez**, no total do produto. O orçado × real fica por produto, não por móvel; cada linha mostra os móveis que usam o produto **Revista por E3b (Revisão 15):** o produto da OS é um item de peça embutida. | 1,4 + 1,2 + 0,6 chapa arredondados por móvel dariam 5 chapas; arredondados juntos, 4 | ✅ |
| E4 | Conferência por checkbox **e** por leitor de código de barras (campo opcional; leitores comuns funcionam como teclado; usa `produto.codigo_barras`) | A fábrica vai usar leitor | ✅ |
| E5 | Lista de compras: consulta dos itens "sem saldo", agrupada pelo **fornecedor principal** do produto, com impressão. **Não** gera pedido de compra **Revista por E5a (Revisão 15):** a lista é a tela Necessidades do Compras. | O módulo de compras não está nesta branch | ✅ |
| E6 | Móvel terceirizado: a central é um **Fornecedor**; o móvel guarda nº do pedido externo e status `ENVIADO → RECEBIDO → CONFERIDO`. Ao marcar "Recebido", o sistema **oferece** lançar a conta a pagar (não lança sozinho) **Revista por E6b (Revisão 15).** | O valor da nota às vezes muda | ✅ |
| E6a | **Revisão 12:** situação **A pedir → Pedido enviado → Recebido → Conferido**, com "registrar problema" (fica Recebido, com o texto) e "voltar um passo". Vários móveis da mesma central num pedido. No recebimento, o sistema **oferece** uma conta por pedido (valor sugerido = orçado, só para quem vê custos; editável; parcelável), categoria "Produção terceirizada" (`DESPESA`). Lançar exige o módulo Financeiro e a permissão de gerir o financeiro. Lista geral de atrasados **Revista por E6b (Revisão 15):** com o Compras, pedido `SERVICO` e contas do recebimento. | Completa E6 com o passo inicial, o caso do móvel com defeito e as regras de dinheiro | ✅ |
| P1 | Modelos de etapas nos Parâmetros, por tipo de produção (interna: Corte → Borda → Furação → Montagem → Embalagem). Cada móvel recebe uma **cópia editável**. Etapa: Pendente / Em execução / Concluída, com responsável (funcionário) e data. **Nenhum preço** na tela | Atende oficina pequena e fábrica com CNC | ✅ |
| P1a | **Revisão 13:** um conjunto de etapas por **móvel** (3 aéreos iguais = uma lista), criado na aprovação. A ordem **não** é imposta (a tela indica a próxima). Etapa pode ser concluída sem ter sido iniciada. Ações em **lote** e "concluir a etapa X em todos os móveis". Concluir de novo não muda nada | O corte de uma obra inteira acontece de uma vez; marcar móvel por móvel faria a fábrica abandonar o sistema | ✅ |
| P2 | O status da OS **não muda sozinho**. Com todos os móveis concluídos, o sistema pergunta "Produção concluída: mover a OS para o próximo status?" | Decisão sempre do usuário | ✅ |
| P2b | **Revisão 13:** o sistema também **pergunta** "mover a OS para Em Produção?" quando a primeira etapa é marcada numa OS Aberta. No fim, "Aguardando Entrega" quando todos os móveis estão prontos (internos com todas as etapas, terceirizados conferidos). A pergunta aparece uma vez por mudança | Mesmo princípio do P2 no começo da produção; o status da OS acompanha a fábrica sem ninguém lembrar | ✅ |
| P2a | **Rótulos de status por segmento** no registry (opção B). Marcenaria: `EM_ANDAMENTO` → "Em Produção", `AGUARDANDO_PECAS` → "Aguardando Material", `AGUARDANDO_RETIRADA` → "Aguardando Entrega" (Revisão 1; curtos e maiúsculas na Spec 01A); demais iguais. Os outros segmentos continuam com os textos de hoje | "Retirada" não descreve o móvel planejado, que é instalado; "entrega" serve também à reforma. ⚠️ Código compartilhado: exige prova de não regressão | ✅ |
| P3 | Na fábrica, **um computador fixo** com o app. Não há versão celular/tablet nesta fase | Realidade da fábrica piloto | ✅ |
| P4 | Permissão nova no cargo: "Ver custos e margens da marcenaria". As telas de Separação e Produção **nunca** mostram preço, com ou sem a permissão | Corrige o Figma, que mostra o preço de venda ao marceneiro | ✅ |

### 6.5. Obra — instalação e entrega

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| I1 | O montador **não usa o sistema na obra**. O sistema imprime o **Termo de Entrega A4 por ambiente** (checklist para marcar à caneta, espaço para pendências, assinaturas). De volta à fábrica, alguém registra "Conforme" ou "Com ressalvas" (+ pendências) e anexa a foto do termo assinado e as fotos da montagem (mecanismo de fotos da OS) | Consequência de P3 | 🟡 |
| I2 | Checklist de vistoria padrão nos Parâmetros, copiado para cada ambiente e editável ali | Mesmo padrão de P1 | 🟡 |
| I3 | Pendência aberta **avisa** ao finalizar a OS, mas **não trava** | Caso real: cliente pagou e aceitou com ressalva | 🟡 |
| I4 | Montador é sempre **funcionário** nesta fase. Sem conta a pagar por instalação | Resposta do usuário ("é sempre montador por agora") | ✅ |
| I5 | Agenda = campos na OS (data/hora da instalação + montadores). A Lista de OS filtra e ordena por essa data. Tela de agenda semanal fica para a fase 2 **Revista por I5a e T8a (Revisão 14) e I5b (Revisão 15):** agendamentos da marcenaria, aba Instalações, `data_instalacao` para o Compras. | Com um computador, a lista ordenada resolve "quem instala onde amanhã" | ✅ |
| I5a | **Revisão 14:** uma OS pode ter **vários agendamentos** (data, hora, ambientes, montadores, observação). Montador em dois agendamentos no mesmo dia: **aviso**, sem trava. Agendamento com data passada e ambiente não entregue aparece como atrasado | I6 já previa entregar a cozinha antes do closet; cada entrega tem a sua data e a sua equipe | ✅ |
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
| T3e | **Criação preguiçosa** (Revisão 7): "Novo orçamento" abre o editor sem gravar; o orçamento nasce na primeira informação real (cliente, projeto ou ambiente) | Clicar e desistir não deixa rascunho vazio nem gasta número | ✅ |
| T3f | **Visão do cliente = proposta** (Revisão 7): mostra exatamente o que a proposta (T5) mostra, inclusive **sem preço por móvel**, e fica somente leitura | O cliente não pode ver na tela algo diferente do que recebe no papel | ✅ |
| T3g | O aviso de **margem negativa** aparece também para quem não vê custos, sem números: "O desconto deixou o orçamento abaixo do custo. Fale com o responsável antes de enviar." (Revisão 7) | Sem ele, o vendedor daria desconto até o prejuízo sem saber; a frase não revela a margem | ✅ |
| T4 | Modal "Adicionar Móvel": busca de insumo no cadastro de produtos, **cadastro rápido** de produto, botão **"Duplicar móvel"**, mão de obra fixa ou por horas. O campo **"Categoria" do móvel sai** nesta fase | Categoria não era usada em cálculo nem filtro | ✅ |
| T4a | **Cadastro rápido de insumo** (Revisão 7): nome, código (sugerido), unidade, custo de compra, preço de venda e "sofre perda". Preço de venda vazio grava **igual ao custo** | `valor_varejo` é obrigatório; gravar 0 deixaria o item ser vendido de graça no PDV | ✅ |
| T4b | O modal do móvel mostra o **preço calculado enquanto o usuário digita**, pedido ao backend (`simular`), sem gravar (Revisão 7) | Ver o efeito de cada chapa antes de salvar, sem motor em TypeScript (C8) | ✅ |
| T5 | **Proposta comercial em PDF** obrigatória na fase 1. Mostra ambientes, móveis com descrição e medidas, **total por ambiente** (sem preço por móvel), condições (sinal, prazo, validade). **Nunca** mostra custos | Sem proposta não há como "Enviar". Total por ambiente é o padrão de mercado | ✅ |
| T5a | O PDF da proposta sai pelo destino **"Salvar como PDF"** do diálogo de impressão (template A4, mesmo motor das vias de OS e venda). O sistema não guarda o arquivo; o evento de envio guarda total, sinal e validade (Revisão 8) | Reaproveita cabeçalho, regra de preto e branco e quebras de página; o arquivo fica onde o vendedor escolher, pronto para anexar | ✅ |
| T6 | Seção **"Marcenaria"** em Configurações: markup, perda, validade, prazo de entrega, custo/hora, RT padrão e modo do RT, modelos de etapas, checklist de vistoria | Padrões editáveis pelo dono | ✅ |
| T7 | **Histórico** só de inclusão (nada é apagado): mudanças de status do orçamento, etapas, separação e termos, com quem fez e quando. A Spec 06A verifica se algum histórico existente da OS pode ser reaproveitado | Auditoria barata desde o primeiro projeto | ✅ |
| T8 | **Lista de OS** atual, com coluna e filtro novos de data de instalação (I5) **Revista por T8a (Revisão 14).** | Sem tela nova | ✅ |
| T8a | **Revisão de T8 (Revisão 14):** a agenda fica numa aba **"Instalações"** na tela de Serviços (só marcenaria), com filtro por período, montador e atrasadas. A Lista de OS compartilhada **não** muda | A coluna na lista compartilhada exigiria mexer na tela mais usada das 3 lojas em produção por uma informação que só a marcenaria tem (PR1) | ✅ |

### 6.7. Convergência com o código da branch (Revisão 15)

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| FB1 | **Fábrica aposentada.** `modo_fabrica_ligado()` passa a responder sempre `False`: nenhuma OS nova entra no trilho de 10 fases. Saem das telas: a chave "Modo fábrica" (Configurações › OS), a linha "Fábrica" dos cargos, a seção "Insumo da fábrica" do produto (o "sofre perda" vai para a 04B), a rota `/fabrica/separacao` e as abas Orçamento/Trilho da fábrica no modal de OS. O **banco não muda**: as 4 migrações da fábrica estão na cadeia (a fiscal `d7a3e9c2f418` vem depois delas) e podem já estar aplicadas nas lojas, então tabelas e colunas ficam, vazias. O código backend da fábrica fica **inerte** (só age em OS com `fase_fabrica`, que nenhuma OS tem) e sai numa spec de limpeza depois do piloto. O "devolver tudo ao cancelar" da fábrica passa a valer só para OS com `fase_fabrica` (senão anularia E2a). Specs 03A e 03B | Dois desenhos para o mesmo negócio na mesma branch. A 03A (OS só nasce do orçamento) quebraria a fábrica, e o trilho (status travado) quebraria a P2b. Nenhuma loja usa a marcenaria (usuário, 08/10) | ✅ |
| FB2 | **Compras e etiquetas prevalecem.** Onde as specs tinham planejado peça própria e o sistema já tem módulo, usa-se o módulo como ele é. Mudança nesses módulos só **aditiva** e só se indispensável (os campos do móvel no motor de etiquetas, Spec 14) | Decisão do usuário (08/10). Os módulos já foram testados e podem estar nas lojas; duas versões da mesma regra acabariam discordando | ✅ |
| F2b | **Revisão de F2:** na aprovação, os insumos dos móveis **internos** aprovados entram na OS como **peças embutidas**: um item `PRODUTO` por produto (a soma de todos os móveis, com a perda), `quantidade` = o sugerido de E3b, `valor_unitario = 0`, `visivel_cliente = false`, `custo_unitario` = custo copiado do orçamento, `origem = ORCAMENTO_MARCENARIA`. Móveis e instalação continuam itens de serviço (F2) | O Compras (reserva, Necessidades, "Compras desta OS") enxerga material pelos itens de produto da OS. A peça embutida não aparece para o cliente nem soma no total (o motivo original de F2: o cliente não paga duas vezes), e a comissão não muda (só conta item de serviço, `get_comissao_base`). E, se a separação não for usada, a finalização baixa o material (regra de hoje) e o CMV o conta | 🟡 (recomendação do plano de 08/10) |
| E1b | **Revisão de E1/E1a:** reserva e disponível vêm de `services/compras/demanda_os` (já somam `quantidade − quantidade_separada` dos itens de produto das OS abertas, de todos os segmentos). Nenhuma consulta própria da marcenaria; vale com ou sem o módulo COMPRAS contratado (é função do backend, não tela) | FB2. Com F2b, a chave da marcenaria e a peça da oficina disputam a mesma prateleira na mesma conta | ✅ |
| E3b | **Revisão de E2a/E3/E3a:** a separação opera sobre os itens de insumo da OS (um por produto, já somados, E3a). Retirar = SAÍDA no livro + `quantidade_separada`; devolver = ENTRADA − `quantidade_separada`; concluir com menos = a `quantidade` do item passa a ser o retirado (a finalização não baixa a sobra e a reserva solta); retirar mais que o sugerido é permitido com aviso (a `quantidade` acompanha). O "arredonda para cima" usa `UNIDADES_FRACIONAVEIS`. Cancelar a OS **não** devolve sozinho (E2a mantida). A tabela `marcenaria_separacao` sai | Reaproveita as colunas que a finalização e o Compras já entendem; uma regra só para baixa, reserva e finalização | ✅ |
| E5a | **Revisão de E5:** a lista de compras é a tela **Necessidades** do Compras (módulo COMPRAS), que já agrupa por fornecedor e gera o pedido. Sem o módulo, a aba Separação mostra e imprime as faltas **daquela OS**. A aba "Lista de compras" planejada em Produtos sai | FB2 | 🟡 (o modo sem Compras) |
| E6b | **Revisão de E6/E6a:** com o módulo COMPRAS, "Pedir à central" cria um **pedido de compra `SERVICO`** (o mesmo caminho da fábrica F5), e o recebimento no Compras lança as contas a pagar. A oferta de conta própria e a categoria "Produção terceirizada" da 11A saem: conta sem categoria já conta como despesa no resultado (`crud/financeiro._total_pago`). Sem o módulo, a situação é marcada à mão (A pedir → Pedido enviado → Recebido → Conferido, com o nº do pedido em texto) e a conta é lançada em Contas a Pagar. "Conferido" e "registrar problema" são da marcenaria nos dois casos | FB2 | 🟡 (o modo sem Compras) |
| I5b | **Complemento de I5a:** a OS guarda em `ordens_servico.data_instalacao` a data do próximo agendamento ainda não entregue | A coluna existe (fábrica F3) e só o Compras a lê: a fila de material atende primeiro quem instala primeiro (RC12). Nada muda na Lista de OS (T8a) | ✅ |
| R15-CNPJ | A consulta de CNPJ no cliente **já existe** (`011dff7`). O preenchimento de hoje prevalece (sobrescreve razão social e endereço com a Receita; preenche o regime MEI/Simples). A Spec 02 fica com o que falta: erro "sem internet" × "não encontrado", tempo limite, dígito verificador antes da consulta automática e aviso de cliente duplicado | O código já está na linha de produção e o preenchimento do regime resolveu uma rejeição real da SEFAZ (06/10) | ✅ |
| R15-MIG | **Códigos de migração novos** (os planejados colidiam com 7 migrações existentes), em cadeia a partir de `d7a3e9c2f418`: 04A `608dc99a8616` → 06A `683ff38df873` → 08A `971eb6cc5a33` → 09A `195109da93f7` → 11A `642b2e8f79fa` → 12A `072437088f6c` → 13A `2c4df92b1412`. A 10A não tem migração (E3b). Antes de cada uma, `alembic heads`: se outra branch tiver acrescentado migração, o `down_revision` acompanha | Dois arquivos com o mesmo código quebram a atualização do banco das lojas | ✅ |

**Achado registrado (não é da marcenaria):** o Compras lança a conta do recebimento **sem categoria**, e conta sem categoria conta como despesa; o material comprado sai do lucro no pagamento **e** de novo no CMV quando baixa. Afeta todo segmento que usar o Compras. Registrado como **PEND-003** em `docs/pendencias-sistema.md`; a marcenaria não o corrige (FB2).

---

## 7. Fora da fase 1

| Item | Quando | Observação |
|------|--------|------------|
| **Reforma de móveis** (segundo tipo de trabalho) | Fase seguinte | Referência completa na §7.1 (Revisão 4) |
| Importação de projeto 3D (Promob, CorteCloud, Dinabox, UpMob) | Fase 2 | Depende de arquivos reais da fábrica |
| Aditivos após aprovação | Fase 2 | Hoje: nova versão antes de aprovar, ou cancelar e refazer |
| Kanban de produção com cronômetro | Fase 2 | Usa o histórico de etapas (T7) |
| Agenda semanal de instalação | Fase 2 | Hoje: agendamentos da marcenaria e a aba Instalações em Serviços (I5a, T8a) |
| Vários comissionados na mesma tela | Fase 2 | O modelo de dados já aceita N |
| Versão celular/tablet | Futuro | P3 |
| Etiqueta por peça / plano de corte | Futuro | Depende da importação 3D |
| Contrato em PDF, assinatura digital, WhatsApp | Futuro | — |
| Cobrança parcial por ambiente | Futuro | I6 |
| Pedido de compra gerado pela lista de compras | — | **Resolvido pelo Compras** (E5a): a tela Necessidades gera o pedido |
| Limpeza do código da fábrica aposentada | Depois do piloto | FB1: o código inerte sai; tabelas e colunas ficam |


### 7.1. Referência: Reforma de móveis (para a volta)

O cliente traz o móvel (ou a loja busca) e a loja restaura, pinta ou troca peças. É conserto, como na oficina: **não usa** o orçamento técnico, e o cliente aprova item a item. Estado em `feat/segmento-marcenaria @ f040e8d`, antes da Spec 03A:

| Campo | Rótulo | Tipo | Escopo | Observação |
|-------|--------|------|--------|------------|
| `nome_projeto` | Móvel | texto, obrigatório | objeto (coluna `modelo`) | ex.: "Guarda-roupa 3 portas" |
| `servico_reforma` | O que fazer | opção: Restauração, Troca de peça, Pintura / verniz, Ajuste, Outro | OS | |
| `material` | Material | texto | OS | |
| `acabamento` | Acabamento / cor | texto | OS | |
| `movel_trazido` | Móvel trazido pelo cliente | booleano | OS | desmarcado = a loja busca |
| `etapa` | Etapa atual | opção: Aguardando aprovação, Aguardando material, Separação, Corte, Montagem interna, Concluído | OS | informativa, sem automação |

**Para voltar, será preciso:**
1. Declarar o tipo `reforma_moveis` com `criacao_manual=True` (os campos acima).
2. **Devolver `CAP_APROVACAO_ITENS`** à marcenaria e esconder os controles de aprovação nos itens vindos do orçamento (a capacidade é do segmento; ver Revisão 3).
3. Gravar o tipo padrão na criação da OS: com Planejados não criável, o seletor fica com uma opção só e se esconde, e hoje o tipo padrão só é **mostrado**, não gravado (achado na Spec 03B, versão de 06/10, §8).
4. Os textos de impressão da Reforma **continuam no código**: são o pacote base `MARCENARIA` em `textosImpressaoOS.ts` (Planejados é a sobrescrita `porTipoTrabalho.planejados`).
5. O rótulo "Aguardando Entrega" (Spec 01A) já serve à Reforma.
---

## 8. Lista de specs

⚠️ = toca código compartilhado com outros segmentos (prova de não regressão obrigatória).

| Spec | Camada | Título | Depende de | Decisões |
|------|--------|--------|------------|----------|
| 00 | Documento | Registro de decisões | — | Todas |
| 01A ⚠️ | Backend | Rótulos de status por segmento (registry) | 00 | P2a |
| 01B ⚠️ | Frontend | Rótulos de status por segmento (telas, filtros e dashboard) | 01A | P2a |
| 02 ⚠️ | Frontend | Consulta de CNPJ no cliente: o que falta (erro tipado, tempo limite, duplicidade) | 00 | O6, R15-CNPJ |
| 03A ⚠️ | Backend | Ajuste do segmento (só Planejados, trava de criação, sem aprovação por item) e **aposentadoria da fábrica** | 01A | O4, E0, E0a, E0b, FB1 |
| 03B ⚠️ | Frontend | Ajuste do segmento (botão Criar OS, tipo travado, textos, fallback) e **retirada das telas da fábrica** | 03A | O4, E0, E0a, E0b, E0c, FB1 |
| 04A ⚠️ | Backend | Base: `sofre_perda` no contrato do produto, Parâmetros, permissão "ver custos" | 03A | F6, T6, P4, R15-MIG |
| 04B ⚠️ | Frontend | Base: campo no produto, seção Marcenaria em Configurações, permissão no cargo | 04A | F6, T6, P4 |
| 05 | Backend | Motor de cálculo (funções puras + testes) | 04A | C1–C9, O3a |
| 06A | Backend | Orçamento: modelo de dados, API, versões, validade, autosave, histórico | 05 | F1, O1–O3, T7 |
| 06B ⚠️ | Frontend | Orçamento: lista, menu, editor, modal Adicionar Móvel | 06A | T2–T4 |
| 07 | Frontend | Proposta comercial em PDF | 06B | T5 |
| 08A ⚠️ | Backend | Aprovação → OS (parcial, itens travados, insumos como peças embutidas, desfazer) | 06A | F2–F4, F2b, O4, O5, O7, O8 |
| 08B ⚠️ | Frontend | Aprovação → OS (modal de aprovação, aba Orçamento, itens travados) | 08A, 06B | F4, T1 |
| 09A ⚠️ | Backend | RT do arquiteto (conta a pagar na finalização) e CMV sem dupla contagem | 08A | C5a–C5e, F2a |
| 09B ⚠️ | Frontend | RT do arquiteto (campo no orçamento, tipo de fornecedor) | 09A, 06B | C5a, C5c, C5e |
| 10A | Backend | Separação sobre os itens da OS, disponível pelo Compras, leitor, faltas da OS | 08A | E1b, E2, E3b, E4, E5a |
| 10B ⚠️ | Frontend | Aba Separação (leitor), faltas da OS, disponível na busca de insumo | 10A | E3b, E4, E5a |
| 11A | Backend | Terceirizados (situação, pedido `SERVICO` do Compras, modo manual sem Compras) | 08A, 09A | E6b |
| 11B ⚠️ | Frontend | Terceirizados (na aba Separação; aba Terceirizados em Serviços) | 11A, 10B | E6b |
| 12A | Backend | Produção: etapas por móvel | 08A, 11A | P1, P1a, P2, P2b |
| 12B ⚠️ | Frontend | Aba Produção, pergunta de status, quadro da fábrica | 12A | P1, P1a, P2, P2b |
| 13A | Backend | Entrega: termos, pendências, fotos, agendamentos | 08A, 12A | I1–I6, I5a, I5b, T8a |
| 13B ⚠️ | Frontend | Aba Entrega, Termo A4, aba Instalações em Serviços, aviso na finalização | 13A | I1–I6, I5a, T8a |
| 14 | Frontend | Etiquetas por volume do móvel, sobre o motor `shared/etiquetas` | 12B, 13A | I7, FB2 |

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
| Duas implementações do mesmo negócio (specs × fábrica) | FB1: a fábrica é aposentada antes de qualquer código novo da marcenaria (Specs 03A/03B) |
| Regra duplicada com Compras ou etiquetas | FB2: reserva, lista de compras, central parceira e etiquetas usam os módulos como são |
| Código de migração repetido | R15-MIG: códigos gerados e conferidos contra a pasta `alembic/versions` |

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
