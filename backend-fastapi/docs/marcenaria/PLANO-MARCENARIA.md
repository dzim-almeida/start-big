# Plano Completo — Segmento Marcenaria (Fase 1)

| Campo      | Valor                                                                             |
|------------|-----------------------------------------------------------------------------------|
| Status     | Specs aprovadas pelo usuário (Revisão 16, 08/10/2026) — implementação a partir do Marco 1 |
| Data       | 08/10/2026                                                                        |
| Branch     | `feat/segmento-marcenaria` @ `53e5d81`                                            |
| Documentos | `SPEC-00` (decisões) + 24 specs de implementação nesta pasta + `docs/pendencias-sistema.md` |

Este documento junta as 25 specs num só plano: o que a fase 1 entrega, em que ordem construir, onde mexemos no código das lojas em produção, o que ficou pendente e o que conferir antes do piloto. Ele **não** substitui as specs: cada linha aponta para a spec que tem os detalhes. Quando uma spec e este plano discordarem, vale a spec (e este plano deve ser corrigido).

> **Revisão 15 (08/10/2026).** Depois dos merges de 08/10 (Compras, etiquetas, embalagens, venda fracionada, fiscal e a "fábrica"), as specs foram ajustadas ao código que já existe: a **fábrica é aposentada** (FB1), **Compras e etiquetas prevalecem** (FB2), os **insumos entram na OS como peças embutidas** (F2b) e a separação usa as colunas que a OS e o Compras já entendem (E3b). Detalhes na SPEC-00 §6.7.

---

## 1. O que a fase 1 entrega

**Objetivo (SPEC-00):** a fábrica piloto leva **um projeto real** do orçamento à assinatura do termo de entrega pelo sistema, sem planilha, e os três segmentos em produção (informática, oficina, serigrafia) seguem **idênticos**.

O caminho completo de um projeto, e a spec de cada passo:

| # | Passo | Quem faz | Specs |
|---|-------|----------|-------|
| 1 | Cadastra o cliente (com consulta de CNPJ) e o arquiteto que indicou | Vendedor | 02, 09B |
| 2 | Monta o orçamento: ambientes, móveis, insumos do estoque, mão de obra, terceirizados, instalação, desconto, sinal; o rascunho salva sozinho | Vendedor | 05, 06A, 06B |
| 3 | Vê custo, margem e RT (só quem tem permissão) e mostra a "visão do cliente" | Dono / vendedor | 04A, 04B, 06B |
| 4 | Gera a proposta em PDF e envia; versões, vencimento, renovação, atualização de preços | Vendedor | 06A, 06B, 07 |
| 5 | Aprova (todo ou em parte), diz se o sinal foi pago, e o sistema cria a OS com os móveis e os insumos (peças embutidas) | Vendedor | 08A, 08B |
| 6 | Separa o material do estoque (com leitor) e vê o que falta; com o módulo Compras, a falta vira necessidade e pedido | Fábrica / compras | 10A, 10B + **Compras** |
| 7 | Pede os móveis terceirizados à central (pedido `SERVICO` do Compras ou marcação manual), recebe, confere | Fábrica / compras | 11A, 11B + **Compras** |
| 8 | Marca as etapas de produção de cada móvel; o status da OS acompanha (com pergunta) | Fábrica | 12A, 12B |
| 9 | Imprime as etiquetas dos volumes | Fábrica | 14 + **etiquetas** |
| 10 | Agenda a instalação, imprime o termo por ambiente, registra a entrega e as pendências | Atendimento / montador | 13A, 13B |
| 11 | Finaliza a OS (pagamentos de sempre); o material que não foi separado baixa aqui; o RT do arquiteto vira conta a pagar | Atendimento | 09A |
| 12 | O resultado do mês mostra cada custo uma vez (material, RT, terceirizado, salários) | Dono | 09A (F2a) |

Fora da fase 1 (SPEC-00 §7): Reforma de móveis (referência guardada em §7.1), importação 3D e plano de corte, vários arquitetos na tela, agenda em calendário, cobrança por ambiente, versão celular/tablet, limpeza do código da fábrica aposentada (depois do piloto).

