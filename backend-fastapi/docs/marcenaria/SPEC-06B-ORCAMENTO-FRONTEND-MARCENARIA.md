# Spec 06B — Orçamento de Marcenaria (Frontend): Lista, Editor e Móvel

| Campo        | Valor                                                                                     |
|--------------|-------------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                           |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado (menu, atalhos, tela de OS, cargos) |
| Dependências | Specs 02 (cliente), 03B (botões de OS), 04B (capacidade, permissões de custo), 06A (API)   |
| Bloqueia     | Specs 07 (proposta), 08B (aprovação), 09B (RT do arquiteto)                                |
| Referência   | SPEC-00: C4, C7, C8, C9, E0c, F5, O1, O1a, O2, O3, O3a, O5, O6, P4, T2, T3, T3a–T3g, T4, T4a, T4b, T5 · PR1, PR3, PR4, PR6 |

> **Revisão 1 (08/10/2026) — correções e convergência com a branch (SPEC-00 Revisão 15).** (1) O "≈" do desconto e do sinal (D18) lê `calculo.desconto_bp_efetivo` e `calculo.sinal_bp_efetivo` (Spec 05 Revisão 1, 06A Revisão 3) quando o modo é `VALOR`, e `calculo.desconto_centavos`/`sinal_centavos` quando é `PERCENTUAL`: nenhuma conta em TypeScript. (2) A linha "Orçamentos de Marcenaria" dos cargos usa `segmento: 'marcenaria'` (mecanismo existente; 04B Revisão 1), e não `capacidade`. (3) O prazo de entrega aceita de 1 a **365** dias, como a 04A (a versão anterior dizia 730). (4) O desenho do editor (§6.2) tinha um ambiente "Dormitório casal" que não fechava com o bruto; ficou só o cenário B da Spec 05 (Cozinha Gourmet + instalação = R$ 9.725,15).

---

## 1. Objetivo

Dar ao vendedor e ao dono da marcenaria as telas para **montar, enviar e acompanhar** orçamentos:

1. **Menu "Orçamentos"** com a lista, filtros e contadores.
2. **Editor em página inteira**: cliente e projeto, ambientes e móveis, instalação, medição (texto e anexos), condições (desconto, sinal, validade, prazo), resumo de valores e painel de custos.
3. **Modal do móvel**: medidas, insumos do cadastro de produtos, mão de obra, produção interna ou terceirizada, com o preço calculado enquanto o usuário digita.
4. **Ciclo de vida**: enviar, voltar a editar, recusar, renovar, nova versão, atualizar preços, excluir, histórico.
5. **Salvamento automático** do rascunho, sem perder trabalho e sem um computador apagar o que o outro fez.

## 2. Escopo

**Dentro do escopo**
- Módulo `modules/marcenaria/orcamentos/` (tipos, schemas, serviços, queries, composables, telas).
- Item de menu, atalho "Novo orçamento" e botão "Novo orçamento" na tela de OS (E0c).
- Linha "Orçamentos de Marcenaria" na matriz de cargos.
- Cadastro rápido de insumo (T4).
- Testes e roteiro manual.

**Fora do escopo**
- Proposta em PDF (Spec 07). Esta spec deixa o **lugar** do botão no modal de envio (§7.9).
- Aprovar, gerar OS e desfazer (Spec 08B). O botão "Aprovar" não aparece aqui, mesmo que `acoes.aprovar` venha `true`.
- Campo do arquiteto (RT) no orçamento (Spec 09B). Aqui o painel de custos só **mostra** o RT que o motor devolve.
- Importação 3D (T3b) e categoria do móvel (T4): não existem.

---

## 3. Arquivos afetados

```
frontend/src/
├── shared/constants/permissions.constants.ts                 # ALTERAR ⚠️ — 3 chaves + aliases
├── modules/
│   ├── mainLayout/
│   │   ├── routes.ts                                         # ALTERAR ⚠️ — 3 rotas filhas
│   │   ├── types/layout.types.ts                             # ALTERAR ⚠️ — `requiredCapacidade?`, rótulo 'Orçamentos'
│   │   ├── constants/layout.constants.ts                     # ALTERAR ⚠️ — item "Orçamentos"
│   │   ├── components/layout/sidebar/BaseSidebar.vue         # ALTERAR ⚠️ — filtro por capacidade
│   │   └── views/MainLayout.vue                              # ALTERAR ⚠️ — atalho "Novo orçamento"
│   ├── order-service/views/OrdemServicoView.vue              # ALTERAR ⚠️ — botão "Novo orçamento"
│   ├── employees/constants/positions.constants.ts            # ALTERAR ⚠️ — linha da matriz
│   └── marcenaria/orcamentos/                                # CRIAR — tudo abaixo
│       ├── constants/
│       │   ├── orcamento.constants.ts                        # status, rótulos, cores, chaves de query, sugestões de ambiente
│       │   └── avisos.constants.ts                           # texto de cada aviso do motor
│       ├── types/orcamento.types.ts                          # tipos da API (espelham a 06A)
│       ├── schemas/
│       │   ├── orcamentoDetalhe.schema.ts                    # zod da resposta (com e sem custos)
│       │   ├── movelForm.schema.ts                           # zod do modal do móvel
│       │   └── insumoRapido.schema.ts                        # zod do cadastro rápido
│       ├── services/
│       │   ├── orcamento.service.ts                          # CRUD, transições, versões, histórico
│       │   ├── orcamentoMovel.service.ts                     # ambientes, móveis, simular
│       │   ├── orcamentoPrecos.service.ts                    # preços desatualizados e atualização
│       │   └── orcamentoAnexos.service.ts                    # anexos
│       ├── composables/
│       │   ├── useOrcamentosQuery.ts                         # lista + contagens
│       │   ├── useOrcamentoQuery.ts                          # detalhe
│       │   ├── useFilaOrcamento.ts                           # fila única de escrita (D7)
│       │   ├── useSalvamentoAutomatico.ts                    # cabeçalho (D8–D10)
│       │   ├── useAcoesOrcamento.ts                          # enviar, recusar, versões...
│       │   ├── useSimularMovel.ts                            # prévia do preço no modal (D6)
│       │   ├── usePermissoesOrcamento.ts                     # ver/gerir/excluir/custos
│       │   └── useExigeCapacidade.ts                         # guarda da rota (D3)
│       ├── utils/
│       │   ├── conversoes.ts                                 # R$↔centavos, %↔bp, qtd↔milésimos, mm
│       │   ├── diferencaCabecalho.ts                         # o que mudou desde o último salvamento
│       │   └── dadosProposta.ts                              # o que o CLIENTE pode ver (visão do cliente e Spec 07)
│       ├── views/
│       │   ├── OrcamentosListaView.vue
│       │   └── OrcamentoEditorView.vue
│       └── components/
│           ├── lista/{OrcamentosFiltros,OrcamentosTabela,OrcamentoStatusBadge}.vue
│           ├── editor/
│           │   ├── EditorCabecalho.vue                       # código, versão, status, salvamento, ações
│           │   ├── EditorFaixaStatus.vue                     # faixa por status (D13)
│           │   ├── EditorAvisos.vue
│           │   ├── BlocoClienteProjeto.vue
│           │   ├── BlocoAmbientes.vue  · AmbienteCard.vue · MovelLinha.vue
│           │   ├── BlocoInstalacao.vue
│           │   ├── BlocoMedicao.vue    · AnexosOrcamento.vue
│           │   ├── BlocoCondicoes.vue  · CampoPercentualOuValor.vue
│           │   ├── PainelResumo.vue    · PainelCustos.vue
│           │   └── VisaoClienteView.vue                      # T3a
│           └── modais/
│               ├── MovelModal.vue      · InsumosEditor.vue · InsumoBusca.vue
│               ├── InsumoRapidoModal.vue
│               ├── EnviarModal.vue · RecusarModal.vue · VoltarEditarModal.vue
│               ├── AtualizarPrecosModal.vue
│               ├── ProjetoModal.vue
│               ├── VersoesMenu.vue · HistoricoDrawer.vue
│               └── ConflitoModal.vue                         # D12
```

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `services/*` | Chamar a API e validar a resposta com zod | Regra de tela |
| `useFilaOrcamento` | Enfileirar **toda** escrita do orçamento, mandar a `revisao` atual, gravar a resposta no cache | Decidir o que salvar |
| `useSalvamentoAutomatico` | Observar o cabeçalho, juntar mudanças, mandar à fila, expor o estado ("Salvo às 14:32") | Ambientes e móveis (são ações imediatas) |
| `OrcamentoEditorView` | Montar os blocos, ligar `acoes` aos botões, tratar conflito | Calcular valor nenhum |
| `MovelModal` | Formulário do móvel e prévia do preço | Gravar sozinho (devolve o móvel ao editor) |

