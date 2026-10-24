# Faturamento da marcenaria — plano de implementação

> **Status:** plano, 24/10/2026. Nada implementado. Branch sugerida:
> `feat/marcenaria-faturamento`, saindo de `feat/marcenaria-remodelacao`.
> Head de migration hoje: `a7d1t1v0os01`.

## 0. O problema, em uma frase

A NF-e da OS (`services/fiscal/emissoes/nfe_os.py` + `adaptador_os.py`) só
fatura itens `PRODUTO`. Na marcenaria os **móveis e a instalação são
`SERVICO`** (decisão C5: a comissão sai da margem dos itens de serviço) e os
**insumos embutidos são `PRODUTO` a R$ 0** (F2b). Se alguém emitir hoje, a nota
sai **só com as chapas a zero e sem nenhum móvel**.

O cliente piloto já trabalha no fluxo de indústria: entra o material, a
produção o consome, o móvel entra no estoque como **produto acabado** e é ele
que sai na NF-e. É o mesmo fluxo dos ERPs industriais (pedido → ordem de
produção → apontamento → faturamento). Este plano leva esse fluxo para o
sistema: nota na entrega, entrega futura, terceirizado e instalação embutida
na nota ou fora dela.

> **NFS-e fica fora** (decisão do Alan, 24/10/2026): o sistema ainda não emite
> NFS-e, e isso só será tratado depois que a marcenaria estiver organizada.
> Ver §8.

## 1. Regras que não mudam (para não quebrar quem usa)

| # | Regra |
|---|---|
| R1 | Tudo nasce **desligado**: `faturamento_modo = DESLIGADO`. Desligado, a NF-e da OS da marcenaria se comporta como hoje, e a dos outros segmentos **nunca** passa pelo código novo. |
| R2 | Dentro da OS, o móvel **continua `SERVICO`**. Comissão (C5/C5d), CMV (F2a), separação, aditivo e relatórios não mudam. A troca para "produto" acontece só no adaptador fiscal. |
| R3 | As movimentações do produto acabado usam uma **origem nova, `PRODUCAO`**. `get_cmv_os` / `get_cmv_vendas` filtram por `ORDEM_SERVICO` / `VENDA`, então o material **não** é contado duas vezes (ele já entra no CMV pela baixa da separação). Nenhuma query existente muda. |
| R4 | Um teste de **payload de ouro** da NF-e de OS da informática/oficina/serigrafia é escrito **antes** de qualquer mudança (F0) e precisa continuar idêntico até o fim. |
| R5 | Migrations: uma por fase, encadeadas em linha (`+1`), decidindo pela presença do schema antigo; nunca `alembic merge`. Testar em **banco copiado** das lojas. |
| R6 | Arquivos `.py` abaixo de 64 KB (PyArmor trial). O adaptador da marcenaria nasce em arquivo próprio, não engorda `adaptador_os.py` nem `nfe_os.py`. |

## 2. Decisões (confirmar com o contador do cliente antes da F3)