---

## 2. As 25 specs

Tamanho é uma **estimativa relativa** de esforço (P = pequeno, M = médio, G = grande), para planejar a sequência; não é prazo.

| Spec | Camada | O que entrega | ⚠️ Mexe em código compartilhado | Tamanho |
|------|--------|---------------|-------------------------------|---------|
| 00 | Documento | Registro de todas as decisões (com 15 revisões) | — | — |
| 01A | Backend | Rótulos de status por segmento no registry ("Em Produção", "Aguardando Material", "Aguardando Entrega") | ⚠️ registry, dashboard | P |
| 01B | Frontend | Rótulos nas telas, filtros e dashboard; correção do rótulo de desfecho (exceção ao PR1 aprovada) | ⚠️ lista de OS, resumo, filtros, dashboard | M |
| 02 | Frontend | O que falta na consulta de CNPJ do cliente: erro tipado, tempo limite, dígito verificador, duplicidade | ⚠️ cadastro de cliente (todos os segmentos ganham) | P |
| 03A | Backend | Marcenaria só com "Móveis planejados"; OS só nasce de orçamento; **fábrica aposentada** | ⚠️ criação/edição/cancelamento de OS | P |
| 03B | Frontend | Botões "Criar OS" somem onde não há tipo criável; tipo travado; textos; **telas da fábrica retiradas** | ⚠️ tela de OS, menu rápido, Configurações › OS, cargos, produto | M |
| 04A | Backend | `sofre_perda` no contrato do produto (a coluna já existe), parâmetros da marcenaria, permissões de custo, capacidade `orcamento_tecnico` | ⚠️ schemas de produto | M |
| 04B | Frontend | Caixa "Sofre perda" no produto, Configurações › Marcenaria, linha "Custos da Marcenaria" nos cargos (mecanismo `segmento` existente) | ⚠️ produto, configurações, cargos | M |
| 05 | Backend | Motor de cálculo (funções puras, centavos e basis points, sem `float`) | — | M |
| 06A | Backend | Orçamento: tabelas, ciclo de vida, versões, trava de edição, anexos, histórico (3 revisões) | — | G |
| 06B | Frontend | Lista, editor em página inteira, salvamento automático, modal do móvel, cadastro rápido de insumo, menu e atalhos | ⚠️ menu, menu rápido, tela de OS, cargos | G |
| 07 | Frontend | Proposta comercial A4 ("Salvar como PDF") | — | M |
| 08A | Backend | Aprovação → OS (parcial; móveis como serviço; insumos como peças embutidas), sinal, trava de itens, desfazer (2 revisões) | ⚠️ coluna `origem` nos itens de OS e trava | G |
| 08B | Frontend | Modal de aprovação, orçamento aprovado, aba "Orçamento" e cadeado nos itens da OS | ⚠️ abas e itens do modal de OS | M |
| 09A | Backend | RT do arquiteto como conta a pagar na finalização; ganchos da OS; CMV sem dupla contagem (1 revisão) | ⚠️ finalizar/reabrir/cancelar OS (ganchos), CMV | M |
| 09B | Frontend | Arquiteto no orçamento, tipo de fornecedor "Arquiteto / Designer", prazo do RT | ⚠️ cadastro de fornecedor | M |
| 10A | Backend | Separação sobre os itens da OS (retirar, devolver, concluir, leitor), disponível pelo Compras, faltas da OS | — | M |
| 10B | Frontend | Aba Separação (com leitor), faltas da OS, disponível na busca de insumo | ⚠️ abas da OS | M |
| 11A | Backend | Terceirizados: situação do móvel; com Compras, pedido `SERVICO`; sem Compras, marcação manual | — | M |
| 11B | Frontend | Seção na Separação, aba "Terceirizados" em Serviços | ⚠️ tela de Serviços | M |
| 12A | Backend | Etapas por móvel, lotes, sugestão de status, quadro de produção | — | M |
| 12B | Frontend | Aba Produção, pergunta de status, aba "Produção" em Serviços | ⚠️ abas da OS e de Serviços, contexto do modal de OS | M |
| 13A | Backend | Entrega por ambiente, pendências, fotos, agendamentos (preenche `data_instalacao` para o Compras) | — | M |
| 13B | Frontend | Aba Entrega, Termo A4, aba "Instalações", aviso na finalização | ⚠️ abas, finalização de OS | M |
| 14 | Frontend | Etiquetas por volume sobre o motor `shared/etiquetas` (campos do móvel + modelo pronto) | ⚠️ `shared/etiquetas` (só acréscimo) | P |

