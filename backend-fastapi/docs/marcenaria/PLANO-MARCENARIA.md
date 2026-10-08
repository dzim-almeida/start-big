# Plano Completo — Segmento Marcenaria (Fase 1)

| Campo      | Valor                                                                             |
|------------|-----------------------------------------------------------------------------------|
| Status     | Specs escritas — aguardando implementação                                         |
| Data       | 08/10/2026                                                                        |
| Branch     | `feat/segmento-marcenaria`                                                        |
| Documentos | `SPEC-00` (decisões) + 24 specs de implementação nesta pasta + `docs/pendencias-sistema.md` |

Este documento junta as 25 specs num só plano: o que a fase 1 entrega, em que ordem construir, onde mexemos no código das lojas em produção, o que ficou pendente e o que conferir antes do piloto. Ele **não** substitui as specs: cada linha aponta para a spec que tem os detalhes. Quando uma spec e este plano discordarem, vale a spec (e este plano deve ser corrigido).

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
| 5 | Aprova (todo ou em parte), diz se o sinal foi pago, e o sistema cria a OS | Vendedor | 08A, 08B |
| 6 | Separa o material do estoque (com leitor), vê o que falta e a lista de compras | Fábrica / compras | 10A, 10B |
| 7 | Pede os móveis terceirizados à central, recebe, confere, lança a conta | Fábrica / financeiro | 11A, 11B |
| 8 | Marca as etapas de produção de cada móvel; o status da OS acompanha (com pergunta) | Fábrica | 12A, 12B |
| 9 | Imprime as etiquetas dos volumes | Fábrica | 14 |
| 10 | Agenda a instalação, imprime o termo por ambiente, registra a entrega e as pendências | Atendimento / montador | 13A, 13B |
| 11 | Finaliza a OS (pagamentos de sempre); o RT do arquiteto vira conta a pagar | Atendimento | 09A |
| 12 | O resultado do mês mostra cada custo uma vez (material, RT, terceirizado, salários) | Dono | 09A (F2a) |

Fora da fase 1 (SPEC-00 §7): Reforma de móveis (referência guardada em §7.1), importação 3D e plano de corte, vários arquitetos na tela, pedido de compra, agenda em calendário, cobrança por ambiente, versão celular/tablet.

---

## 2. As 25 specs

Tamanho é uma **estimativa relativa** de esforço (P = pequeno, M = médio, G = grande), para planejar a sequência; não é prazo.