---

## 4. Decisões

### 4.1. Navegação e acesso

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Rotas filhas do layout principal: `/orcamentos` (lista), `/orcamentos/novo` e `/orcamentos/:id` (editor). Nomes `marcenaria-orcamentos`, `marcenaria-orcamento-novo`, `marcenaria-orcamento` | Mesmo lugar das outras telas (`mainLayout/routes.ts`); o layout dá menu, cabeçalho e atalhos |
| D2 | Item de menu **"Orçamentos"** logo depois de "Serviços", com permissão `view_orcamentos_marcenaria` e o campo **novo e genérico** `requiredCapacidade: 'orcamento_tecnico'`. Sem a capacidade, o item **some** (não fica com cadeado) | T2. Capacidade não é plano: um segmento sem orçamento técnico não tem o que comprar. Campo genérico em vez de `if (opt.id === ...)`, como o `services` faz hoje |
| D3 | Guarda **no componente** (`useExigeCapacidade('orcamento_tecnico')`): quando o contrato do segmento chega sem a capacidade, `router.replace({ name: 'home' })`. Enquanto carrega, vale o fallback (a marcenaria já declara a capacidade no fallback, 04B D2) | O guard do router não tem acesso ao TanStack Query (o `QueryClient` não é exportado). O backend já responde 404 (06A D26); a guarda só evita uma tela quebrada para quem digitar o endereço |
| D4 | Onde `podeCriarOSManual = false` **e** `temOrcamentoTecnico` **e** o usuário pode gerir orçamentos: o atalho "Criar OS" do menu rápido vira **"Novo orçamento"**, e a tela de OS (aba Ordens) mostra **"Novo orçamento"** no lugar de "Nova OS". Os dois levam a `/orcamentos/novo` | E0c e 03B D3. Nos outros segmentos, nada muda: a regra começa por `podeCriarOSManual`, que é `true` lá |
| D5 | **Criação preguiçosa:** `/orcamentos/novo` abre o editor vazio, **sem** gravar. O `POST` acontece na primeira informação real (escolher cliente, digitar o nome do projeto ou adicionar um ambiente); depois, `router.replace` para `/orcamentos/:id` | Sem isto, cada clique em "Novo orçamento" seguido de "voltar" deixaria um rascunho vazio na lista, com número gasto |

### 4.2. Valores e salvamento

| # | Decisão | Motivo |
|---|---------|--------|
| D6 | **Nenhum cálculo em TypeScript** (C8). A tela só formata o que a API devolve. A prévia do preço no modal do móvel vem de `POST /{id}/moveis/simular` (06A Revisão 1), chamado 400 ms depois da última digitação | Dois motores acabariam discordando em centavos. O banco é local: a resposta chega em poucos milissegundos |
| D7 | **Fila única de escrita** por orçamento: toda escrita (cabeçalho, ambiente, móvel, anexo, transição) entra na fila e sai **uma por vez**, com a `revisao` que estiver no cache naquele momento. A resposta (detalhe completo, 06A D21) substitui o cache com `setQueryData` | A trava otimista (06A D20) exige a revisão certa. Duas escritas em paralelo do **mesmo** computador mandariam a mesma revisão e a segunda levaria 409 sem motivo |
| D8 | **Salvamento automático só do cabeçalho** (cliente, vendedor, projeto, medição, parâmetros, instalação, desconto, sinal, validade, prazo, observações): 800 ms depois da última mudança, manda **só os campos que mudaram** num `PATCH`. Ambientes e móveis são **ações** que gravam na hora (adicionar, renomear, excluir, salvar o modal) | T3d. Mandar só o que mudou evita sobrescrever um campo que o usuário nem tocou. Ações discretas não precisam de espera |
| D9 | Indicador ao lado do código: **"Salvando…"**, **"Salvo às 14:32"**, **"Alterações não salvas"** (esperando os 800 ms), **"Não foi possível salvar — tentando de novo"** (erro de rede: 3 novas tentativas, 2 s, 5 s, 10 s; depois, botão "Tentar agora") | O usuário precisa confiar no salvamento automático para não procurar um botão "Salvar" que não existe |
| D10 | Ao **sair** do editor (outra rota, fechar a aba do app), a fila é esvaziada antes (`onBeforeRouteLeave` espera o `flush`). Se o salvamento falhar, pergunta: "Há alterações que não foram salvas. Sair mesmo assim?" | Fechar o app ou trocar de tela não pode perder trabalho (T3d) |
| D11 | **Atualização entre computadores:** o detalhe é recarregado a cada `REFETCH_REALTIME` **só quando a fila está vazia e não há campo esperando salvar**. A lista recarrega sempre no mesmo intervalo | Padrão do projeto (`queryIntervals.ts`). Recarregar no meio da digitação apagaria o que o usuário acabou de escrever |
| D12 | **Conflito** (`409` com `codigo = REVISAO_DESATUALIZADA`, 06A Revisão 1): a fila para, e um modal que **não fecha sozinho** diz "Este orçamento foi alterado em outro computador." e lista os campos que **não** foram salvos ("Desconto, Observações da proposta"). Botão único: **"Recarregar orçamento"** | A trava avisa, mas não junta (06A §8). Mostrar o que se perdeu deixa o usuário refazer em segundos, em vez de descobrir depois |

### 4.3. Editor

| # | Decisão | Motivo |
|---|---------|--------|
| D13 | O que pode ser feito vem **só** de `acoes` (06A §6.2). Fora de `RASCUNHO`, todos os campos ficam somente leitura, e uma **faixa** no topo explica o status e oferece a ação certa (§6.3) | Uma regra só, a do backend. A faixa responde "por que não consigo editar?" antes de a pergunta surgir |
| D14 | **Visão do cliente** (T3a): botão no cabeçalho que troca o editor por uma tela **somente leitura** igual à proposta (T5): ambientes, móveis com descrição e medidas, **total por ambiente**, desconto, total, sinal, saldo, prazo e validade. **Sem** preço por móvel, insumos, custos, margens, avisos e parâmetros. Sai pelo botão "Voltar ao orçamento". Os dados vêm de `montarDadosProposta` (§7.13), a **mesma** função que a proposta impressa (Spec 07) usa | O vendedor vira a tela para o cliente. Mostrar ao cliente algo diferente da proposta geraria a pergunta "por que aqui está diferente?" Uma função só garante que as duas nunca divirjam |
| D15 | **Painel de custos** só com `inclui_custos`; **recolhível**, aberto por padrão. A preferência aberto/fechado fica no navegador (por usuário, com `try/catch`; sem armazenamento, fica aberto) | T3a. É conveniência de quem usa, não dado do orçamento |
| D16 | Sem `view_custos_marcenaria`: some o painel de custos; no modal do móvel somem **custo do insumo, mão de obra e valor da central**, com a frase "Mão de obra, valor da central e custos são preenchidos por quem vê os custos."; na instalação, aparece só o **preço** (sem o custo) | P4 e 06A D23–D24. O vendedor ainda monta o móvel (medidas e insumos); o dono completa |
| D17 | Avisos do motor viram frases (§6.6). `MARGEM_NEGATIVA` aparece **para todos**, mas sem números para quem não vê custos: "O desconto deixou o orçamento abaixo do custo. Fale com o responsável antes de enviar." | Esconder o aviso deixaria o vendedor vender no prejuízo sem saber. A frase avisa sem revelar a margem |
| D18 | **Desconto e sinal** (C7, C9): cada um com dois campos lado a lado, **%** e **R$**. O campo digitado define o modo (`PERCENTUAL` ou `VALOR`) e é o que vai para a API; o outro mostra o valor **equivalente**, calculado pela API, em cinza, com "≈": em R$, `calculo.desconto_centavos`/`sinal_centavos`; em %, `calculo.desconto_bp_efetivo`/`sinal_bp_efetivo` (Revisão 1) | "Digitar em um preenche o outro" (C7) sem cálculo em TS (C8): o equivalente vem da resposta |
| D19 | **Ambientes:** nome com **sugestões** (lista local: Cozinha, Sala de estar, Sala de jantar, Dormitório casal, Dormitório solteiro, Closet, Banheiro, Lavabo, Área de serviço, Home office, Varanda gourmet) e texto livre. Cada ambiente é um cartão recolhível com subtotal | 03A D11 deixou a lista para a 06B. Sugestão acelera; texto livre atende o caso raro |
| D20 | **Ordenar** ambientes e móveis com botões **subir/descer** (não arrastar), com `aria-label` | Mesmo padrão do editor de listas da 04B; arrastar é difícil de acertar no mouse e impossível no teclado |
| D21 | **Projeto (O5):** depois de escolher o cliente, o bloco mostra os projetos que ele já tem (06A Revisão 1, `GET /projetos`) para escolher, ou "Novo projeto" (nome + endereço da obra). **Trocar o cliente limpa o projeto escolhido** (o nome digitado fica) | O cliente que volta para fazer o quarto encontra o apartamento já cadastrado; um projeto de outro cliente nunca fica preso ao orçamento |
| D22 | **Vendedor:** select de funcionários ativos; vem preenchido com o funcionário do usuário logado (06A Revisão 1) | É quem recebe a comissão na OS (C5, O7); esquecer o campo não pode deixar a OS sem responsável |

