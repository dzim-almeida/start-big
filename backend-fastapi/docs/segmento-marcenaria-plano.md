# Plano: segmento Marcenaria (planejados + reforma de móveis)

Escrito em 16/09/2026, na branch `feat/segmento-marcenaria` (criada a partir de
`feat/fiscal-nfe @ 0c64aec`, a linhagem que roda nas lojas). Quarto segmento
depois de informática, oficina mecânica e serigrafia — e o primeiro com **duas
lojas esperando** (uma fábrica de planejados e uma marcenaria de bairro).

O fluxo abaixo é o que o dono da fábrica de planejados descreveu, palavra por
palavra, e é a base de tudo:

```
cliente liga ou vem → solicita orçamento → orçamento aprovado (com % adiantado)
→ compra o material → produção: separação → corte → montagem interna
→ montagem externa (na casa do cliente)
```

A regra que governa este plano é a mesma da serigrafia
(`project_arquitetura_pastas_segmento`): **segmento novo só acrescenta
declaração no registry — se exigir Vue novo, é falta de metadado.** E a
diretriz do dono: crescer **sem nunca quebrar** os três que já rodam.

---

## 0. O que "pronto" significa

O segmento está pronto quando, **nas duas lojas, em produção**, o dono
consegue sozinho:

| # | Critério de aceite | Hoje |
|---|---|---|
| P1 | Cadastrar a empresa como Marcenaria no onboarding | **já funciona** (`'marcenaria'` está em `SEGMENTOS` e em `SEGMENTOS_VALIDOS`) — cai na OS genérica de conserto |
| P2 | Abrir uma OS de **Planejados** com ambiente, módulos, material, acabamento, ferragens, endereço da obra | não existe (sem `definicoes/marcenaria.py`) |
| P3 | Abrir uma OS de **Reforma de móvel** com o móvel e o que fazer | idem |
| P4 | Registrar **% adiantado** na aprovação e ver o saldo na finalização | **já funciona** (`valor_entrada` + `forma_pagamento_entrada_id`; trava `sum(pagamentos) + valor_entrada == valor_total`) — a tela pede valor, não % |
| P5 | Cliente **aprova item a item** o orçamento | capacidade existe (`CAP_APROVACAO_ITENS`, da oficina); não declarada |
| P6 | Ver **em que etapa** está o móvel de um cliente (separação / corte / montagem interna / externa) | não existe |
| P7 | Imprimir a via de entrada e a de saída **sem texto de conserto** ("Peças não retiradas", garantia de reparo) | hoje herdaria o pacote da assistência técnica (`PADRAO = ASSISTENCIA_TECNICA` em `textosImpressaoOS.ts`) |
| P8 | Anexar a **foto do ambiente / projeto / móvel** já na abertura, e ela sair na via de entrada | capacidade existe (`CAP_IMAGEM_NA_ENTRADA`); teste diz "exclusiva da serigrafia por enquanto" |
| P9 | Os três segmentos em produção **continuam idênticos** (tela, impressão, testes) | é a condição de tudo |

P2–P3 e P6–P7 são a obra. P4–P5 e P8 são ligar o que existe. P9 é a prova.

---

## 1. Onde estamos (16/09/2026)

**O que já existe e serve como está:**

- `'marcenaria'` é valor válido nos dois lados (`shared/constants/segmentos.ts`,
  `app/schemas/auth.py`), tem card no onboarding com ícone `Hammer`
  (`useObjetoLabels.ts`) e a dica *"as ordens de serviço com orçamento
  detalhado serão seu principal recurso"* (`sign-in/constants/segments.ts`).
- Como não tem arquivo em `core/segmentos/definicoes/`, `get_definicao_segmento`
  devolve `None`: a loja abre OS genérica (rótulos de conserto, sem objeto de
  serviço, `dados_adicionais` livre) e `segmento_usa_ordem_servico` responde
  `True` pelo padrão.
- Adiantamento, aprovação por item, imagem na entrada, garantia por prazo,
  rótulos de situação por segmento, identificador gerado do nº da OS,
  tipos de trabalho — tudo existe e foi provado na serigrafia (10/08) e na
  oficina.