| Spec | Camada | O que entrega | ⚠️ Mexe em código compartilhado | Tamanho |
|------|--------|---------------|-------------------------------|---------|
| 00 | Documento | Registro de todas as decisões (com 14 revisões) | — | — |
| 01A | Backend | Rótulos de status por segmento no registry ("Em Produção", "Aguardando Material", "Aguardando Entrega") | ⚠️ registry, dashboard | P |
| 01B | Frontend | Rótulos nas telas, filtros e dashboard; correção do rótulo de desfecho (exceção ao PR1 aprovada) | ⚠️ lista de OS, resumo, filtros, dashboard | M |
| 02 | Frontend | Consulta de CNPJ no cadastro de cliente | ⚠️ cadastro de cliente (todos os segmentos ganham) | P |
| 03A | Backend | Marcenaria só com "Móveis planejados"; OS só nasce de orçamento | ⚠️ criação/edição de OS (trava genérica) | P |
| 03B | Frontend | Botões "Criar OS" somem onde não há tipo criável; tipo travado; textos | ⚠️ tela de OS, menu rápido | P |
| 04A | Backend | `produto.sofre_perda`, parâmetros da marcenaria, permissões de custo, capacidade `orcamento_tecnico` | ⚠️ tabela de produtos (coluna nova) | M |
| 04B | Frontend | Caixa "Sofre perda" no produto, Configurações › Marcenaria, linha de custos nos cargos (nível de acesso intacto) | ⚠️ produto, configurações, cargos | M |
| 05 | Backend | Motor de cálculo (funções puras, centavos e basis points, sem `float`) | — | M |
| 06A | Backend | Orçamento: tabelas, ciclo de vida, versões, trava de edição, anexos, histórico (3 revisões) | — | G |
| 06B | Frontend | Lista, editor em página inteira, salvamento automático, modal do móvel, cadastro rápido de insumo, menu e atalhos | ⚠️ menu, menu rápido, tela de OS, cargos | G |
| 07 | Frontend | Proposta comercial A4 ("Salvar como PDF") | — | M |
| 08A | Backend | Aprovação → OS (parcial), sinal recebido ou combinado, trava de itens, desfazer (1 revisão) | ⚠️ coluna `origem` nos itens de OS e trava | G |
| 08B | Frontend | Modal de aprovação, orçamento aprovado, aba "Orçamento" e cadeado nos itens da OS | ⚠️ abas e itens do modal de OS | M |
| 09A | Backend | RT do arquiteto como conta a pagar na finalização; ganchos da OS; CMV sem dupla contagem (1 revisão) | ⚠️ finalizar/reabrir/cancelar OS (ganchos), CMV | M |
| 09B | Frontend | Arquiteto no orçamento, tipo de fornecedor "Arquiteto / Designer", prazo do RT | ⚠️ cadastro de fornecedor | M |
| 10A | Backend | Separação por produto, reserva calculada, baixa, devolução, leitor, lista de compras | — | G |
| 10B | Frontend | Aba Separação (com leitor), lista de compras em Produtos, disponível na busca de insumo | ⚠️ abas da OS, tela de Produtos | M |
| 11A | Backend | Terceirizados: A pedir → Enviado → Recebido → Conferido, conta da central | — | M |
| 11B | Frontend | Seção na Separação, aba "Terceirizados" em Serviços | ⚠️ tela de Serviços | M |
| 12A | Backend | Etapas por móvel, lotes, sugestão de status, quadro de produção | — | M |
| 12B | Frontend | Aba Produção, pergunta de status, aba "Produção" em Serviços | ⚠️ abas da OS e de Serviços, contexto do modal de OS | M |
| 13A | Backend | Entrega por ambiente, pendências, fotos, agendamentos | — | M |
| 13B | Frontend | Aba Entrega, Termo A4, aba "Instalações", aviso na finalização | ⚠️ abas, finalização de OS | M |
| 14 | Frontend | Etiquetas por volume (A4 comum, adesiva, térmica) | — | P |

---

## 3. Ordem de implementação

A ordem respeita as dependências declaradas em cada spec. As linhas do mesmo marco podem andar em paralelo quando não dependem uma da outra.

### Marco 1 — Fundação (nada da marcenaria aparece ainda para o cliente)

```
00 ─┬─ 01A ── 01B
    ├─ 02                      (independente; pode andar em paralelo com tudo)
    └─ 01A ── 03A ── 03B
              03A ── 04A ─┬─ 04B
                          └─ 05
```

**Pronto quando:** as 3 lojas em produção passam pela prova de não regressão das specs ⚠️ (01A, 01B, 02, 03A, 03B, 04A, 04B) e o motor (05) reproduz os cenários A, B e C da Spec 05 centavo a centavo.

### Marco 2 — Comercial (a marcenaria vende e gera OS)

```
04A + 05 ── 06A ── 06B ── 07
                    └──── 08A (+ 03A) ── 08B
                          08A ── 09A ── 09B
```

**Pronto quando:** um orçamento real é montado, enviado com a proposta, aprovado em parte, vira OS com os valores do motor, e o RT vira conta a pagar na finalização.

### Marco 3 — Fábrica

```
08A + 09A ── 10A ── 10B
08A + 09A ── 11A ── 11B (+ 10B)
08A + 11A ── 12A ── 12B (+ 11B)
```

**Pronto quando:** a OS do marco 2 é separada com o leitor, os terceirizados são pedidos e conferidos, as etapas são marcadas e a OS chega a "Aguardando Entrega" pela pergunta do sistema.