### 4.4. Modal do móvel

| # | Decisão | Motivo |
|---|---------|--------|
| D23 | O modal **não** salva sozinho: botões **Cancelar**, **Salvar** e, ao criar, **"Salvar e adicionar outro"** (mantém o ambiente, limpa o resto). Fechar com alterações pergunta "Descartar as alterações deste móvel?" | Um móvel pela metade no orçamento seria pior que nenhum. O salvamento automático é do rascunho, não do formulário aberto |
| D24 | **Medidas em milímetros**, inteiras, rotuladas "Largura", "Altura", "Profundidade (mm)". Na lista, aparecem como "700 × 2200 × 600 mm" | Padrão da marcenaria e do banco (PR4); milímetro não tem vírgula para errar |
| D25 | **Quantidade do insumo** com até 3 casas ("1,4" chapa, "26" m de fita), convertida para milésimos com `Math.round`. A unidade vem do produto (`siglaUnidade`) | O banco guarda milésimos (06A D10); a unidade evita confundir "26 un" com "26 m" |
| D26 | **Busca de insumo** no cadastro de produtos (nome ou código, a partir de 2 letras, 300 ms). Cada resultado mostra nome, código, unidade, selo "sofre perda" e, **só com `view_custos`**, o custo pela regra O3a (última compra, senão custo médio). Escolher um produto que **já está** no móvel não duplica: leva o foco à quantidade da linha existente | F5, O3a. Linha duplicada faria o mesmo material aparecer duas vezes na separação (Spec 10) |
| D27 | Linha de insumo: descrição, quantidade, unidade, e com `view_custos`: custo unitário **editável** (ao editar, selo "manual"), selo de origem ("última compra", "custo médio", **"sem custo"** em vermelho) e subtotal (da prévia) | O3a. O selo "sem custo" chama atenção para o cadastro faltando antes de virar um móvel barato demais |
| D28 | **Mão de obra** (C4) em três opções: "Sem mão de obra", "Valor fixo (R$)", "Horas" (com a linha "Custo/hora deste orçamento: R$ 45,00"). Com custo/hora **zero**, aviso âmbar no próprio campo: "O custo/hora deste orçamento está em R$ 0,00; a mão de obra por horas sairá zerada." | 04A, Spec 05 `HORAS_SEM_CUSTO_HORA`. O aviso aparece onde a decisão é tomada |
| D29 | **Produção:** "Interna" (padrão) ou "Terceirizada"; terceirizada pede **central parceira** (select de fornecedores ativos, obrigatório) e **valor da central (R$)** | E6, 06A §6.9 |
| D30 | **Prévia** no rodapé do modal (D6): custo unitário (com `view_custos`), preço unitário e preço total do móvel. Enquanto a prévia carrega, os números ficam esmaecidos; se a simulação falhar, mostra "Prévia indisponível" e **não** impede salvar | O usuário vê o efeito de cada chapa e de cada hora antes de salvar; uma falha na prévia não pode travar o trabalho |

### 4.5. Cadastro rápido de insumo (T4)

| # | Decisão | Motivo |
|---|---------|--------|
| D31 | Na busca sem resultado (ou pelo link "Cadastrar insumo novo"), abre um modal **pequeno**: Nome*, Código*, Unidade*, Custo de compra (R$)*, Preço de venda (R$), "Sofre perda no orçamento". Usa o `POST /produtos` existente com `estoque.quantidade = 0`. Ao salvar, o produto entra no móvel na hora | Cadastrar uma chapa nova não pode exigir sair do orçamento. O cadastro completo (fotos, fiscal, fornecedor) fica para a tela de Produtos |
| D32 | **Código** vem sugerido ("INS-" + 6 dígitos do relógio) e é editável. Código repetido mostra o erro do backend no campo | O `codigo_produto` é obrigatório e único (`ProdutoCreate`); a marcenaria raramente tem SKU próprio |
| D33 | **Preço de venda vazio** grava `valor_varejo = custo de compra`, com a ajuda "Se a loja também vende este item no balcão, informe o preço. Sem ele, o preço de venda fica igual ao custo." | `valor_varejo` é obrigatório. Gravar 0 deixaria o item ser vendido de graça no PDV; igual ao custo é o erro menos caro |
| D34 | O modal respeita as configurações do cadastro de produto (`exigirCategoria`, `exigirCodigoBarras`): quando exigidas, os campos aparecem e são obrigatórios | Mesmas regras da tela de Produtos; o cadastro rápido não pode ser um atalho para burlá-las |
| D35 | Só aparece para quem pode **criar produto** (mesma chave que o `POST /produtos` exige; conferir em `ENDPOINT_PERMISSION_MAP` e `PERMISSION_ALIASES`) | Sem a permissão, o botão levaria a um 403 |

### 4.6. Ciclo de vida

| # | Decisão | Motivo |
|---|---------|--------|
| D36 | **Enviar:** o botão fica sempre visível em `RASCUNHO`. Ao clicar, se faltar algo, um modal lista **só o que falta** ("Escolha o cliente", "Dê um nome ao projeto", "Adicione pelo menos um móvel"), com link para o bloco. Completo, o modal de confirmação mostra total, sinal, validade ("vale até 21/10/2026, 15 dias") e os avisos do motor (não bloqueiam) | Botão desabilitado não explica por quê. Os avisos no último passo são a última chance de corrigir um insumo sem custo |
| D37 | **Voltar a editar** (T3c): confirmação "O cliente recebeu este orçamento com total de R$ 9.238,89. Ao editar, ele volta para Rascunho e precisa ser enviado de novo." | O valor já está com o cliente |
| D38 | **Recusar:** modal com motivo obrigatório (até 500), atalhos que preenchem o texto ("Preço", "Prazo", "Fechou com outra marcenaria", "Desistiu do projeto") e campo livre | 06A D17. Atalhos padronizam o motivo para relatórios futuros sem tirar a liberdade |
| D39 | **Renovar** (vencido) e **Nova versão**: depois da ação, se o usuário tem `view_custos` e `GET /precos-desatualizados` traz itens, abre o modal **Atualizar preços** (O3). Sem `view_custos`, aparece a faixa "Os preços dos insumos podem ter mudado. Peça a quem vê os custos para conferir antes de enviar." | O3: nunca mudar preço sem avisar, e nunca esconder que pode ter mudado |
| D40 | **Atualizar preços:** tabela com móvel, insumo, custo no orçamento, custo hoje (e origem), diferença e uma caixa por linha (todas marcadas); selo "perda mudou" quando `sofre_perda` mudou. Rodapé: "Total: R$ 9.238,89 → R$ 9.312,04 (+R$ 73,15)". Botões **"Manter preços do orçamento"** e **"Atualizar selecionados"**. Também abre pelo painel de custos ("Conferir preços dos insumos") em `RASCUNHO` | O vendedor decide sabendo quanto o total muda |
| D41 | **Excluir:** só no menu "Mais", só com `acoes.excluir`, com confirmação de perigo. Depois, volta à lista | 06A D18 |
| D42 | **Versões:** o rótulo "v2" no cabeçalho abre um menu com todas as versões (número, status, total, data). Em `SUBSTITUIDO`, a faixa diz "Esta versão foi substituída pela v3" com o link | O2. O histórico do que foi oferecido fica a um clique |
| D43 | **Histórico:** botão no cabeçalho abre uma gaveta lateral com os eventos (06A D25): frase, quem, quando ("há 2 horas", com a data completa no `title`) | T7 |