- Status da OS (fixos, compartilhados): `ABERTA → EM_ANDAMENTO →
  AGUARDANDO_PECAS → AGUARDANDO_APROVACAO → AGUARDANDO_RETIRADA → FINALIZADA /
  CANCELADA`. Rótulo de status **não** varia por segmento (só o da situação
  final varia, via `rotulos_situacao`).
- Tipos de campo do registry: `texto`, `numero`, `inteiro`, `opcao`,
  `booleano`, `lista` (`TIPOS_DE_CAMPO_SUPORTADOS`, `core/segmentos/campos.py`).

**O que o mercado faz** (Calcme, GestorMarceneiro, Planejados Pro, WoodOrça+,
Promob — pesquisa de 16/09): o documento central é o **orçamento por ambiente**
(cliente + endereço da obra → ambientes → módulos com medidas, material,
acabamento, ferragens → mão de obra, frete, montagem → sinal + parcelas + saldo,
validade 15–30 dias, prazo contado da aprovação e do sinal). A produção segue
*medição → projeto → aprovação → compra → corte → usinagem/fitagem → montagem →
acabamento → conferência → instalação*. A **medição** tem checklist (vãos,
pé-direito, prumo, esquadro, pontos de água/luz/gás, fotos) com quem mediu e
quando — é o "vistoria" deles.

---

## 2. O fluxo do dono, sobre a OS que existe

| O dono disse | Na OS | Decisão |
|---|---|---|
| Solicita orçamento | `ABERTA` + itens do catálogo | Serviços/produtos entram pelo catálogo, como na serigrafia: **preço não é do registry** |
| Orçamento aprovado | `AGUARDANDO_APROVACAO` + `CAP_APROVACAO_ITENS` | Ligar. "Aprovou a cozinha, deixou o closet" = item a item |
| % adiantado | `valor_entrada` | Usar como está (valor). Atalho de % é Fase 5 |
| Compra o material | `AGUARDANDO_PECAS` | Fica com esse nome. A **Etapa** carrega "Aguardando material" |
| Separação → corte → montagem interna → montagem externa | nada | Campo `etapa` (opção), com **as palavras dele**. Informação para o dono, sem automação — decisão de 16/09 |
| Montagem externa (na casa do cliente) | a OS não sabe "onde" | Campo `endereco_obra` (texto) no tipo Planejados |
| Entregou / instalou | `FINALIZADA` + `REPARADO` | `rotulos_situacao`: REPARADO → "Entregue", SEM_REPARO → "Não produzido", CONDENADO → "Perda na produção" |

**Duas lojas, dois tipos de trabalho** (mesmo modelo camisa/sacola):

- **Planejados** — ambiente, módulos com medidas, material, acabamento,
  ferragens, endereço da obra, montagem incluída, etapa.
- **Reforma de móveis** — o móvel, o que fazer, peça trazida ou buscar, etapa.
  Aqui "defeito relatado" faz sentido de verdade: é conserto.

O dono acha que a marcenaria de bairro tem o mesmo fluxo. Isso é hipótese até
a segunda loja ler o rascunho (Fase 0).

---

## 3. Decisões já tomadas (conversa de 16/09)

1. Dois tipos de trabalho: **Planejados** e **Reforma de móveis**.
2. **Etapa é campo, não workflow.** Sem automação, sem contagem no dashboard,
   sem filtro na lista. Se o dono pedir "me mostra tudo que está em Corte",
   vira capacidade — depois de medir a demanda.
3. **"Aguardando Peças" fica.** A Etapa diz "Aguardando material". Rótulo de
   status por segmento é mecanismo novo em código compartilhado — só se o dono
   reclamar (Fase 5).
4. **Adiantamento como está** (valor em R$). Atalho de % é melhoria geral
   (serve à oficina também) e entra na Fase 5.
5. **Preço vem do catálogo**, como na serigrafia. Nenhum motor de m² ou de
   chapa no registry — a loja cadastra "Cozinha planejada — metro linear" ou
   "Armário sob medida" em Serviços e o sistema multiplica.

---

## 4. Fases