> ⚠️ **10A antes do piloto, sem exceção.** A decisão F2a (09A) tira do resultado do mês o custo declarado nos itens da marcenaria; o material só volta ao resultado pela baixa de estoque da 10A. Um piloto sem a 10A teria o lucro do mês inflado pelo material.

### Marco 4 — Obra

```
08A + 12A ── 13A ── 13B (+ 07, 12B)
12B + 13A ── 14
```

**Pronto quando:** a obra é agendada, os termos são impressos e registrados, as pendências acompanhadas, as etiquetas impressas e a OS finalizada.

### Marco 5 — Piloto

O roteiro manual de cada spec B, em sequência, com **um projeto real** da fábrica piloto (critério de pronto da SPEC-00).

---

## 4. Banco de dados

### 4.1. Migrações (cadeia)

| Ordem | Revisão | Spec | O que faz |
|-------|---------|------|-----------|
| 1 | `y8z9a0b1c2d3` (filha de `x7y8z9a0b1c2`) | 04A | `produtos.sofre_perda`; tabela `configuracoes_marcenaria` |
| 2 | `z9a0b1c2d3e4` | 06A | Tabelas do orçamento (orçamento, RT, ambientes, móveis, insumos, anexos, eventos) |
| 3 | `a0b1c2d3e4f5` | 08A | ⚠️ `ordem_servico_itens.origem`; vínculos do orçamento aprovado |
| 4 | `b1c2d3e4f5a6` | 09A | Conta do RT na linha do arquiteto; prazo e categoria do RT na configuração |
| 5 | `c2d3e4f5a6b7` | 10A | `marcenaria_separacao` |
| 6 | `d3e4f5a6b7c8` | 11A | Colunas do terceirizado no móvel; categoria da produção terceirizada |
| 7 | `e4f5a6b7c8d9` | 12A | `marcenaria_etapas` |
| 8 | `f5a6b7c8d9e0` | 13A | Entregas, pendências, fotos da entrega, agendamentos |

Regras para todas (PR8): decidir pela presença do schema **antigo** (o `create_all()` do startup roda antes); `ADD COLUMN` só se a coluna faltar, sem `batch_alter_table` nas tabelas grandes; nunca renomear o arquivo do banco.

### 4.2. Tabelas existentes alteradas

Só duas, as duas com coluna **nula ou com padrão**, sem mudar o comportamento das linhas que já existem:

| Tabela | Coluna | Spec | Decisão |
|--------|--------|------|---------|
| `produtos` | `sofre_perda` (padrão `false`) | 04A | F6 |
| `ordem_servico_itens` | `origem` (nula) | 08A | F4a (exceção a F1) |

Todo o resto vive em tabelas `marcenaria_*` (F1).

---

## 5. Onde mexemos no que já funciona (⚠️ PR1)

Toda spec ⚠️ tem uma seção "Prova de não regressão". Juntas, elas tocam:

| Área do sistema | Specs | O que muda para os outros segmentos |
|-----------------|-------|-------------------------------------|
| Registry de segmentos e dashboard | 01A | Nada (rótulos novos são opcionais) |
| Lista, filtros e resumo de OS | 01B | **Serigrafia:** o desfecho passa a mostrar os textos dela (exceção aprovada, Revisão 2) |
| Cadastro de cliente | 02 | **Ganha** a consulta de CNPJ (melhoria para todos) |
| Criação e edição de OS | 03A, 08A | Nada (travas genéricas que não se aplicam a eles) |
| Tela de OS e menu rápido | 03B, 06B | Nada (os botões só mudam onde não há tipo criável) |
| Produto, configurações, cargos | 04B, 06B | Nada (tudo por capacidade; nível de acesso dos cargos idêntico) |
| Itens da OS | 08A, 08B | Nada (`origem` nula em todos os itens deles) |
| Finalizar, reabrir, cancelar OS | 09A, 13B | Nada (ganchos vazios para eles; aviso só por capacidade) |
| CMV (resultado do mês) | 09A | Nada (nenhum item deles tem `origem`) — conferir no banco de cada loja |
| Cadastro de fornecedor | 09B | Nada (tipo novo só por capacidade) |
| Abas do modal de OS e da tela de Serviços | 08B, 10B, 11B, 12B, 13B | Nada (abas por capacidade, como a de Revisões da oficina) |
| Tela de Produtos | 10B | Nada (aba por capacidade) |