---

## 3. Ordem de implementação

A ordem respeita as dependências declaradas em cada spec. As linhas do mesmo marco podem andar em paralelo quando não dependem uma da outra.

### Marco 1 — Fundação (nada da marcenaria aparece ainda para o cliente)

```
00 ─┬─ 01A ── 01B
    ├─ 02                      (independente; pode andar em paralelo com tudo)
    └─ 01A ── 03A ── 03B       (03A/03B aposentam a fábrica ANTES de qualquer código novo)
              03A ── 04A ─┬─ 04B
                          └─ 05
```

**Pronto quando:** as 3 lojas em produção passam pela prova de não regressão das specs ⚠️ (01A, 01B, 02, 03A, 03B, 04A, 04B), nenhuma OS nova entra no trilho da fábrica, e o motor (05) reproduz os cenários A, B e C da Spec 05 centavo a centavo.

### Marco 2 — Comercial (a marcenaria vende e gera OS)

```
04A + 05 ── 06A ── 06B ── 07
                    └──── 08A (+ 03A) ── 08B
                          08A ── 09A ── 09B
```

**Pronto quando:** um orçamento real é montado, enviado com a proposta, aprovado em parte, vira OS com os móveis e as peças embutidas do motor, e o RT vira conta a pagar na finalização.

### Marco 3 — Fábrica

```
08A + 09A ── 10A ── 10B
08A + 09A ── 11A ── 11B (+ 10B)
08A + 11A ── 12A ── 12B (+ 11B)
```

**Pronto quando:** a OS do marco 2 é separada com o leitor, os terceirizados são pedidos e conferidos, as etapas são marcadas e a OS chega a "Aguardando Entrega" pela pergunta do sistema.

> Com F2b, o material entra no resultado do mês mesmo **sem** a 10A: a finalização da OS baixa as peças embutidas (regra de hoje). A 10A continua necessária para o piloto (a fábrica separa antes de produzir, e o orçado × real só existe com ela), mas a falta dela não infla mais o lucro do mês.

### Marco 4 — Obra

```
08A + 12A ── 13A ── 13B (+ 07, 12B)
12B + 13A ── 14
```

**Pronto quando:** a obra é agendada, os termos são impressos e registrados, as pendências acompanhadas, as etiquetas impressas e a OS finalizada.

### Marco 5 — Piloto

O roteiro manual de cada spec B, em sequência, com **um projeto real** da fábrica piloto (critério de pronto da SPEC-00).

### Andamento

**Marco 1 concluído em 09/10/2026** (01A, 01B, 02, 03A, 03B, 04A, 04B, 05): backend 2.350 passando e 1 pulado; frontend 304 testes e `vue-tsc` sem erros. Pendentes antes de seguir para a loja: os roteiros manuais (olho na tela) das specs B e o `npm run build:sidecar`.

**Marco 2 concluído em 09/10/2026** (06A, 06B, 07, 08A, 08B, 09A, 09B): backend 2.516 passando e 1 pulado; frontend 446 testes e `vue-tsc` sem erros. Pendentes antes da loja: os roteiros manuais das specs 06B, 07, 08B e 09B e o `npm run build:sidecar`.

**Marco 3 concluído em 09/10/2026** (10A, 10B, 11A, 11B, 12A, 12B): backend 2.610 passando e 1 pulado; frontend 540 testes e `vue-tsc` sem erros. Pendentes antes da loja: os roteiros manuais das specs 10B, 11B e 12B (no computador da fábrica, com leitor de código) e o `npm run build:sidecar` (o backend mudou nas 10A, 11A e 12A).