### 4.7. Medição e anexos

| # | Decisão | Motivo |
|---|---------|--------|
| D44 | Bloco **"Medição"**: o texto "Medidas e observações da medição" (salvamento automático) e a grade de anexos. Anexos entram por botão ou arrastando arquivos (vários de uma vez), com a legenda editável **depois** (06A Revisão 1) | O1. A legenda é o que ajuda a achar "Parede da pia" entre 15 fotos |
| D45 | Foto abre ampliada na própria tela; **PDF** abre no visualizador do sistema (`abrirArquivo`, já usado no módulo fiscal) | Reaproveita o que existe |
| D46 | Excluir anexo avisa: "Este arquivo é usado por todas as versões deste orçamento. Excluir mesmo assim?" | 06A D30 e §8 |
| D47 | Anexos podem ser incluídos, excluídos e legendados **em qualquer status, exceto `SUBSTITUIDO` e `APROVADO`**, desde que o usuário possa gerir. Anexar **não** passa pela fila (D7), porque não mexe na `revisao` | 06A D31 (Revisão 1): a foto do ambiente muitas vezes chega depois do envio e não muda o preço |

### 4.8. Lista e cargos

| # | Decisão | Motivo |
|---|---------|--------|
| D48 | Lista com **chips de status e contagem** ("Rascunho 3", "Enviado 5", "Vence em 3 dias 2", "Vencido 1", "Recusado", "Aprovado"), busca (código, projeto, cliente), vendedor e "Mostrar versões antigas". Contagens vêm de `GET /contagens` (06A Revisão 1) | T2. "Vence em 3 dias" é a pergunta que o vendedor faz toda manhã |
| D49 | Colunas: Código (com "v2"), Cliente, Projeto, Vendedor, Móveis, Total, **Margem** (só com `view_custos`), Validade ("vence em 2 dias" em âmbar; vencido em vermelho), Status, Atualizado. Linha inteira clicável | P4; padrão das tabelas do sistema |
| D50 | Lista vazia: "Nenhum orçamento ainda." com o botão "Novo orçamento" (se puder gerir). Filtro sem resultado: "Nenhum orçamento com estes filtros." com "Limpar filtros" | Os dois vazios pedem ações diferentes |
| D51 | Matriz de cargos: linha **"Orçamentos de Marcenaria"** (Ver / Gerenciar / Excluir) com `segmento: 'marcenaria'`, pelo mecanismo que a matriz já tem (04B Revisão 1). Marcar Gerenciar ou Excluir marca Ver | 06A D22. Os outros segmentos não veem a linha, e o nível de acesso deles não muda |

---

## 5. Contratos consumidos

Spec 06A §6 com a **Revisão 1** (feita junto com esta spec):

| Mudança na 06A | Usada em |
|----------------|----------|
| `409` com `detail = {codigo, mensagem}`: `REVISAO_DESATUALIZADA`, `STATUS_NAO_EDITAVEL`, `TRANSICAO_INVALIDA`, `EXCLUSAO_NAO_PERMITIDA` | D12 |
| `422` do motor com `detail = {codigo: "CALCULO_INVALIDO", campo, mensagem}` (`campo`: `desconto`, `sinal`, `markup`, `perda`, `custo_hora` ou `null`) | Erro no campo certo (§7.4) |
| `GET /projetos?cliente_id=` | D21 |
| `POST /{id}/moveis/simular` | D6, D30 |
| `PUT /{id}/moveis/{mid}`: chave de custo **ausente** mantém o valor gravado | D16 |
| `GET /contagens` | D48 |
| `PATCH /{id}/anexos/{xid}` (legenda) e anexos fora de `RASCUNHO` | D44, D47 |
| `POST /`: vendedor padrão = funcionário do usuário logado | D22 |

Outros contratos existentes: `GET /produtos?buscar=&limite=` e `POST /produtos` (cadastro rápido), `GET /fornecedores` (central), funcionários (o mesmo serviço que a OS usa, `getEmployeesAll`), `GET /configuracoes/marcenaria` (não usado aqui: o orçamento traz os próprios parâmetros), contrato do segmento (capacidades).

A resposta do detalhe é validada com **zod**, em duas formas (com e sem custos), como na 04B:

```ts
// orcamentoDetalhe.schema.ts (trecho)
const calculoMovelBase = z.object({                 // o que todos veem
  preco_unit_centavos: z.number().int(),            // preço de uma unidade do móvel
  preco_total_centavos: z.number().int(),           // preço × quantidade
});
const calculoMovelComCustos = calculoMovelBase.extend({   // só com view_custos (06A D23)
  material_centavos: z.number().int(),
  perda_centavos: z.number().int(),
  mao_obra_centavos: z.number().int(),
  custo_unit_centavos: z.number().int(),
  rt_linha_centavos: z.number().int(),
});

export const orcamentoDetalheSchema = z.discriminatedUnion('inclui_custos', [
  detalheBase.extend({ inclui_custos: z.literal(false) }),      // vendedor sem custos
  detalheComCustos.extend({ inclui_custos: z.literal(true) }),  // dono, gerente
]);
```

---

## 6. Telas

### 6.1. Lista — `/orcamentos`

```
Orçamentos                                                       [+ Novo orçamento]
[Todos 14] [Rascunho 3] [Enviado 5] [Vence em 3 dias 2] [Vencido 1] [Recusado 2] [Aprovado 1]
[🔍 Código, projeto ou cliente…]  [Vendedor ▾]  [ ] Mostrar versões antigas

Código            Cliente            Projeto              Vendedor  Móveis  Total        Margem  Validade         Status
ORC-2026-000084 v2 Studio Arquitet…  Res. Alpha Ville 802  Alan      7      R$ 9.238,89  36,6%   vence em 2 dias  Enviado
…
                                                                   [‹ 1 2 3 ›]
```

- "Vence em 3 dias" usa `vence_em_dias=3`; os outros chips usam `status`.
- O filtro escolhido fica na URL (`?status=ENVIADO&busca=alpha`): voltar do editor devolve a mesma lista.
- Carregando: esqueleto da tabela (`BaseTableContainer`). Erro: mensagem e "Tentar de novo".
- Sem permissão de ver: a rota mostra "Você não tem permissão para ver orçamentos." (o menu já não mostra o item).

### 6.2. Editor — `/orcamentos/:id` e `/orcamentos/novo`