**Teste obrigatório antes de qualquer instalador:** aplicar todas as migrações num **banco copiado** de cada uma das 3 lojas em produção e conferir: nenhuma linha muda; CMV e comissão do mês atual e dos três anteriores idênticos; telas de OS, Produtos, Serviços, Cargos e Configurações iguais (snapshots).

---

## 6. Peças novas que outras partes do sistema podem reaproveitar

| Peça | Spec | Para que serve além da marcenaria |
|------|------|-----------------------------------|
| Capacidade `orcamento_tecnico` | 04A | Qualquer segmento futuro com orçamento técnico liga tudo com uma linha no registry |
| Rótulos de status por segmento | 01A | Cada segmento pode chamar os status da OS do seu jeito |
| Coluna `origem` + trava de item | 08A | Qualquer documento que gere itens de OS |
| Ganchos de finalizar/reabrir/cancelar OS | 09A | Qualquer módulo que reaja ao ciclo da OS sem o serviço da OS conhecê-lo |
| Consulta de CNPJ compartilhada | 02 | Cliente, empresa e fornecedor |
| `ListaTextosEditavel` | 04B → 12B | Qualquer lista curta de textos editável |
| `openExistingOS(os, { abaInicial })` | 12B | Abrir a OS direto numa aba |

---

## 7. Permissões e cargos

| Chave | Spec | Libera |
|-------|------|--------|
| `view_custos_marcenaria` / `manage_custos_marcenaria` | 04A | Ver custos, margens e RT; alterar os parâmetros |
| `view_` / `manage_` / `delete_orcamentos_marcenaria` | 06A | Ver, montar/enviar/aprovar, excluir orçamentos |
| `servico` (de hoje) | 10A–13A | Separação, terceirizados, produção, entrega (são abas da OS) |
| `produto` (de hoje) | 10A | Lista de compras |
| `manage_financeiro` + módulo Financeiro (de hoje) | 11A | Lançar a conta da central |

As linhas novas da matriz de cargos só aparecem e só contam no nível de acesso onde o segmento tem a capacidade (04B D17). Sugestão de cargos para o piloto: **Dono** (tudo), **Vendedor** (orçamentos sem custos), **Fábrica** (OS), **Financeiro** (OS + financeiro + custos).

---

## 8. Pendências e pontos em aberto

### 8.1. Pendências do sistema (afetam todos os segmentos; spec própria)

| ID | Título | Gravidade | Onde |
|----|--------|-----------|------|
| PEND-001 | CNPJ alfanumérico não é aceito em nenhum cadastro (Receita, desde 07/2026) | Alta | `pendencias-sistema.md` |
| PEND-002 | Comissão da OS ignora o desconto da OS | Média | `pendencias-sistema.md` |

### 8.2. Decisões ainda marcadas 🟡 na SPEC-00

Já implementadas nas specs com o texto proposto; precisam do "ok" explícito:

| Código | Decisão | Usada em |
|--------|---------|----------|
| C3a | O markup incide sobre a instalação | 05 |
| I1 | Montador não usa o sistema na obra; termo A4 por ambiente, registrado na fábrica com foto | 13A, 13B |
| I2 | Checklist padrão copiado para cada ambiente e editável | 13A |
| I3 | Pendência aberta avisa na finalização, mas não trava | 13A, 13B |
| I6 | Termo por ambiente; a OS finaliza uma vez; sem cobrança por ambiente | 13A |

### 8.3. Observações registradas nas specs, sem pendência aberta