| # | Decisão proposta | Por quê | A confirmar |
|---|---|---|---|
| D1 | Unidade de faturamento = **móvel**. Cada móvel aprovado é faturado uma vez só (trava por móvel, não por OS). | A entrega é por ambiente, em dias diferentes; cada saída de mercadoria precisa de nota. | — |
| D2 | **Produto acabado genérico** por tipo ("Cozinha planejada", "Guarda-roupa planejado", "Móvel planejado"), com o cadastro fiscal normal do produto (NCM, CST/CSOSN, origem). Na nota, a **descrição é o nome do móvel** ("Torre Quente — Cozinha Gourmet"). | Um produto por móvel incharia o cadastro; o motor fiscal já sabe ler produto. | NCM de cada tipo |
| D3 | Cada móvel do orçamento ganha o campo **"Tipo fiscal"** (qual produto acabado), com o padrão vindo da configuração. | Uma OS pode ter cozinha (9403.40) e dormitório (9403.50). | — |
| D4 | Móvel **interno** → CFOP de **produção própria** (5101/6101/6107). Móvel **terceirizado** (comprado pronto da central) → **revenda** (5102/6102/6108), com produto acabado próprio. | Quem fabrica é outro estabelecimento. | Sim: terceirizado é revenda mesmo? |
| D5 | O CFOP de produção própria é **forçado pelo modo marcenaria**, sem depender de `empresa.tipo_atividade == INDUSTRIA`. | Hoje `MISTO` vira 5102 (`derivacao/cfop.py`), o que estaria errado para quem fabrica. | — |
| D6 | **Instalação**: dois modos. `EMBUTIDA` (padrão: o valor é rateado no preço dos móveis da NF-e; é acessória à venda) ou `FORA` (a instalação não entra na NF-e; a nota de serviço é emitida fora do sistema, na prefeitura). O modo `NFSE` entra depois (§8). | As fontes tratam a instalação como acessória à venda e alertam para não separar só para pagar menos imposto. | Qual modo |
| D7 | **Modo de faturamento**: `NOTA_NA_ENTREGA` (5101 a cada entrega) ou `ENTREGA_FUTURA` (5922 no fechamento + 5116/5117 a cada entrega, referenciando a 5922). | São as duas práticas do mercado de planejados. | Qual o cliente usa (ver a nota dele) |
| D8 | O **desconto, o acréscimo e a taxa de entrega** da OS são rateados entre os móveis faturados, como o adaptador já faz para as peças (`_desconto_dos_produtos`). Em nota parcial (um ambiente), entra a fatia proporcional daquela entrega. | Mesma regra que já passou pela SEFAZ. | — |
| D9 | **Custo do produto acabado** = custo de material do móvel no orçamento (insumos × perda), não o `custo_os_unit_centavos` (que inclui RT e mão de obra). | Estoque de acabado se avalia pelo material; RT e mão de obra entram no resultado pelos seus registros (F2a). | Sim, se ele quer mão de obra no custo do acabado |
| D10 | Os produtos acabados **não aparecem no PDV nem nas Necessidades do Compras** (filtro pelos ids guardados na configuração da marcenaria, só no segmento marcenaria). | Evita vender "Cozinha planejada" no balcão ou pedir à central. | — |
| D11 | Sinal recebido antes da nota entra no grupo de pagamento proporcional (já é assim). Na 5922 sem pagamento, `detPag` = 90 (sem pagamento) ou o combinado, a confirmar. | — | Sim |

## 3. Modelo de dados (todas aditivas)

**Migration F1** (`marcenaria_faturamento_base`, `down_revision = 'a7d1t1v0os01'`):

- `configuracoes_marcenaria` + colunas (ADD COLUMN só se faltar):
  - `faturamento_modo` `VARCHAR(20)` default `'DESLIGADO'` — `DESLIGADO | NOTA_NA_ENTREGA | ENTREGA_FUTURA`
  - `instalacao_modo` `VARCHAR(10)` default `'EMBUTIDA'` — `EMBUTIDA | FORA` (o `NFSE` da §8 será só um valor a mais, sem migration)
  - `produto_acabado_padrao_id` FK `produtos.id` NULL
  - `produto_acabado_revenda_id` FK `produtos.id` NULL (terceirizado, D4)
- `marcenaria_moveis` + `produto_acabado_id` FK `produtos.id` NULL (D3; NULL = usa o padrão).
- Tabela nova **`marcenaria_moveis_faturamento`** (uma linha por móvel):
  `id, os_id, movel_id UNIQUE, produto_id, quantidade, custo_unitario_centavos,
  mov_entrada_id, mov_saida_id, documento_fiscal_id NULL, documento_simples_faturamento_id NULL,
  situacao (NO_ESTOQUE | FATURADO | ESTORNADO), criado_em, atualizado_em`.
  É ela que garante D1 (um móvel, uma nota) e liga produção → estoque → nota.