### Fase 0 — Rascunho para o dono ler (½ dia)

- **0.1** Escrever `app/core/segmentos/definicoes/marcenaria.py` completo
  (anexo A), **sem** somar ao `__init__.py`. Nada muda no sistema.
- **0.2** Gerar uma folha (PDF, 1 página por tipo) com os campos e os rótulos
  nas palavras do dono, para as duas lojas lerem. É o momento em que a sacola
  ganhou "Referências" no lugar de "medida" — a correção barata acontece aqui.
- **0.3** Voltar com a resposta das duas lojas e ajustar o `.py`. Diferença
  entre as duas vira campo de tipo, nunca `if loja`.

### Fase 1 — Ligar o segmento no backend (1 dia)

- **1.1** `definicoes/__init__.py`: import + entrada na tupla. São as duas
  linhas que o próprio arquivo prevê.
- **1.2** `test/core/test_registry_segmentos.py`:
  - os guards existentes (`test_toda_definicao_tem_rotulos_e_identificador`,
    `test_campo_usa_vocabulario_suportado`, `test_campo_de_opcao_declara_opcoes`,
    `test_tipos_de_trabalho_sao_bem_formados`,
    `test_identificador_gerado_nao_e_pedido_ao_usuario`,
    `test_segmento_com_tipos_nao_usa_veiculo_nem_checkin`) já cobram a
    definição nova sem escrever nada;
  - novo `test_ids_dos_tipos_da_marcenaria_sao_contrato_com_o_frontend`
    (espelho do da serigrafia: `planejados`, `reforma_moveis`);
  - `test_imagem_na_entrada_e_exclusiva_da_serigrafia_por_enquanto` → passa a
    dizer "serigrafia e marcenaria", **mantendo** os `not in` de oficina e
    informática. O teste existe para dizer isso em voz alta — a docstring é
    atualizada, não contornada;
  - `test_garantia_por_prazo_segue_ligada_em_quem_conserta`: marcenaria
    declara `CAP_GARANTIA_PRAZO` (decisão §7.2); o teste ganha a linha.
- **1.3** `test/api/v1/test_os_identificador_gerado.py`: caso para o prefixo
  `PRJ` (o código do projeto sai impresso e etiqueta as peças cortadas —
  mesmo motivo do `ART` na tela de serigrafia).
- **1.4** `test_os_forma_pagamento_adiantamento.py` já cobre P4 sem mudança;
  conferir que o caso roda com `segmento='marcenaria'`.
- **Prova:** `pytest test/` inteiro. **Nenhum teste dos três segmentos em
  produção muda de resultado.** Os únicos arquivos tocados são o `.py` novo,
  o `__init__` e os testes acima.

### Fase 2 — Frontend: os três espelhos (1 dia)

Tudo dentro de `modules/order-service/shared/segmento/`:

- **2.1** `textosImpressaoOS.ts`: pacote `MARCENARIA` com `porTipoTrabalho`
  (Planejados × Reforma diferem em `condicoesEntrada`, `prazoRetirada` e
  `garantiaExclusoes`) e entrada em `PACOTES`. **É o item obrigatório** — sem
  ele a marcenaria imprime "Peças com serviço concluído não retiradas" e o
  termo de garantia de conserto. Textos no anexo B.
- **2.2** `useCapacidades.ts`: `FALLBACK_POR_SEGMENTO.marcenaria` e
  `CAMPOS_FALLBACK_POR_SEGMENTO.marcenaria` (evita a aba de imagens piscar
  antes de o contrato chegar). O contrato do backend manda; isto é só o
  carregamento.
- **2.3** `sign-in/constants/segments.ts`: rever a dica do card ("orçamento
  detalhado" → dizer que Planejados e Reforma são tipos da OS e que o preço
  vem do catálogo, como a dica da serigrafia faz).
- **2.4** `npx vue-tsc --noEmit` = 0. Depois, a varredura que o type-check não
  faz (`feedback_vue_tsc_nao_prova_tela`): nenhum componente PascalCase sem
  import no que foi tocado.