**Marco 4 concluído em 09/10/2026** (13A, 13B, 14): backend 2.648 passando e 1 pulado; frontend 582 testes e `vue-tsc` sem erros. Pendentes antes da loja: os roteiros manuais das specs 13B e 14 (impressão do termo, da lista do dia e das etiquetas no papel de verdade) e o `npm run build:sidecar` (o backend mudou na 13A).

Uma linha por spec entregue, com a suíte medida depois dela (referência de 08/10: backend 2.334 passando e 1 pulado; frontend 188 testes e `vue-tsc` sem erros). Sidecar: `npm run build:sidecar` antes do próximo instalador.

| Spec | Data | Commit | Testes | Suíte depois |
|------|------|--------|--------|--------------|
| 01A | 09/10/2026 | `5540bfd` | +13 | 2.347 passando, 1 pulado |
| 03A | 09/10/2026 | `00b71e4` | +30; −50 (D17); −1 (Reforma); −39 casos por campo do registry (campos que saíram) | 2.287 passando, 1 pulado |
| 01B | 09/10/2026 | `c5e89cc` | +28 (vitest) | frontend: 216 testes, `vue-tsc` sem erros |
| 02 | 09/10/2026 | `efa4fb9` | +21 (vitest) | frontend: 237 testes, `vue-tsc` sem erros |
| 03B | 09/10/2026 | `15dbc0f` | +33; −3 (`cargos.spec.ts`, D15) | frontend: 267 testes, `vue-tsc` sem erros |
| 04A | 09/10/2026 | `ea86a32` | +28 | 2.315 passando, 1 pulado |
| 04B | 09/10/2026 | `e9f7287` | +37 (vitest) | frontend: 304 testes, `vue-tsc` sem erros |
| 05 | 09/10/2026 | `b98901f` | +35 (cenários A, B e C centavo a centavo; 500 orçamentos aleatórios) | 2.350 passando, 1 pulado |
| 06A | 09/10/2026 | `5fada11` | +76 (23 de serviço, 50 de API, 3 da migração; cenário B pelo banco centavo a centavo) | 2.426 passando, 1 pulado |
| 08A | 09/10/2026 | `0a88ba0` | +56 (39 de API, 10 de serviço com 200 aprovações aleatórias, 4 da migração, 3 de não regressão da OS) | 2.482 passando, 1 pulado |
| 09A | 09/10/2026 | `7c32baf` | +30 (19 do RT, 5 dos ganchos da OS, 2 do CMV, 4 da migração) | 2.512 passando, 1 pulado |
| 06B | 09/10/2026 | `d8ab396` | +64 (vitest: 53 do orçamento — schemas contra JSON reais da API, fila, salvamento, editor pela rota —, 3 do menu, 4 dos atalhos, 4 de cargos) | frontend: 368 testes, `vue-tsc` sem erros |
| 07 | 09/10/2026 | `9dfa4eb` | +16 (vitest: dados, nome do PDF, documento A4 e o fluxo enviar → imprimir) | frontend: 384 testes, `vue-tsc` sem erros, `check:print-bw` ok |
| 08B | 09/10/2026 | `a30db21` | +30 (vitest: 20 da aprovação — modal, desfazer com PIN, faixa, proposta aprovada, aba da OS —, 10 de não regressão das abas e do cadeado da OS) | frontend: 414 testes, `vue-tsc` sem erros |
| 09B | 09/10/2026 | `01f4fa6` | +32 vitest (21 do arquiteto no orçamento — bloco, salvamento do %, corrida com a troca, painel, faixa, modal de envio —, 9 do cadastro de fornecedor, 2 do prazo do RT); +4 pytest (rota `GET /arquitetos`) | frontend: 446 testes, `vue-tsc` sem erros; backend: 2.516 passando, 1 pulado |
| 10A | 09/10/2026 | `cc073be` | +40 (30 de API, 7 de serviço com a finalização e o CMV, 3 do leitor) | 2.556 passando, 1 pulado |
| 11A | 09/10/2026 | `861f99e` | +26 (22 de API, com e sem o Compras; 4 da migração) | suítes vizinhas (marcenaria, Compras, fábrica, OS, migrações): 563 passando; a suíte inteira é medida com a 12A |
| 12A | 09/10/2026 | `de41026` | +28 (25 de API, 3 da migração) | 2.610 passando, 1 pulado (com a 11A) |
| 10B | 09/10/2026 | `28965b1` | +20 (vitest: schemas contra JSON reais da 10A, leitor, aba, modais, faltas, impressão, disponível na busca) | frontend: 466 testes, `vue-tsc` sem erros, `check:print-bw` ok |
| 11B | 09/10/2026 | `597f441` | +39 (vitest: 33 dos terceirizados — schemas contra JSON reais da 11A, regras da barra, seção com e sem o Compras, modais, aba em Serviços —, 2 da seção na Separação, 3 das abas de Serviços por segmento, 1 do botão do topo) | frontend: 505 testes, `vue-tsc` sem erros, `check:print-bw` ok |
| 12B | 09/10/2026 | `39d84c6` | +35 (vitest: 24 da produção — schemas contra JSON reais da 12A, chips, lote, otimista e desfazer, pergunta de status, Feito por, editar etapas, seleção, quadro —, 3 do status sem perder o formulário e da aba inicial, 3 do editor de listas, 3 das abas da OS, 1 da aba em Serviços, 1 da pergunta na Separação) | frontend: 540 testes, `vue-tsc` sem erros, `check:print-bw` ok |
| 13A | 09/10/2026 | `aa19e71` | +38 (35 de API — registro, correção, pendências, fotos na galeria, agenda, data de instalação no Compras, desfazer, lista de instalações —, 3 da migração) | 2.648 passando, 1 pulado |
| 13B | 09/10/2026 | `cea7cde` | +27 (vitest: 25 da entrega — schemas contra JSON reais da 13A, regras de tela, aba, agendar, registrar com fotos antes, pergunta sem foto, "Finalizar a OS agora?", termo A4, aviso da finalização, aba Instalações —, 2 das abas da OS e de Serviços) | frontend: 567 testes, `vue-tsc` sem erros, `check:print-bw` ok |
| 14 | 09/10/2026 | `c290fc2` | +15 (vitest: 7 do motor — layout do móvel, modelos prontos, chaves dos modelos de antes congeladas, térmica direta —, 6 do modal e da montagem dos volumes, 2 da aba Produção) | frontend: 582 testes, `vue-tsc` sem erros, `check:print-bw` ok |