```
← Orçamentos   ORC-2026-000084  [v2 ▾]  (Rascunho)   ✓ Salvo às 14:32
                                   [Visão do cliente] [Histórico] [Mais ▾] [Enviar ao cliente]
┌ Faixa de status (D13) ────────────────────────────────────────────────────────────┐
┌ Avisos (D17) ─────────────────────────────────────────────────────────────────────┐
├──────────────────────────────────────────────────────────┬─────────────────────────┤
│ Cliente e projeto                                        │ Resumo                  │
│  Cliente [Studio Arquitetura…  Trocar]   Vendedor [▾]     │  Bruto       9.725,15   │
│  Projeto (•) Res. Alpha Ville 802 ( ) Novo projeto        │  Desconto 5%  −486,26   │
│  Endereço da obra  Av. das Américas, 4200                 │  Total       9.238,89   │
│                                                          │  Sinal 40%   3.695,56   │
│ Ambientes                                   [+ Ambiente] │  Saldo       5.543,33   │
│  ▾ Cozinha Gourmet                  Subtotal 8.300,15 ⋯  │  Instalação incluída    │
│     Torre Quente   700 × 2200 × 600 mm  1×  Terceirizada │─────────────────────────│
│                               R$ 4.222,75   ✎ ⧉ ↑ ↓ 🗑    │ Custos ▾ (D15)          │
│     Balcão         …                    2×               │  Material   …           │
│                               R$ 4.077,40   ✎ ⧉ ↑ ↓ 🗑    │  Perda      …           │
│     [+ Adicionar móvel]                                  │  Mão de obra …          │
│ Instalação  [x] Cobrar instalação  Custo R$ 750,00       │  Terceirizados …        │
│             Preço R$ 1.425,00                            │  Custo total 5.118,50   │
│                                                          │  Margem bruta 4.120,39  │
│ Medição                                                  │  RT arquiteto  739,11   │
│  Medidas e observações [ texto ]                         │  Margem líquida 3.381,28│
│  [foto][foto][PDF Planta] [+ Anexar]                     │                 (36,6%) │
│                                                          │  Parâmetros deste orç.  │
│ Condições                                                │  Markup 90%  Perda 10%  │
│  Desconto [ 5 ]% ≈ R$ 486,26   Sinal [ 40 ]% ≈ R$ 3.695  │  Custo/hora R$ 45,00    │
│  Validade [15] dias   Prazo de entrega [30] dias          │  [Conferir preços]      │
│  Observações da proposta [ texto ]                       │                         │
└──────────────────────────────────────────────────────────┴─────────────────────────┘
```

- Coluna lateral **fixa** ao rolar (`sticky`). Em janela estreita (< 1024 px), ela desce para baixo do conteúdo.
- O cartão do ambiente mostra o **subtotal bruto** (antes do desconto), como na proposta (06A §6.2).
- Na linha do móvel, com `view_custos`, aparece também "custo R$ 2.222,50 · margem 47%" em cinza, abaixo do preço.
- Menu "⋯" do ambiente: Renomear, Subir, Descer, Excluir ("Excluir o ambiente Cozinha Gourmet e os 4 móveis dele?").
- Ações do móvel: Editar, Duplicar (06A, " (cópia)"), Subir, Descer, Excluir (confirmação simples).
- **Parâmetros deste orçamento** (markup, perda, custo/hora) ficam no painel de custos, com a frase "Valem só para este orçamento. O padrão fica em Configurações › Marcenaria."
- Instalação: a caixa "Cobrar instalação" desmarcada manda `instalacao_custo_centavos = null`.

### 6.3. Faixa de status (D13)

| Status | Texto | Ações |
|--------|-------|-------|
| `RASCUNHO` | (sem faixa) | — |
| `ENVIADO` | "Enviado em 06/10/2026. Vale até 21/10/2026 (em 15 dias)." | Voltar a editar · Recusar · Nova versão |
| `VENCIDO` | "A validade terminou em 21/10/2026." | Renovar · Nova versão · Recusar |
| `RECUSADO` | "Recusado em 12/10/2026: Preço." | Nova versão |
| `SUBSTITUIDO` | "Esta versão foi substituída pela v3." | Abrir v3 |
| `APROVADO` | "Aprovado em 15/10/2026." (a Spec 08B acrescenta a OS) | — |

Cada botão aparece só se a ação correspondente de `acoes` for `true`.

### 6.4. Modal do móvel

```
Novo móvel — Cozinha Gourmet                                                 [×]
Nome*            [Torre Quente c/ Nicho p/ Forno e Micro-ondas            ]
Descrição        [MDF Branco TX e Freijó, corrediças com amortecedor      ]  sai na proposta
Medidas (mm)     Largura [700]  Altura [2200]  Profundidade [600]   Quantidade [1]
Ambiente         [Cozinha Gourmet ▾]                                          (só ao editar)
Produção         (•) Interna  ( ) Terceirizada → Central [▾]  Valor da central R$ [   ]

Insumos                                               [🔍 Buscar no cadastro…]
 MDF Branco TX 18mm     [1,4] un   R$ 280,00 (última compra)  sofre perda   R$ 392,00  🗑
 Fita de borda 22mm     [26 ] m    R$ 0,00   (sem custo)                    R$ 0,00    🗑
 Corrediça telescópica  [2  ] par  R$ 200,00 (manual)                       R$ 400,00  🗑
 Nenhum produto encontrado. [Cadastrar insumo novo]

Mão de obra      ( ) Sem  (•) Valor fixo R$ [300,00]  ( ) Horas [  ]  (R$ 45,00/h)

──────────────────────────────────────────────────────────────────────────────────
Custo unitário R$ 2.222,50   Preço unitário R$ 4.222,75   Total R$ 4.222,75
                                  [Cancelar] [Salvar e adicionar outro] [Salvar]
```

- Sem `view_custos`: sem a coluna de custo, sem "Mão de obra", sem "Valor da central", sem "Custo unitário" na prévia (D16).
- Validação (zod) com as mesmas regras do backend: nome obrigatório (até 120), descrição até 500, medidas inteiras ≥ 0, quantidade ≥ 1, quantidade de insumo > 0, central obrigatória em terceirizada, até 100 insumos.
- Ao editar, insumos existentes vão com o `id` (mantêm o custo copiado, 06A §6.4); só a quantidade muda, a não ser que o custo seja editado à mão.

### 6.5. Visão do cliente (D14)

Mesma ordem da proposta: cabeçalho com cliente, projeto e endereço; cada ambiente com os móveis (nome, descrição, medidas, quantidade) e o **total do ambiente**; instalação (preço); bruto, desconto, total; sinal e saldo; prazo de entrega ("30 dias após a aprovação") e validade. Fundo claro, fonte maior. Botão fixo "Voltar ao orçamento".

### 6.6. Avisos do motor (D17)

| Código | Com `view_custos` | Sem `view_custos` |
|--------|-------------------|-------------------|
| `INSUMO_SEM_CUSTO` | "Há insumos sem custo cadastrado (R$ 0,00). Confira os itens marcados com \"sem custo\"." | igual |
| `HORAS_SEM_CUSTO_HORA` | "Há móveis com mão de obra por horas, mas o custo/hora deste orçamento é R$ 0,00." | (não aparece: o vendedor não vê nem edita a mão de obra) |
| `MARGEM_NEGATIVA` | "A margem líquida está negativa: o orçamento sai abaixo do custo." | "O desconto deixou o orçamento abaixo do custo. Fale com o responsável antes de enviar." |
| `ORCAMENTO_VAZIO` | "Adicione um ambiente e um móvel para começar." (texto neutro, não âmbar) | igual |

Código desconhecido (spec futura) não quebra a tela: não aparece.

---

## 7. Especificação técnica

### 7.1. Rotas — `mainLayout/routes.ts`

```ts
      {
        path: '/orcamentos',                                    // lista (D1)
        name: 'marcenaria-orcamentos',
        component: () => import('@/modules/marcenaria/orcamentos/views/OrcamentosListaView.vue'),
        meta: {
          title: 'Orçamentos',
          subtitle: 'Propostas de móveis planejados, do rascunho à aprovação.',
          tabId: 'marcenaria-orcamentos',                       // marca o item do menu como ativo
          requiresAuth: true,
        },
      },
      {
        path: '/orcamentos/novo',                               // editor ainda sem gravar (D5)
        name: 'marcenaria-orcamento-novo',
        component: () => import('@/modules/marcenaria/orcamentos/views/OrcamentoEditorView.vue'),
        meta: { title: 'Novo orçamento', tabId: 'marcenaria-orcamentos', requiresAuth: true },
      },
      {
        path: '/orcamentos/:id(\\d+)',                          // só número: "novo" não cai aqui
        name: 'marcenaria-orcamento',
        component: () => import('@/modules/marcenaria/orcamentos/views/OrcamentoEditorView.vue'),
        props: (rota) => ({ id: Number(rota.params.id) }),      // a tela recebe o id já como número
        meta: { title: 'Orçamento', tabId: 'marcenaria-orcamentos', requiresAuth: true },
      },
```