- **Prova de P9 (medida, não deduzida):** para cada um dos três segmentos em
  produção, imprimir A4 e cupom de uma OS de exemplo **antes** (`git show
  HEAD:` do arquivo) e **depois**, com a receita do chrome headless
  (`project_comprovantes_perfil`), e comparar. Diferença zero é o critério.

### Fase 3 — Prova no app, em dev (½ dia)

Roteiro, com o backend em `fastapi dev` (porta 8000) e `npm run tauri dev`:

1. Onboarding → Marcenaria. O menu de Serviços aparece (P1).
2. OS de **Planejados**: cliente novo, ambiente Cozinha, 3 linhas de módulos,
   foto do ambiente na abertura, itens do catálogo, adiantamento de 50% em PIX
   → imprimir via de entrada (P2, P4, P8, P7).
3. Aprovar dois itens e reprovar um (P5). Avançar Etapa até "Montagem
   externa" (P6). Finalizar com o saldo; situação "Entregue"; via de saída (P7).
4. OS de **Reforma**: móvel trazido, "Pintura/verniz", sem endereço de obra
   (P3). Cancelar retendo o adiantamento.
5. **Regressão:** abrir uma OS em informática, uma na oficina (com vistoria) e
   uma na serigrafia (camisa) — nada mudou de lugar, nada de texto novo.
6. Reabrir a OS de Planejados finalizada: `credito_anterior` abate do novo
   total (é a parte que mais quebrou no passado —
   `project_desconto_reabertura_os`).

### Fase 4 — Entrega às duas lojas (1 dia de loja + build)

- **4.1** `npm run build:sidecar` (o `.py` novo só chega à loja dentro do
  `erp-api.exe`; `check:sidecar` barra o build se esquecer). Atenção ao teto
  de bytecode do PyArmor (`project_pyarmor_teto_bytecode`): a definição da
  serigrafia passou; comentário não conta, mas uma definição com muitos
  `campo()` pode encostar em ~18k — medir antes de gerar o instalador.
- **4.2** Instalador. Conferir hash do `erp-api.exe` depois de instalar
  (`project_atualizacao_cliente_backend`).
- **4.3** Nas lojas: onboarding, uma OS real de cada tipo, impressão na
  impressora delas (A4 e térmica).
- **4.4** Deixar com cada dono uma folha: "o que você anota no papel que não
  coube aqui?" — é a entrada da Fase 5.

### Fase 5 — Segunda rodada (só depois do feedback; não estimar agora)

Candidatos, em ordem do que o mercado e o fluxo indicam. **Nenhum entra sem
uma loja pedir**, e cada um é código compartilhado (prova medida obrigatória):

- **5.1** Atalho de **%** no adiantamento (botões 30/50%), na tela de
  pagamento da OS. Serve à oficina também — é melhoria geral que a marcenaria
  motivou, não `if marcenaria` em tela compartilhada.
- **5.2** **Rótulo de status por segmento** (`rotulos_status` no registry +
  `ordemServico.constants.ts` ler dele) — só se "Aguardando Peças" incomodar.
- **5.3** **Medidas estruturadas** (L×A×P por módulo, tipo de campo novo em
  `campos.py` + `CampoDinamico.vue`) — só se a fábrica quiser orçar por m²
  dentro do sistema. Hoje `lista` de texto resolve abrir e imprimir.
- **5.4** **Endereço da obra estruturado** (CEP, rota para o montador) — hoje
  texto livre.
- **5.5** **Filtro/contagem por Etapa** na lista e no dashboard — é o
  momento em que Etapa vira capacidade.
- **5.6** **Medição como vistoria** (`CAP_VISTORIA` com o checklist de
  ambiente: vãos, pé-direito, prumo, pontos de água/luz/gás) — a oficina já
  tem o mecanismo; falta o checklist declarado. Interessa mais à fábrica.

---

## 5. Ordem e custo

| Ordem | Fase | Custo | Depende de |
|---|---|---|---|
| 1 | 0 (rascunho + folha para os donos) | ½ d + resposta das lojas | — |
| 2 | 1 (backend) | 1 d | Fase 0 |
| 3 | 2 (frontend + prova medida dos 3) | 1 d | — (pode andar em paralelo com a 1) |
| 4 | 3 (prova em dev) | ½ d | 1 e 2 |
| 5 | 4 (sidecar, instalador, lojas) | 1 d de loja + build | 3 |
| 6 | 5 (segunda rodada) | por item, depois do feedback | 4 |