---

## 4. Banco de dados

### 4.1. Migrações (cadeia, R15-MIG)

Antes de cada uma, `alembic heads`: se outra branch tiver acrescentado migração, o `down_revision` acompanha.

| Ordem | Revisão | Filha de | Spec | O que faz |
|-------|---------|----------|------|-----------|
| 1 | `608dc99a8616` | `d7a3e9c2f418` (head de 08/10) | 04A | Tabela `configuracoes_marcenaria` (a coluna `produtos.sofre_perda` já existe) |
| 2 | `683ff38df873` | `608dc99a8616` | 06A | Tabelas do orçamento (orçamento, RT, ambientes, móveis, insumos, anexos, eventos) |
| 3 | `971eb6cc5a33` | `683ff38df873` | 08A | ⚠️ `ordem_servico_itens.origem`; vínculos do orçamento aprovado |
| 4 | `195109da93f7` | `971eb6cc5a33` | 09A | Conta do RT na linha do arquiteto; prazo e categoria do RT na configuração |
| — | (nenhuma) | — | 10A | A separação usa `quantidade_separada` e `custo_real`, que já existem (E3b) |
| 5 | `642b2e8f79fa` | `195109da93f7` | 11A | Colunas do terceirizado no móvel (inclui `pedido_compra_id`) |
| 6 | `072437088f6c` | `642b2e8f79fa` | 12A | `marcenaria_etapas` |
| 7 | `2c4df92b1412` | `072437088f6c` | 13A | Entregas, pendências, fotos da entrega, agendamentos |

Regras para todas (PR8): decidir pela presença do schema **antigo** (o `create_all()` do startup roda antes); `ADD COLUMN` só se a coluna faltar, sem `batch_alter_table` nas tabelas grandes; nunca renomear o arquivo do banco; nunca apagar as migrações da fábrica (FB1: estão na cadeia antes da fiscal `d7a3e9c2f418`).