`/orcamentos` não colide com nenhuma rota atual (o orçamento do PDV vive dentro de Vendas). O título do layout troca para o código (`ORC-2026-000084 v2`) quando o detalhe chega, pelo mesmo `layoutStore` que já recebe `title`.

### 7.2. Menu — `layout.types.ts`, `layout.constants.ts`, `BaseSidebar.vue`

```ts
// layout.types.ts — acrescentar:
export type SidebarLabelOptions = /* ...os de hoje... */ | 'Orçamentos';

export interface SidebarOption {
  // ...campos de hoje
  /**
   * Capacidade do segmento que este item exige (ex.: 'orcamento_tecnico').
   * Sem ela, o item SOME: capacidade não é plano, então não há o que vender com cadeado.
   */
  requiredCapacidade?: SegmentCapability;
}

// layout.constants.ts — logo depois de 'services':
      {
        id: 'marcenaria-orcamentos',                       // nome da rota (navega direto)
        icon: ClipboardList,
        label: 'Orçamentos',
        requiredPermission: PERMISSIONS.viewOrcamentosMarcenaria,
        requiredCapacidade: 'orcamento_tecnico',           // só no segmento com orçamento técnico
      },

// BaseSidebar.vue — dentro do .filter((opt) => { ... }), antes da permissão:
        // Item que depende do que o segmento FAZ (contrato do backend), não do plano.
        if (opt.requiredCapacidade && !temCapacidade(opt.requiredCapacidade)) return false;
```

`temCapacidade` é o `tem` de `useCapacidades()`. O `MainLayout` já usa o contrato do segmento (mesma `queryKey`), então o menu **não** faz chamada nova. Enquanto o contrato carrega, vale o fallback (04B D2): o item não pisca.

### 7.3. Permissões — `permissions.constants.ts`

```ts
  /** Ver a lista e abrir orçamentos de marcenaria (Spec 06A D22). */
  viewOrcamentosMarcenaria: 'view_orcamentos_marcenaria',
  /** Criar, editar, enviar, recusar, versões e anexos. Inclui ver. */
  manageOrcamentosMarcenaria: 'manage_orcamentos_marcenaria',
  /** Excluir rascunho nunca enviado (06A D18). */
  deleteOrcamentosMarcenaria: 'delete_orcamentos_marcenaria',

// PERMISSION_ALIASES — quem gere ou exclui também vê:
  [PERMISSIONS.viewOrcamentosMarcenaria]: ['manage_orcamentos_marcenaria', 'delete_orcamentos_marcenaria'],
```

`usePermissoesOrcamento` junta tudo num lugar (lembrando que `hasPermission` não considera `is_master`, 04B §6.2):

```ts
export function usePermissoesOrcamento() {
  const { hasPermission } = useCheckPermission();          // permissões do cargo
  const { userData } = storeToRefs(useAuthStore());        // usuário logado
  const isMaster = computed(() => userData.value?.is_master === true); // dono do sistema passa em tudo (padrão do projeto)
  const pode = (chave: Permissions) => computed(() => isMaster.value || hasPermission(chave));
  return {
    podeVer: pode(PERMISSIONS.viewOrcamentosMarcenaria),     // menu e lista
    podeGerir: pode(PERMISSIONS.manageOrcamentosMarcenaria), // botões "Novo orçamento"
    podeVerCustos: pode(PERMISSIONS.viewCustosMarcenaria),   // painel de custos (04B)
  };
}
```

Dentro do editor, **quem decide** são `acoes` e `inclui_custos` da resposta (D13); `usePermissoesOrcamento` serve às telas que ainda não têm um orçamento carregado (menu, lista, atalhos).

### 7.4. Fila de escrita — `useFilaOrcamento.ts` (D7, D12)

```ts
/**
 * Fila única de escrita de UM orçamento.
 * Toda gravação passa por aqui, uma de cada vez, com a revisão mais recente do cache.
 */
export function useFilaOrcamento(id: Ref<number | null>) {
  const queryClient = useQueryClient();                      // cache do TanStack Query
  let fila: Promise<unknown> = Promise.resolve();            // a "corrente" de escritas, uma após a outra
  const pendentes = ref(0);                                  // quantas escritas ainda não terminaram
  const conflito = ref(false);                               // true depois de um 409 de revisão

  /** Enfileira uma escrita. `executar` recebe a revisão atual e devolve o detalhe novo. */
  function enfileirar(executar: (revisao: number) => Promise<OrcamentoDetalhe>) {
    pendentes.value++;                                       // a tela mostra "Salvando…"
    const tarefa = fila.then(async () => {
      if (conflito.value) throw new ConflitoRevisao();       // depois de um conflito, nada mais sai
      const atual = queryClient.getQueryData<OrcamentoDetalhe>(chaveDetalhe(id.value!));
      try {
        const novo = await executar(atual!.revisao);         // manda a revisão que o cache tem AGORA
        queryClient.setQueryData(chaveDetalhe(id.value!), novo); // a resposta já traz o cálculo novo
        return novo;
      } catch (erro) {
        if (codigoDoErro(erro) === 'REVISAO_DESATUALIZADA') conflito.value = true; // abre o ConflitoModal
        throw erro;                                          // quem chamou decide a mensagem
      } finally {
        pendentes.value--;
      }
    });
    fila = tarefa.catch(() => undefined);                    // um erro não trava as próximas da fila
    return tarefa;
  }

  /** Espera tudo o que está na fila (usado ao sair da tela, D10). */
  const esvaziar = () => fila;

  return { enfileirar, esvaziar, pendentes, conflito };
}
```

- Depois de toda escrita, a lista é invalidada (`invalidateQueries` da chave da lista e das contagens), não recarregada na hora.
- `codigoDoErro` lê `error.response.data.detail.codigo` (06A Revisão 1). O texto do `409` não é comparado em lugar nenhum.

### 7.5. Salvamento automático — `useSalvamentoAutomatico.ts` (D8–D11)

```ts
/** Campos do cabeçalho que salvam sozinhos (D8). Ambientes e móveis ficam de fora. */
const CAMPOS_AUTOMATICOS = [
  'cliente_id', 'funcionario_id', 'objeto_id', 'projeto_nome', 'endereco_obra',
  'medicao_observacoes', 'markup_bp', 'perda_bp', 'custo_hora_centavos',
  'instalacao_custo_centavos', 'desconto', 'sinal', 'validade_dias',
  'prazo_entrega_dias', 'observacoes_proposta',
] as const;

export function useSalvamentoAutomatico(detalhe: Ref<OrcamentoDetalhe | undefined>, fila: FilaOrcamento) {
  const form = reactive(cabecalhoDoDetalhe(detalhe.value));  // cópia editável dos campos
  let ultimoSalvo = cabecalhoDoDetalhe(detalhe.value);        // o que o servidor tem
  const estado = ref<'salvo' | 'esperando' | 'salvando' | 'erro'>('salvo');
  const salvoEm = ref<Date | null>(null);                     // "Salvo às 14:32"
  const errosPorCampo = ref<Record<string, string>>({});     // 422 com `campo` (06A Revisão 1)

  const salvar = useDebounceFn(async () => {
    const mudancas = diferencaCabecalho(ultimoSalvo, form);   // só o que mudou (D8)
    if (!Object.keys(mudancas).length) { estado.value = 'salvo'; return; }
    estado.value = 'salvando';
    try {
      const novo = await fila.enfileirar((revisao) => patchOrcamento(detalhe.value!.id, revisao, mudancas));
      ultimoSalvo = { ...ultimoSalvo, ...mudancas };          // o servidor agora tem isso
      errosPorCampo.value = {};
      estado.value = 'salvo';
      salvoEm.value = new Date();
    } catch (erro) {
      const campo = campoDoErro(erro);                         // 'desconto', 'sinal'... ou null
      if (campo) errosPorCampo.value = { [campo]: mensagemDoErro(erro) }; // mostra embaixo do campo
      estado.value = 'erro';                                   // rede: novas tentativas (D9)
    }
  }, 800);                                                     // 800 ms depois da última tecla

  watch(form, () => { estado.value = 'esperando'; salvar(); }, { deep: true });

  /** Detalhe novo do servidor (polling ou outra ação): só entra se nada está pendente (D11). */
  watch(detalhe, (novo) => {
    if (estado.value === 'salvo' && fila.pendentes.value === 0) {
      Object.assign(form, cabecalhoDoDetalhe(novo));          // atualiza a tela sem apagar digitação
      ultimoSalvo = cabecalhoDoDetalhe(novo);
    }
  });

  return { form, estado, salvoEm, errosPorCampo, salvarAgora: salvar };
}
```