**Total de código: ~3 dias.** O resto é conversa com os donos e prova em
loja. A Fase 0 é a que mais economiza: um campo errado descoberto no papel
custa uma linha; descoberto na loja custa sidecar + instalador + visita
(`project_informatica_producao`).

Tudo sai **desta branch**. O instalador continua saindo da linhagem da
oficina/fiscal — sem cherry-pick para o master
(`project_branch_oficina_isolada`).

---

## 6. O que NÃO entra

- **Orçamento automático por m² / por chapa / plano de corte.** O catálogo
  resolve o preço (decisão §3.5), como resolveu na serigrafia depois de um
  motor de faixas ter sido desenhado e cortado. Sistemas que fazem isso
  (Promob, Calcme) são de projeto, não de balcão.
- **Integração com Promob/CAD.** Outro produto.
- **PCP / fila de máquinas / cronograma de produção.** A Etapa é informação
  para o dono; produção é decisão dele no chão da fábrica.
- **Validade do orçamento (15–30 dias) e "prazo conta do sinal".** O mercado
  faz; a OS não tem o conceito. Fica para depois de alguma loja pedir — e aí é
  regra de OS, não de segmento.
- **Contrato / assinatura digital.** A via impressa com aceite do cliente é o
  que as duas lojas usam hoje.
- **Setores como pessoas** (quem está com o móvel). `Responsável` é um por OS;
  ver §7.1.

---

## 7. Decisões em aberto (são do dono)

1. **Quem executa cada etapa?** Os "setores" (corte, montagem interna, externa)
   são pessoas diferentes. Basta a Etapa, ou ele quer o **nome** de quem está
   com o móvel? Se quiser, a saída barata é um campo `texto` "Setor / responsável
   da etapa" ao lado da Etapa — não mexe no `Responsável` da OS (que é quem
   responde pelo serviço e recebe comissão).
2. **Garantia por prazo ligada?** Marcenaria dá garantia (90 dias é comum;
   planejados às vezes 1 ano). Recomendação: **ligar** (`CAP_GARANTIA_PRAZO`),
   com o texto de exclusões próprio (umidade, cupim, mau uso, alteração por
   terceiros). Se não ligar, a via de saída sai sem Termo de Garantia.
3. **Lista de ambientes** (Cozinha, Dormitório, Closet, Banheiro, Sala,
   Escritório, Área de serviço, Outro) — confirmar com a fábrica. Texto livre
   viraria "cozinha", "Cozinha", "COZ" — enum aqui é o certo.
4. **A marcenaria de bairro tem mesmo o mesmo fluxo?** É a hipótese do dono da
   fábrica. Quem responde é a segunda loja, na Fase 0.
5. **Imagem na entrada vale para Reforma também?** Capacidade é por segmento,
   não por tipo. Em Planejados a foto é o pedido (ambiente/projeto); em
   Reforma é prova do estado do móvel — e ir para a via de entrada é **bom**
   (o cliente assina vendo a foto). Recomendação: ligar para o segmento todo.

---

## 8. Riscos

- **Código compartilhado.** `textosImpressaoOS.ts` e `useCapacidades.ts` são
  lidos pelos três em produção. O risco não é o pacote novo, é a mão escorregar
  no `PADRAO` ou num pacote vizinho. A prova antes × depois da Fase 2 existe
  para isso.
- **Opções gravadas.** Renomear uma opção de `etapa` depois que uma OS gravou
  o valor deixa a OS antiga com valor fora da lista (a serigrafia manteve
  "Mileiro" e "Vazada" no fim da lista por esse motivo). Acertar os nomes na
  Fase 0.
- **Uso real acha o que teste não acha** (`feedback_uso_real_acha_defeito`):
  1293 testes não pegaram o Salvar que travava. A Fase 3 é obrigatória, não
  opcional.