### 4.2. Tabelas existentes alteradas

Só uma coluna nova em tabela existente, **nula**, sem mudar o comportamento das linhas que já existem:

| Tabela | Coluna | Spec | Decisão |
|--------|--------|------|---------|
| `ordem_servico_itens` | `origem` (nula) | 08A | F4a (exceção a F1) |

Colunas que **já existem** (vieram da fábrica) e passam a ser usadas: `produtos.sofre_perda` (04A, F6), `ordem_servico_itens.quantidade_separada` e `custo_real` (10A, E3b), `ordens_servico.data_instalacao` (13A, I5b). Todo o resto vive em tabelas `marcenaria_*` (F1). As tabelas `fabrica_*` e as colunas `fase_fabrica`, `compra_liberada_*`, `modo_fabrica`, `fabrica_travar_etapas`, `fabrica_orcamento_id`, `fabrica_movel_id`, `unidade_consumo` e `consumo_por_unidade` ficam como estão, sem uso (FB1).

---

## 5. Onde mexemos no que já funciona (⚠️ PR1)

Toda spec ⚠️ tem uma seção "Prova de não regressão". Juntas, elas tocam:

| Área do sistema | Specs | O que muda para os outros segmentos |
|-----------------|-------|-------------------------------------|
| Registry de segmentos e dashboard | 01A | Nada (rótulos novos são opcionais) |
| Lista, filtros e resumo de OS | 01B | **Serigrafia:** o desfecho passa a mostrar os textos dela (exceção aprovada, Revisão 2) |
| Cadastro de cliente | 02 | **Ganha** erro "sem internet" × "não encontrado", tempo limite e aviso de duplicidade (melhoria para todos) |
| Criação, edição e cancelamento de OS | 03A, 08A | Nada: travas genéricas que não se aplicam a eles; o "devolver a separação ao cancelar" da fábrica passa a exigir `fase_fabrica` (nenhuma OS deles tem separação) |
| Configurações › OS, cargos, produto (telas da fábrica) | 03B | Nada: as telas da fábrica só apareciam na marcenaria |
| Tela de OS e menu rápido | 03B, 06B | Nada (os botões só mudam onde não há tipo criável) |
| Produto, configurações, cargos | 04A, 04B, 06B | Nada (tudo por capacidade ou pela linha `segmento`; nível de acesso dos cargos idêntico) |
| Itens da OS | 08A, 08B | Nada (`origem` nula em todos os itens deles; a trava estende a que já existe para a fábrica) |
| Finalizar, reabrir, cancelar OS | 09A, 13B | Nada (ganchos vazios para eles; aviso só por capacidade) |
| CMV (resultado do mês) | 09A | Nada (nenhum item deles tem `origem`) — conferir no banco de cada loja |
| Cadastro de fornecedor | 09B | Nada (tipo novo só por capacidade) |
| Abas do modal de OS e da tela de Serviços | 08B, 10B, 11B, 12B, 13B | Nada (abas por capacidade, como a de Revisões da oficina) |
| Motor de etiquetas | 14 | Nada: campos e modelo **acrescentados**; os modelos de produto e de envio não mudam |

**Não mexemos** no módulo Compras (FB2): ele passa a enxergar o material da marcenaria porque os insumos são itens de produto da OS, o mesmo dado que ele já lê.

**Teste obrigatório antes de qualquer instalador:** aplicar todas as migrações num **banco copiado** de cada uma das 3 lojas em produção e conferir: nenhuma linha muda; CMV e comissão do mês atual e dos três anteriores idênticos; telas de OS, Produtos, Serviços, Cargos e Configurações iguais (snapshots).

---

## 6. Peças novas que outras partes do sistema podem reaproveitar