- Erro de validação (`422`) **não** tenta de novo: o campo fica com a mensagem e o valor digitado, até o usuário corrigir.
- Erro de rede tenta de novo em 2 s, 5 s e 10 s; depois, "Tentar agora".
- `campos pendentes` (para o `ConflitoModal`, D12) = chaves de `diferencaCabecalho(ultimoSalvo, form)`, traduzidas para os rótulos da tela.
- Na rota `/orcamentos/novo` (D5), o primeiro `salvar` com cliente, projeto ou ambiente faz o `POST` em vez do `PATCH` e troca a rota com `router.replace`.

### 7.6. Prévia do móvel — `useSimularMovel.ts` (D6, D30)

```ts
export function useSimularMovel(orcamentoId: Ref<number>, movel: Ref<MovelForm>) {
  const entrada = refDebounced(movel, 400);                       // espera o usuário parar de digitar
  return useQuery({
    queryKey: computed(() => ['marcenaria-simular', orcamentoId.value, entrada.value]),
    queryFn: () => simularMovel(orcamentoId.value, paraApiMovel(entrada.value)), // nada é gravado
    enabled: computed(() => movelSimulavel(entrada.value)),       // nome e quantidade válidos
    placeholderData: keepPreviousData,                            // mantém o último número, esmaecido
    retry: false,                                                 // falhou: "Prévia indisponível" (D30)
  });
}
```

A resposta também traz o **custo e a origem** dos insumos novos (06A Revisão 1), para o selo "última compra / custo médio / sem custo" aparecer antes de salvar.

### 7.7. Conversões — `utils/conversoes.ts`