**Migration F4** (`documento_fiscal_papel`):
- `documento_fiscal` + `papel` `VARCHAR(25)` NULL — `NULL` (todos os documentos de hoje) |
  `SIMPLES_FATURAMENTO` | `REMESSA_ENTREGA_FUTURA` | `VENDA_MARCENARIA`. NULL preserva o comportamento atual de toda nota existente.

`MovimentacaoOrigem.PRODUCAO` é só um valor novo no enum Python: a coluna `origem` é `String(20)`, sem CHECK. Sem migration.

## 4. Fases

Cada fase fecha com `pytest` verde, `vitest` verde, `vue-tsc` 0, o teste de
ouro (R4) idêntico e commit próprio. Nenhuma fase depende de ligar a anterior
em produção.

### F0 — Base de segurança (sem mudança de comportamento)
- **Teste de ouro**: payload NF-e de OS de informática, oficina e serigrafia (com peça, mão de obra, desconto, taxa de entrega) gravado em fixture; o teste compara o dict inteiro.
- **Teste que documenta o bug de hoje**: NF-e de OS da marcenaria sai com os insumos a R$ 0. Na F3 ele passa a afirmar o certo.
- Coletar a nota que o sistema atual do cliente emite para um móvel (XML) e guardar em `docs/payloads/marcenaria/`: é o alvo da F3/F4.

### F1 — Configuração e produto acabado
**Backend**
- Migration F1 (§3). Model, schema (`schemas/configuracao/marcenaria.py`) e service (`services/configuracao/marcenaria.py`) com os campos novos.
- Validação no PUT: modo ≠ `DESLIGADO` exige `produto_acabado_padrao_id` com cadastro fiscal completo (reusa `verificar_produto_fiscal`).
- Ação "Criar produtos acabados sugeridos": cria "Móvel planejado (produção própria)" e "Móvel planejado (revenda)" com unidade UN, sem preço, com estoque controlado, e o fiscal em branco para o contador preencher.
- `marcenaria_moveis.produto_acabado_id` no schema do orçamento (leitura e edição), copiado na nova versão e no aditivo.
- Filtro D10 no PDV e nas Necessidades.

**Frontend**
- Configurações › **Marcenaria** › bloco **"Faturamento dos móveis"**: modo, instalação, produto acabado padrão, produto de revenda; aviso do que falta no cadastro fiscal, com link para o produto.
- Editor do orçamento: campo "Tipo fiscal" por móvel (some se o modo for `DESLIGADO`).

**Pronto quando:** dá para configurar tudo e nada muda em nenhuma OS.

### F2 — Entrada de produção (o móvel vira estoque)
- `services/marcenaria/faturamento/estoque_acabado.py`:
  - `dar_entrada(db, movel)`: quando o móvel fica **pronto** (última etapa concluída — `producao.py`; terceirizado `CONFERIDO` — `terceirizados`), cria `MovimentacaoEstoque(ENTRADA, origem=PRODUCAO, ordem_servico_id, quantidade=movel.quantidade, custo=D9)` e a linha `marcenaria_moveis_faturamento(NO_ESTOQUE)`. Idempotente (o `movel_id` é UNIQUE).
  - `estornar_entrada(db, movel)`: etapa desmarcada ou terceirizado voltou um passo → `SAIDA` de estorno (origem `PRODUCAO`), linha `ESTORNADO`. **Bloqueado** se o móvel já foi faturado (mensagem: cancele a nota antes).
  - Desfazer aprovação e cancelar OS: estornam o que estiver `NO_ESTOQUE`; bloqueiam se houver móvel faturado.
- Só age com `faturamento_modo ≠ DESLIGADO`. Para ligar com OS em andamento: botão "Dar entrada dos móveis já prontos" (retroativo, idempotente).
- Aba **Produção**: selo "No estoque" / "Faturado" em cada móvel.
- Testes: CMV do mês **idêntico** com e sem a entrada (R3); estoque do produto acabado sobe e desce; idempotência; estorno bloqueado após a nota.