| Peça | Spec | Para que serve além da marcenaria |
|------|------|-----------------------------------|
| Capacidade `orcamento_tecnico` | 04A | Qualquer segmento futuro com orçamento técnico liga tudo com uma linha no registry |
| Rótulos de status por segmento | 01A | Cada segmento pode chamar os status da OS do seu jeito |
| Coluna `origem` + trava de item | 08A | Qualquer documento que gere itens de OS |
| Ganchos de finalizar/reabrir/cancelar OS | 09A | Qualquer módulo que reaja ao ciclo da OS sem o serviço da OS conhecê-lo |
| `ListaTextosEditavel` | 04B → 12B | Qualquer lista curta de textos editável |
| `openExistingOS(os, { abaInicial })` | 12B | Abrir a OS direto numa aba |
| Campos de móvel no motor de etiquetas | 14 | Qualquer etiqueta de volume de OS |

---

## 7. Permissões e cargos

| Chave | Spec | Libera |
|-------|------|--------|
| `view_custos_marcenaria` / `manage_custos_marcenaria` | 04A | Ver custos, margens e RT; alterar os parâmetros |
| `view_` / `manage_` / `delete_orcamentos_marcenaria` | 06A | Ver, montar/enviar/aprovar, excluir orçamentos |
| `servico` (de hoje) | 10A–13A | Separação, terceirizados, produção, entrega (são abas da OS) |
| Permissões do **Compras** (de hoje) | 10A, 11A | Necessidades, pedidos e recebimento (módulo COMPRAS) |
| `view_fabrica` / `manage_fabrica` | — | **Aposentadas** (FB1): a linha "Fábrica" some dos cargos; as chaves gravadas não liberam mais nada |

As linhas novas da matriz de cargos usam `segmento: 'marcenaria'`: só aparecem na marcenaria e ficam fora do nível de acesso dos outros segmentos (mecanismo que a matriz já tem). Sugestão de cargos para o piloto: **Dono** (tudo), **Vendedor** (orçamentos sem custos), **Fábrica** (OS), **Financeiro** (OS + financeiro + custos), **Compras** (se o módulo for contratado).

---

## 8. Pendências e pontos em aberto

### 8.1. Pendências do sistema (afetam todos os segmentos; spec própria)

| ID | Título | Gravidade | Onde |
|----|--------|-----------|------|
| PEND-001 | CNPJ alfanumérico não é aceito em nenhum cadastro (Receita, desde 07/2026) | Alta | `pendencias-sistema.md` |
| PEND-002 | Comissão da OS ignora o desconto da OS | Média | `pendencias-sistema.md` |
| PEND-003 | Conta do recebimento de Compras nasce sem categoria e o material sai do lucro duas vezes | Média | `pendencias-sistema.md` |

### 8.2. Decisões da SPEC-00

Nenhuma decisão em aberto: as que estavam 🟡 (C3a, C5c, C8, I1, I2, I3, I6, F2b, E5a, E6b) foram aprovadas na Revisão 16 (08/10/2026).

### 8.3. Observações registradas nas specs, sem pendência aberta

| Assunto | Spec | Situação |
|---------|------|----------|
| Número da OS sem nova tentativa quando dois computadores criam ao mesmo tempo | 06A §8, 08A §9 | Existe hoje em todas as lojas; o orçamento já trata o seu número |
| Adiantamento (sinal) da OS não entra no fechamento de caixa | 08A §9 | Lacuna de hoje, comentada no código; a marcenaria herda |
| Material de OS cancelada sai do estoque e não aparece como perda no resultado | 10A §8 | Regra de hoje (CMV só de OS finalizada). Registrar como pendência se o dono quiser essa perda no resultado |
| Código da fábrica aposentada continua no repositório | SPEC-00 FB1 | Inerte; sai numa limpeza depois do piloto (tabelas ficam) |
| Licença do PyArmor em modo *trial* | CLAUDE.md | Revisar antes de um release comercial |

---

## 9. Antes do piloto (checklist)