- **Sidecar velho.** O `.py` novo não chega à loja sem `build:sidecar`; o
  sintoma seria "o onboarding aceita Marcenaria mas a OS continua de conserto".
- **PyArmor.** Definição grande pode estourar o teto de bytecode do módulo;
  medir antes do instalador.

---

## Anexo A — Rascunho da definição (para a Fase 0; ainda não é código ligado)

```
SEGMENTO: marcenaria
rótulo do objeto:        Projeto / Projetos
rótulo do defeito:       Descrição do pedido
placeholder:             Ex: cozinha planejada, MDF branco, 4 módulos + bancada
rótulo do responsável:   Responsável
situação:                Situação do Projeto
  REPARADO  → Entregue
  SEM_REPARO → Não produzido
  CONDENADO → Perda na produção
identificador:           codigo_projeto, gerado, prefixo PRJ  (etiqueta as peças cortadas)
capacidades:             aprovacao_itens, imagem_na_entrada, garantia_prazo
veiculo/checkin/acessorios/vistoria: vazios (declara por tipo)

TIPO planejados — "Móveis planejados"
  [objeto] nome_projeto       texto, obrigatório, coluna=modelo   "Nome do projeto" (ex: Cozinha apto 302)
  [objeto] endereco_obra      texto, inteira                     "Endereço da obra"
  [os]     ambiente           opção: Cozinha, Dormitório, Closet, Banheiro, Sala, Escritório, Área de serviço, Outro
  [os]     modulos            lista, inteira                     "Módulos (um por linha, com medida)"
  [os]     material           texto                              "Material / chapa"      (ex: MDF 15mm branco TX)
  [os]     acabamento         texto                              "Acabamento / cor"
  [os]     ferragens          texto, inteira                     "Ferragens e puxadores"
  [os]     montagem_incluida  booleano                           "Montagem incluída"
  [os]     etapa              opção: Aguardando aprovação, Aguardando material, Separação, Corte,
                                     Montagem interna, Montagem externa, Concluído

TIPO reforma_moveis — "Reforma de móveis"
  [objeto] nome_projeto       texto, obrigatório, coluna=modelo   "Móvel"  (ex: Guarda-roupa 3 portas)
  [os]     servico_reforma    opção: Restauração, Troca de peça, Pintura / verniz, Ajuste, Outro
  [os]     material           texto                              "Material"
  [os]     acabamento         texto                              "Acabamento / cor"
  [os]     movel_trazido      booleano                           "Móvel trazido pelo cliente"  (senão, buscar)
  [os]     etapa              opção: Aguardando aprovação, Aguardando material, Separação, Corte,
                                     Montagem interna, Concluído
```

Grupos: "Dados do Projeto" (objeto), "Especificação" (material/acabamento/
ferragens), "Produção" (etapa, montagem). Larguras: `modulos`, `ferragens`,
`endereco_obra` inteiras; o resto meia.

## Anexo B — Pacote de textos de impressão (esqueleto)

```
objeto: 'móvel'            objetoPlural: 'Móveis'         empresa: 'A empresa'
tituloObjeto: 'Dados do Projeto'    identificador: 'Projeto'   defeito: 'Descrição do Pedido'
assinaturaLoja: 'Responsável'
garantiaExclusoes: umidade e infiltração, cupim, mau uso, sobrecarga, alteração ou
                   montagem por terceiros, desgaste natural de acabamento.
condicoesEntrada (planejados): medidas conferidas no local pelo responsável; alterações
                   após aprovação geram novo orçamento; prazo conta da aprovação e do
                   adiantamento; montagem externa exige ambiente pronto e livre.
condicoesEntrada (reforma):    o cliente declara o estado do móvel conforme fotos; peças
                   de terceiros sob responsabilidade do cliente.
prazoRetirada (reforma):       "Móveis não retirados em N dias após aviso de conclusão…"
prazoRetirada (planejados):    não se aplica — entrega/montagem na obra (texto de
                   agendamento de montagem no lugar).
cupom: mesmas chaves, encurtadas.
```

Redigir os textos finais com os donos na Fase 0 — o `condicoesEntrada` é o que
eles assinam, então as palavras são deles.