### F3 — NF-e de venda (modo `NOTA_NA_ENTREGA`)
- `services/fiscal/emissoes/adaptador_marcenaria.py`: cria um `OSComoVenda` cujos itens são os **móveis selecionados** (via `movel.os_item_id`), com `produto` = produto acabado do móvel, `descricao` = nome do item da OS, quantidade e valor do item da OS. Insumos embutidos (`visivel_cliente=False`, valor 0) **ficam de fora**. Instalação: `EMBUTIDA` → valor rateado nos móveis da nota pelo valor de cada um; `FORA` → fora da NF-e.
- `payload/itens.py`: aceitar uma `descricao` do item adaptado, usando `produto.nome` quando ela não vem. Mudança de uma linha, coberta pelo teste de ouro (os outros segmentos não passam a descrição).
- CFOP: D4/D5 através de `derivar_cfop_operacao(eh_producao_propria=...)` por item. Interestadual e não contribuinte usam o motor DIFAL que já existe (6107/6108).
- `nfe_os.py`: se a OS é da marcenaria e o modo está ligado, delega para o adaptador novo. A trava "uma NF-e por OS" vira, só nesse caminho, "**cada móvel em no máximo uma nota ativa**" (pela `marcenaria_moveis_faturamento`).
- Autorizada → `SAIDA` origem `PRODUCAO` do produto acabado + linha `FATURADO` com `documento_fiscal_id`. Cancelada → `ENTRADA` de estorno + volta a `NO_ESTOQUE`. Rejeitada → nada muda no estoque.
- Completude (`verificar_completude_os`): pendências próprias ("móvel X sem tipo fiscal", "produto acabado sem NCM", "móvel ainda não está pronto").
- **Tela**: na aba **Entrega** de cada ambiente, botão **"Emitir NF-e desta entrega"** (pré-seleciona os móveis do ambiente) e, na OS, "Emitir NF-e" com a lista dos móveis prontos e não faturados. Pré-visualização (`preview_nfe_os`) antes de emitir.
- Testes: payload contra o XML do cliente (F0); nota parcial com rateio fechando ao centavo; terceirizado com CFOP de revenda; interestadual; trava de duplicidade por móvel; cancelamento devolve o estoque.

### F4 — Entrega futura (modo `ENTREGA_FUTURA`)
- Migration F4 (`documento_fiscal.papel`).
- **Simples faturamento (5922/6922)**: emitido na aprovação ou por botão na OS. Itens = todos os móveis aprovados; **sem ICMS destacado**, **sem movimentar estoque**; natureza "Simples faturamento — venda para entrega futura". Um por OS; o aditivo gera a sua própria 5922 (do valor do aditivo).
- **Remessa (5116 produção / 5117 revenda; 6116/6117 interestadual)**: a cada entrega, como na F3, com ICMS, saída de estoque e `notas_referenciadas = [chave da 5922]` (o builder já monta isso na devolução).
- Travas: remessa exige 5922 autorizada; soma das remessas ≤ 5922 (por móvel e em valor); cancelar a 5922 é bloqueado enquanto houver remessa autorizada.
- `PALAVRAS_QUE_DISPENSAM_TRIBUTOS` inclui "REMESSA": conferir se a natureza da 5116 desliga o `vTotTrib` e se isso está certo para a remessa (Lei 12.741).
- Testes: ciclo completo 5922 → duas remessas parciais → total bate; aditivo com 5922 própria; cancelamentos na ordem certa.

### F5 — Homologação e canário
1. Ambiente de **homologação** da SEFAZ com a empresa piloto: um roteiro por modo (nota na entrega; entrega futura com duas remessas; terceirizado; interestadual; instalação embutida e fora; cancelamentos).
2. Comparar o XML gerado com a nota do sistema atual do cliente (F0), campo a campo.
3. Migrations num **banco copiado** de cada loja em produção: nenhuma linha muda, CMV e comissão do mês e dos três anteriores idênticos.
4. `npm run build:sidecar` + instalador desta branch; canário no cliente piloto com backup do `start_big.db`.