**Técnico**
- [ ] Marcos 1 a 4 completos, com todas as provas de não regressão.
- [ ] Suíte de referência comparada a cada spec: em 08/10/2026 (`53e5d81`), backend **2.334 passando, 1 pulado**; frontend **188 testes**, `vue-tsc` sem erros. Toda saída de teste fica escrita na spec que a fez (ex.: 03A D17, 03B D15).
- [ ] Testes de API com `TestClient(app)` **sem** `with` (padrão de `test/api/v1/compras` e `fabrica`): com `with`, o lifespan roda `create_all()` e as migrações no banco real da máquina.
- [ ] Teste de migração nos bancos copiados das 3 lojas (§5).
- [ ] `npm run build:sidecar` e medida do teto do PyArmor com todo o backend novo (PR7).
- [ ] Instalador testado sobre um banco existente (atualização, não instalação nova).

**Na fábrica piloto**
- [x] A fábrica piloto **tem o módulo Compras** (Revisão 16): o piloto usa as Necessidades e o pedido de serviço à central. Conferir na licença dela que o módulo COMPRAS está liberado e que os cargos têm a linha Compras.
- [ ] Configurações › Marcenaria: markup, perda, **custo/hora** (padrão R$ 0,00), **RT padrão** (padrão 0%), modo do RT, prazo do RT, validade, prazo de entrega, etapas e checklist.
- [ ] Produtos: chapas e fitas com **"Sofre perda"** marcado; localização no estoque preenchida (ordena a separação); código de barras nos produtos (ou nas embalagens) que serão lidos; último preço de compra (ou custo médio) em todos os insumos.
- [ ] Fornecedores: centrais parceiras e arquitetos (tipo "Arquiteto / Designer", com PIX).
- [ ] Cargos e usuários (§7); funcionários montadores cadastrados.
- [ ] Leitor de código de barras configurado para mandar **Enter** no fim.
- [ ] Etiquetas: escolher o modelo (folha A4 ou térmica) e calibrar com o **"Imprimir teste"** do motor de etiquetas.
- [ ] Impressora A4 testada com a proposta e o termo; "Salvar como PDF" disponível no diálogo.

**Roteiro do piloto (um projeto real)**
1. Cliente PJ com consulta de CNPJ; arquiteto indicador.
2. Orçamento de 2 ou 3 ambientes, com um móvel terceirizado e instalação; desconto; proposta enviada.
3. Nova versão com ajuste do cliente; aprovação parcial; sinal registrado.
4. Separação com leitor; Necessidades do Compras com a chapa que falta; terceirizado pedido à central pelo Compras, recebido (com a conta) e conferido.
5. Etapas marcadas; etiquetas; status pela pergunta do sistema.
6. Agendamento; termos; entrega com uma ressalva; pendência resolvida.
7. Finalização com pagamento; conta do RT criada; resultado do mês conferido à mão (material, RT, terceirizado uma vez cada; ver PEND-003 se a chapa foi comprada pelo Compras).

---

## 10. Índice dos documentos

| Arquivo | Conteúdo |
|---------|----------|
| `SPEC-00-DECISOES-MARCENARIA.md` | Princípios, glossário, todas as decisões e revisões |
| `SPEC-01A` / `SPEC-01B` | Rótulos de status |
| `SPEC-02` | CNPJ no cliente (o que falta) |
| `SPEC-03A` / `SPEC-03B` | Ajuste do segmento e aposentadoria da fábrica |
| `SPEC-04A` / `SPEC-04B` | Base: perda, parâmetros, permissões |
| `SPEC-05` | Motor de cálculo |
| `SPEC-06A` / `SPEC-06B` | Orçamento |
| `SPEC-07` | Proposta |
| `SPEC-08A` / `SPEC-08B` | Aprovação → OS |
| `SPEC-09A` / `SPEC-09B` | RT do arquiteto e resultado do mês |
| `SPEC-10A` / `SPEC-10B` | Separação e disponível |
| `SPEC-11A` / `SPEC-11B` | Terceirizados |
| `SPEC-12A` / `SPEC-12B` | Produção |
| `SPEC-13A` / `SPEC-13B` | Entrega e instalação |
| `SPEC-14` | Etiquetas |
| `../pendencias-sistema.md` | PEND-001, PEND-002, PEND-003 |
| `../segmento-marcenaria-plano.md` | Plano antigo (16/09), substituído pela SPEC-00 |
| `../marcenaria-fabrica-plano.md` | Plano da fábrica (04–06/10), aposentado pela Revisão 15 (histórico) |