```ts
/** R$ (número da tela) → centavos. Arredonda, nunca trunca (PR4). */
export const reaisParaCentavos = (reais: number) => Math.round(reais * 100);
/** % (número da tela) → basis points: 12,35 % → 1235. */
export const percentualParaBp = (percentual: number) => Math.round(percentual * 100);
/** Quantidade de insumo (até 3 casas) → milésimos: 1,4 → 1400. */
export const quantidadeParaMilesimos = (quantidade: number) => Math.round(quantidade * 1000);
/** Milésimos → número da tela: 1400 → 1,4. */
export const milesimosParaQuantidade = (milesimos: number) => milesimos / 1000;
/** Medidas para a lista: (700, 2200, 600) → "700 × 2200 × 600 mm"; medida vazia sai como "—". */
export function formatarMedidas(l?: number | null, a?: number | null, p?: number | null): string {
  if (l == null && a == null && p == null) return '';           // móvel sem medidas: nada a mostrar
  return `${[l, a, p].map((m) => (m == null ? '—' : m)).join(' × ')} mm`;
}
/** Margem em bp → texto: 3660 → "36,6%". */
export const formatarBp = (bp: number) => `${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
```

Dinheiro sempre por `formatCurrency` (já recebe centavos).

### 7.8. Status — `orcamento.constants.ts`

```ts
/** Rótulo e cor de cada status (mesma paleta dos badges de OS). */
export const STATUS_ORCAMENTO = {
  RASCUNHO:    { rotulo: 'Rascunho',    cor: 'zinc' },
  ENVIADO:     { rotulo: 'Enviado',     cor: 'blue' },
  APROVADO:    { rotulo: 'Aprovado',    cor: 'green' },
  RECUSADO:    { rotulo: 'Recusado',    cor: 'red' },
  VENCIDO:     { rotulo: 'Vencido',     cor: 'amber' },
  SUBSTITUIDO: { rotulo: 'Substituído', cor: 'zinc-claro' },
} as const;
```

### 7.9. Enviar e a Spec 07

`EnviarModal.vue` tem um espaço (`<slot name="proposta">`) acima dos botões. A Spec 07 coloca ali "Gerar proposta (PDF)" e decide se o envio exige o PDF gerado. Nesta spec, o modal envia direto.

### 7.10. Atalhos e tela de OS (D4)

```ts
// MainLayout.vue — o atalho "Criar OS" (já filtrado pela 03B) ganha a alternativa:
const { temOrcamentoTecnico } = useCapacidades();
const { podeGerir } = usePermissoesOrcamento();

const quickActions = computed<QuickActionItem[]>(() =>
  TODOS_OS_ATALHOS.flatMap((acao) => {
    if (acao.id !== 'nova-os' || podeCriarOSManual.value) return [acao];       // hoje: igual
    if (temOrcamentoTecnico.value && podeGerir.value)                          // marcenaria
      return [{ ...acao, id: 'novo-orcamento', label: 'Novo orçamento',
                action: () => router.push({ name: 'marcenaria-orcamento-novo' }) }];
    return [];                                                                 // sem OS e sem orçamento
  }),
);
```

Em `OrdemServicoView.vue`, na aba Ordens, quando `mostrarBotaoAdicionar` (03B) for `false` por causa de `podeCriarOSManual`, aparece "Novo orçamento" com as mesmas condições.

### 7.11. Matriz de cargos — `positions.constants.ts`

```ts
  {
    id: 'marcenaria_orcamentos',
    label: 'Orçamentos de Marcenaria',
    description: 'Ver, montar, enviar e excluir orçamentos',
    icon: ClipboardList,
    viewKey: 'view_orcamentos_marcenaria',
    manageKey: 'manage_orcamentos_marcenaria',
    deleteKey: 'delete_orcamentos_marcenaria',
    segmento: 'marcenaria',                   // só aparece na marcenaria e fica fora do nível de acesso (04B Revisão 1)
  },
```

Fica **antes** de "Custos da Marcenaria" (04B). `MODULE_PERMISSION_MAP` não muda (mesmo motivo da 04B).

### 7.12. Detalhes de comportamento

- **Foco:** ao abrir o editor novo, o foco vai para "Cliente"; ao adicionar ambiente, para o nome dele; ao abrir o modal do móvel, para "Nome".
- **Teclado:** `Esc` fecha modais (com a pergunta de descarte quando há mudança); `Enter` na busca de insumo escolhe o primeiro resultado.
- **Números:** dinheiro com `BaseMoneyInput`; percentuais com 2 casas; dias inteiros de 1 a 365 (validade e prazo), as mesmas regras da 04A (Revisão 1).
- **Datas:** "vence em 2 dias", "vence hoje", "venceu há 3 dias", calculadas pela data local, como o resto do sistema (`date.utils.ts`).

### 7.13. O que o cliente vê — `utils/dadosProposta.ts`

Função pura que recebe o detalhe e devolve **só** o que pode chegar ao cliente. Usada pela visão do cliente (D14) e pela proposta impressa (Spec 07, que a detalha em §6.1 de lá). O tipo de saída **não tem** nenhum campo de custo, margem, insumo, parâmetro ou preço por móvel; um teste confere isso (caso 28).

---

## 8. Prova de não regressão (⚠️ PR1)

1. `npm run test` e `npx vue-tsc --noEmit` sem erros.
2. **Menu:** em informática, oficina, serigrafia e PDV, o menu tem os mesmos itens, na mesma ordem. Nenhum item "Orçamentos".
3. **Atalhos:** nos mesmos segmentos, o menu rápido tem os mesmos 4 atalhos, com os mesmos textos ("Criar OS" continua).
4. **Tela de OS:** aba Ordens com "Nova OS", como hoje.
5. **Cargos:** sem a linha nova; nível de acesso dos cargos existentes idêntico (mesmo teste da 04B §7.4, com as 3 chaves novas).
6. **Rede:** nenhuma chamada a `/marcenaria/...` nos outros segmentos (DevTools).
7. **Orçamento do PDV** (Vendas): tela e rota inalteradas.

## 9. Limitações conhecidas

- **Modal do móvel não salva sozinho** (D23): fechar o app com o modal aberto perde **aquele** móvel. O resto do orçamento já está salvo.
- **Conflito sem junção** (D12): quem perdeu o conflito refaz as alterações listadas.
- **Fechar a janela do app:** o `beforeunload` não espera uma chamada terminar. A espera de 800 ms (D8) deixa no máximo o último segundo de digitação em risco; trocar de tela dentro do app espera a fila (D10).
- **Um arquiteto só na tela** (09B; o modelo aceita vários).
- **Visão do cliente sem preço por móvel** (D14): se o cliente pedir o preço de um móvel, o vendedor sai da visão do cliente. É o mesmo comportamento da proposta (T5).

---

## 10. Critérios de aceite

- [ ] Marcenaria, master: menu "Orçamentos", lista com contagens, "Novo orçamento" no menu rápido e na tela de OS.
- [ ] "Novo orçamento" seguido de "voltar" não cria nada; escolher o cliente cria e troca a rota para `/orcamentos/:id`.
- [ ] Editar desconto, sinal, medição e condições salva sozinho; o indicador passa por "Alterações não salvas" → "Salvando…" → "Salvo às hh:mm".
- [ ] Desconto em R$ maior que o total mostra a mensagem do backend **embaixo do campo**, sem perder o valor digitado.
- [ ] Ambientes: adicionar com sugestão, renomear, subir, descer, excluir com confirmação.
- [ ] Móvel: criar com insumos, mão de obra fixa e por horas, interno e terceirizado; prévia do preço muda ao digitar; "Salvar e adicionar outro" funciona.
- [ ] Insumo já incluído não duplica; insumo sem custo aparece com selo vermelho e aviso no orçamento.
- [ ] Cadastro rápido cria o produto e o coloca no móvel; preço de venda vazio grava o custo.
- [ ] Dois computadores no mesmo rascunho: o segundo a salvar vê o modal de conflito com os campos perdidos; "Recarregar" traz a versão atual.
- [ ] Enviar sem cliente lista só o que falta; completo, mostra total, sinal, validade e avisos; enviado, a faixa mostra a validade.
- [ ] Voltar a editar, recusar (com motivo), renovar, nova versão (com atualizar preços), excluir e histórico funcionam conforme `acoes`.
- [ ] Vendedor sem `view_custos`: sem painel de custos, sem coluna de margem, sem mão de obra/central/custo no modal; salvar um móvel dele não apaga a mão de obra que o dono lançou.
- [ ] Visão do cliente mostra só o que a proposta mostra.
- [ ] Anexos: fotos e PDF entram (vários de uma vez, arrastando), legenda editável, PDF abre no visualizador.
- [ ] Prova de não regressão (§8) completa.
- [ ] Código novo comentado (PR6).

## 11. Casos de teste

### Unidade

| # | Arquivo / cenário | Resultado esperado |
|---|-------------------|--------------------|
| 01 | `reaisParaCentavos(0.1 + 0.2)` (0,30000000000000004 em ponto flutuante) | 30 |
| 02 | `quantidadeParaMilesimos(1.4)` | 1400 |
| 03 | `formatarMedidas(700, null, 600)` | "700 × — × 600 mm" |
| 04 | `diferencaCabecalho` com só o desconto mudado | `{ desconto: {...} }` |
| 05 | `orcamentoDetalheSchema` com `inclui_custos: false` e `custo_unit_centavos` presente | Aceita, mas o tipo não expõe o campo (zod remove chaves desconhecidas) |
| 06 | `orcamentoDetalheSchema` com `inclui_custos: true` sem `margem_liquida_bp` | Rejeita |
| 07 | `useFilaOrcamento`: duas escritas seguidas | A segunda sai com a revisão devolvida pela primeira |
| 08 | `useFilaOrcamento`: 409 `REVISAO_DESATUALIZADA` | `conflito = true`; a escrita seguinte nem é enviada |
| 09 | `useSalvamentoAutomatico`: 3 mudanças em 500 ms | Um só `PATCH`, com as 3 |
| 10 | `useSalvamentoAutomatico`: polling chega com campo esperando | Formulário não muda |
| 11 | `useSalvamentoAutomatico`: 422 com `campo: 'desconto'` | Erro no campo; sem nova tentativa |
| 12 | `useSalvamentoAutomatico`: erro de rede | Tenta em 2, 5 e 10 s; depois "Tentar agora" |
| 13 | Rota `/orcamentos/novo`, primeiro campo preenchido | `POST` (não `PATCH`) e `router.replace` |
| 14 | Texto dos avisos com e sem custos | Tabela §6.6; código desconhecido ignorado |

### Componentes

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 15 | `BaseSidebar`, informática | Sem "Orçamentos"; mesma lista de antes (snapshot) |
| 16 | `BaseSidebar`, marcenaria com `view_orcamentos_marcenaria` | "Orçamentos" depois de "Serviços" |
| 17 | `MainLayout`, informática | 4 atalhos iguais aos de hoje |
| 18 | `MainLayout`, marcenaria, pode gerir | "Novo orçamento" no lugar de "Criar OS" |
| 19 | `MovelModal` sem custos | Sem mão de obra, central e custo; o envio não traz essas chaves |
| 20 | `MovelModal`, terceirizada sem central | Erro "Móvel terceirizado precisa da central parceira." |
| 21 | `InsumoBusca`, produto já no móvel | Foco na quantidade da linha; nenhuma linha nova |
| 22 | `InsumoRapidoModal`, preço de venda vazio | `valor_varejo` = custo no `POST /produtos` |
| 23 | `EditorFaixaStatus` em cada status | Texto e botões da §6.3, filtrados por `acoes` |
| 24 | `EnviarModal` sem cliente e sem móvel | Lista as duas pendências, sem a terceira |
| 25 | `CampoPercentualOuValor`: digitar R$ | Modo `VALOR`; o % mostra `desconto_bp_efetivo` da resposta com "≈" (Revisão 1) |
| 26 | `VisaoClienteView` | Nenhum texto de custo, insumo ou preço por móvel |
| 27 | `PositionModal`, informática | Sem a linha nova; "Selecionar tudo" igual a antes |
| 28 | `montarDadosProposta` com detalhe **com** custos | Saída sem nenhuma chave de custo, margem, insumo, parâmetro ou preço por móvel (comparação das chaves, recursiva) |

### Roteiro manual (dev)

1. Marcenaria, master: Configurações › Marcenaria com custo/hora R$ 45,00. Cadastrar "MDF Branco TX 18mm" (sofre perda, última compra R$ 280,00).
2. Menu rápido › Novo orçamento → voltar: a lista continua vazia.
3. Novo orçamento: cliente PJ (consulta de CNPJ da Spec 02), novo projeto "Residencial Alpha Ville - Apto 802".
4. Montar o cenário B da Spec 05 (Cozinha Gourmet com a Torre Quente, desconto 5%, sinal 40%) e conferir **centavo a centavo** os números do resumo com a Spec 05 §11.1.
5. Abrir o mesmo orçamento num segundo navegador, mudar o desconto nos dois: conflito no segundo.
6. Enviar; voltar a editar; enviar; mudar o custo do MDF no cadastro; nova versão → modal "Atualizar preços" com a diferença.
7. Cargo "Vendedor" (ver e gerir orçamentos, sem custos): abrir o orçamento, editar a quantidade de um insumo, salvar; logar como master: a mão de obra continua lá.
8. Visão do cliente; anexar 3 fotos e 1 PDF arrastando; excluir um anexo (aviso das versões).
9. Informática: §8 inteiro.