## 5. Arquivos tocados (previsão)

| Camada | Novos | Alterados (mudança aditiva) |
|---|---|---|
| Migrations | 2 (F1, F4) | — |
| Models | `marcenaria/faturamento.py` | `configuracao_marcenaria.py`, `marcenaria/ambiente.py` (1 coluna), `documento_fiscal.py` (1 coluna), `core/enum.py` (`PRODUCAO`) |
| Services | `marcenaria/faturamento/{estoque_acabado,emissao}.py`, `fiscal/emissoes/adaptador_marcenaria.py` | `fiscal/emissoes/nfe_os.py` (desvio), `fiscal/payload/itens.py` (descrição), `fiscal/completude/*`, `marcenaria/producao.py` e `terceirizados` (gancho de "pronto"), `marcenaria/aprovacao.py` (desfazer), `configuracao/marcenaria.py` |
| API | endpoints `marcenaria_faturamento.py` | — |
| Frontend | `marcenaria/faturamento/` (seleção de móveis, selos) | `configuracoes/.../Marcenaria.vue`, editor do orçamento, aba Entrega, `NotaFiscalSection.vue`, Centro Fiscal |
| Plataforma web | — | nenhuma: a NF-e usa as rotas que já existem |

## 6. Riscos

| Risco | Mitigação |
|---|---|
| NF-e dos outros segmentos muda sem querer | R1 + teste de ouro (R4) em toda fase |
| CMV contado duas vezes | R3 (origem `PRODUCAO`) + teste de CMV idêntico na F2 |
| Nota aceita e errada (CFOP/NCM) | D2–D5 confirmados pelo contador; homologação comparando com o XML do cliente |
| Móvel faturado duas vezes | `movel_id UNIQUE` + trava por móvel na emissão |
| Desfazer/cancelar OS com nota autorizada | bloqueado com mensagem (F2/F3) |
| Reforma tributária (IBS/CBS nos XMLs a partir de 2026) | fora deste plano: segue o que o motor fiscal fizer para a venda, porque o adaptador reusa o mesmo caminho |

## 7. O que pedir ao cliente agora (F0)
1. O **XML** de uma NF-e de móvel emitida pelo sistema atual (e, se houver, a de simples faturamento e a de remessa).
2. Como os produtos acabados estão cadastrados lá (NCM de cada tipo).
3. Se a instalação sai na mesma nota ou numa nota de serviço à parte.

## 8. Depois: NFS-e (fora deste plano)

Só depois de a marcenaria estar organizada. Anotado para não se perder:
- A plataforma **não tem rota de NFS-e**: `/erp/fiscal/nfse/*` deu 404 no curl de 24/10 (`/erp/fiscal/nfe/emitir` deu 401). O trabalho começa pelo lado web.
- O que já existe no ERP: `documento_fiscal.tipo_documento` (`String(5)`) comporta `'NFSE'`; `ordem_servico_nota_fiscal` tem `status_nfse`, `numero_nfse`, `codigo_verificacao_nfse` e `url_nfse`; `empresa_fiscal_settings` tem `rps_serie`, `rps_ultimo_numero` e `regime_tributacao_iss`; `empresa.inscricao_municipal` existe; `verificar_itens_os_nfse` valida o código LC 116 do serviço; o checkbox `emitir_nfse` da `NotaFiscalSection.vue` existe, mas não emite nada.
- Caminho provável: padrão nacional (DPS / Sistema Nacional NFS-e, via Focus NFe), atrás de um módulo `NFSE` da licença, negado sem resposta.
- Na marcenaria, entra como o terceiro modo da instalação (`NFSE`). Para isso, `configuracoes_marcenaria` ganha `servico_instalacao_id`.