| Assunto | Spec | Situação |
|---------|------|----------|
| Número da OS sem nova tentativa quando dois computadores criam ao mesmo tempo | 06A §8, 08A §9 | Existe hoje em todas as lojas; o orçamento já trata o seu número |
| Adiantamento (sinal) da OS não entra no fechamento de caixa | 08A §9 | Lacuna de hoje, comentada no código; a marcenaria herda |
| Material de OS cancelada sai do estoque e não aparece como perda no resultado | 10A §8 | Regra de hoje (CMV só de OS finalizada). Registrar como pendência se o dono quiser essa perda no resultado |
| Licença do PyArmor em modo *trial* | CLAUDE.md | Revisar antes de um release comercial |

---

## 9. Antes do piloto (checklist)

**Técnico**
- [ ] Marcos 1 a 4 completos, com todas as provas de não regressão.
- [ ] Teste de migração nos bancos copiados das 3 lojas (§5).
- [ ] Teste de desempenho da reserva (10A §7.5) dentro dos limites.
- [ ] `npm run build:sidecar` e medida do teto do PyArmor com todo o backend novo (PR7).
- [ ] Instalador testado sobre um banco existente (atualização, não instalação nova).

**Na fábrica piloto**
- [ ] Configurações › Marcenaria: markup, perda, **custo/hora** (padrão R$ 0,00), **RT padrão** (padrão 0%), modo do RT, prazo do RT, validade, prazo de entrega, etapas e checklist.
- [ ] Produtos: chapas e fitas com **"Sofre perda"** marcado; localização no estoque preenchida (ordena a separação); código de barras nos produtos que serão lidos; último preço de compra (ou custo médio) em todos os insumos.
- [ ] Fornecedores: centrais parceiras e arquitetos (tipo "Arquiteto / Designer", com PIX).
- [ ] Cargos e usuários (§7); funcionários montadores cadastrados.
- [ ] Leitor de código de barras configurado para mandar **Enter** no fim.
- [ ] Folha de etiqueta adesiva: conferir as medidas com a **página de teste** (14 D5).
- [ ] Impressora A4 testada com a proposta, o termo e as etiquetas; "Salvar como PDF" disponível no diálogo.

**Roteiro do piloto (um projeto real)**
1. Cliente PJ com consulta de CNPJ; arquiteto indicador.
2. Orçamento de 2 ou 3 ambientes, com um móvel terceirizado e instalação; desconto; proposta enviada.
3. Nova versão com ajuste do cliente; aprovação parcial; sinal registrado.
4. Separação com leitor; lista de compras; terceirizado pedido e conferido.
5. Etapas marcadas; etiquetas; status pela pergunta do sistema.
6. Agendamento; termos; entrega com uma ressalva; pendência resolvida.
7. Finalização com pagamento; conta do RT criada; resultado do mês conferido à mão (material, RT, terceirizado uma vez cada).

---

## 10. Índice dos documentos

| Arquivo | Conteúdo |
|---------|----------|
| `SPEC-00-DECISOES-MARCENARIA.md` | Princípios, glossário, todas as decisões e revisões |
| `SPEC-01A` / `SPEC-01B` | Rótulos de status |
| `SPEC-02` | CNPJ no cliente |
| `SPEC-03A` / `SPEC-03B` | Ajuste do segmento |
| `SPEC-04A` / `SPEC-04B` | Base: perda, parâmetros, permissões |
| `SPEC-05` | Motor de cálculo |
| `SPEC-06A` / `SPEC-06B` | Orçamento |
| `SPEC-07` | Proposta |
| `SPEC-08A` / `SPEC-08B` | Aprovação → OS |
| `SPEC-09A` / `SPEC-09B` | RT do arquiteto e resultado do mês |
| `SPEC-10A` / `SPEC-10B` | Separação, reserva, compras |
| `SPEC-11A` / `SPEC-11B` | Terceirizados |
| `SPEC-12A` / `SPEC-12B` | Produção |
| `SPEC-13A` / `SPEC-13B` | Entrega e instalação |
| `SPEC-14` | Etiquetas |
| `../pendencias-sistema.md` | PEND-001, PEND-002 |
| `../segmento-marcenaria-plano.md` | Plano antigo (16/09), substituído pela SPEC-00 |
