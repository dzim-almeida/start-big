# Spec 00 — Registro de Decisões do Segmento Lava-Rápido

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Aprovado (Revisão 2); Revisão 4 (interface própria) aprovada em 12/11 — 🟡 de U3, U4 e U5 com o usuário |
| Camada       | Documento                                                             |
| Dependências | Nenhuma                                                               |
| Bloqueia     | Todas as specs do lava-rápido (01 a 07)                               |
| Referência   | Conversa de 12/11/2026; pesquisa de mercado (§3.2); `docs/marcenaria/SPEC-00` (formato e princípios) |
| Branch       | `feat/segmento-lava-rapido` @ `c2228e88` (saiu da `feat/cfop-na-nota`) |

> **Revisão 4 (12/11/2026, tarde) — interface própria.** Ao abrir o app com a 01B, o usuário viu a OS de abas (feita para conserto) e não aprovou: "não tô achando legal reutilizar as coisas de oficina de carro". A pesquisa da §3.3 confirmou: **nenhum** sistema do ramo usa formulário de OS — o centro de todos é a **comanda rápida** e a **tela do dia (pátio)**. Decisões U1–U6 (§6.5). O que muda: o lava-rápido ganha módulo próprio `modules/lava-rapido/` com **Pátio** (tela principal), **Nova entrada** (comanda de uma tela) e **Agenda**; a OS de abas vira só "ver detalhes". O que **não** muda: cada lavagem continua sendo uma OS no banco (PR2) — caixa, financeiro, relatórios, comissão e nota funcionam sem refazer nada —, e 01A/01B continuam valendo (registry, status, placa-ou-gerado, impressão). A ordem dos marcos muda (PLANO §3): comanda e pátio vêm antes da agenda.

> **Revisão 3 (12/11/2026) — organização das specs, ao escrever a 01A.** A 01A fica **só com a fundação do segmento** (registry, status, identificador — sem tabela nova). Lavadores da OS e comissão (O7a, O7c) passam para as **Specs 10A/10B**, ainda no Marco 1: mexem no relatório de comissão de todas as lojas e merecem prova de não regressão própria. As capacidades novas entram cada uma na spec que a implementa (nunca antes: metadado órfão). Decisões técnicas da 01A: placa **sem regex** no lava-rápido (D4) e chave `identificador.gerado_se_vazio` (D5); O2b mantém "Aberta / Em Andamento / Finalizada" com o texto padrão e só renomeia Aguardando Retirada → **"Pronto"** (01A D10).
>
> **Revisão 2 (12/11/2026) — usuário.** **O2b:** o segmento usa **quatro** status — Aberto, Em andamento, **Pronto** (o `AGUARDANDO_RETIRADA` de sempre, renomeado) e Finalizado; o WhatsApp é sugerido ao marcar "Pronto". **O7c:** com 2 lavadores, **o dono decide** no cadastro dos funcionários se a comissão é **dividida** ou **inteira para cada um** (cascata funcionário → cargo, como o modo de comissão de hoje). Substituem O2a e O7b.
>
> **Revisão 1 (12/11/2026) — respostas do usuário e do primeiro cliente.**
> **Usuário:** F1 ✅ (nome "Lava-Rápido / Estética Automotiva"); **O2a** (status reduzidos a **Aberto / Em andamento / Finalizado**); **O11** (nova aba **Agenda** em Serviços, entra na fase 1); **C1a** (qualquer usuário altera o preço na OS); O8 ✅ (WhatsApp por link); ordem dos marcos ✅, com a Agenda logo depois do pátio; branch própria do segmento ✅ (`feat/segmento-lava-rapido`; o instalador sai dela).
> **Cliente (o primeiro, 2 pessoas na loja):** lava **qualquer transporte** → **P4a** (tipo "Outros", placa opcional); cobra por porte e cadastra no serviço → P1 ✅, **P2a** (lista de portes editável pela loja); **não** usa plano, pacote, fidelidade nem frota hoje → C3 e C4 ficam no plano para os **próximos** clientes, depois da Agenda; **O7a** (quem abre a OS é o responsável, e a OS identifica **1 ou 2 lavadores**); impressão **térmica e A4/PDF** (O10a); não emite nota hoje, mas o segmento já sai preparado → **C5a** (Spec 09).
> Mudam: §6, §7 (agendamento e lavadores saem do "fora"), §8 (specs 08 e 09 novas) e §10 (respondida).

---

## 1. Objetivo

Registrar, em um só lugar, **tudo o que foi combinado** sobre o segmento lava-rápido (carro, moto, caminhão e ônibus) antes de escrever qualquer spec de código. Toda spec seguinte cita as decisões deste documento pelo código (ex.: "P1", "O3") em vez de repetir o raciocínio.

**Critério de pronto da fase 1:** o primeiro cliente (já fechado em 12/11/2026) roda um dia inteiro de pátio pelo sistema — entrada pela placa, preço pelo porte, vistoria com foto, quadro do pátio, aviso de "pronto" e finalização com pagamento — e os segmentos em produção (informática, oficina, serigrafia, PDV, marcenaria) seguem **idênticos**.

## 2. Escopo

**Dentro do escopo**
- Princípios que valem para todas as specs (§4).
- Decisões de negócio e de experiência do usuário, por bloco (§6).
- O que fica fora da fase 1 (§7).
- Lista de specs, ordem e dependências (§8).

**Fora do escopo**
- Código, contratos de API e telas: cada spec cuida do seu.
- Valores da tabela de preços do cliente (ele cadastra os dele).
- Enquadramento fiscal do serviço (item da LC 116 e alíquota de ISS): **confirmar com o contador do cliente** antes da primeira NFS-e.

---

## 3. Contexto

### 3.1. O que já existe e é reaproveitado

| Peça | Onde | Uso no lava-rápido |
|------|------|--------------------|
| Registry de segmentos (dado × motor): campos, tipos de trabalho, capacidades, rótulos de status | `app/core/segmentos/` | O segmento nasce como **um arquivo** `definicoes/lava_rapido.py` (F1) |
| Placa como identificador, com regex Mercosul | `definicoes/oficina.py` (`PLACA_REGEX`) | Mesma regex (F2): cobre carro, moto e caminhão |
| Busca da OS pela placa, com o veículo já escolhido (`objetoPreSelecionado`) | `ordens/composables/useOSCreateFlow.ts` | Base da entrada rápida (O1) |
| Vistoria por grupos (OK / N_OK / REPARAR) | capacidade `vistoria` + `grupo_vistoria` | Avarias da entrada (O5) |
| Fotos na criação da OS e na via de entrada | capacidade `imagem_na_entrada` | Fotos das avarias antes de lavar (O5) |
| Checklist pelo celular (QR + token HMAC) | `endpoints/checklist_mobile.py` | O lavador fotografa e marca a vistoria no pátio (O5) |
| Responsável da OS (`ordens_servico.funcionario_id`) + comissão sobre serviço por funcionário/cargo | `db/crud/relatorio/equipe.py` | Comissão do lavador sem código novo (O7) |
| `ordens_servico.data_previsao` | modelo da OS | Previsão de entrega do quadro (O4) |
| `objetos_servico.proxima_revisao_data` + módulo `revisoes` | modelo do objeto, `order-service/revisoes/` | Lembrete de retorno (O9) |
| Rótulos de status por segmento (`rotulos_status`) | registry (Spec 01A da marcenaria) | "Na fila", "Lavando", "Pronto" (O2) |
| Quadro de produção (abrir a OS numa aba, ações rápidas) | Spec 12B da marcenaria, `openExistingOS(os, { abaInicial })` | Padrão visual do quadro do pátio (O3) |
| PDV, estoque, caixa, financeiro, NFS-e | módulos existentes | Venda de produto no balcão, pagamento, nota de serviço |

### 3.2. O que o mercado faz (pesquisa de 12/11/2026)

Sistemas olhados: Jump Car, Lava já!, SisJato, Brilha Car, WashAI, ClickLava, Wüst, WSoft, GestãoClick, Lavify; fora do Brasil, DRB, Washify, WashCard. São páginas de venda — o que listam é o que **vendem**, não o que foi testado.

| Recurso | Quem anuncia | Entra aqui? |
|---------|--------------|-------------|
| **Preço por porte**: um serviço, um preço (e duração) por porte — hatch, sedã, SUV, caminhonete | GestãoClick, guias Tlimm e Lavify | **Sim, fase 1** (P1) |
| Check-in pela placa | SisJato, Lava já!, WashAI (com câmera/OCR) | Sim, digitada (O1); OCR fora (§7) |
| Fila / controle de pátio em tempo real | Wüst, WSoft, Lava já! | **Sim, fase 1** (O3) |
| Checklist de avarias com foto (e vídeo) | Jump Car, Brilha Car, Lava já!, Lavify | Sim, foto (O5); vídeo fora (§7) |
| WhatsApp (carro pronto, lembrete) | SisJato, Brilha Car, ClickLava | Sim, por link `wa.me` (O8); API e campanhas fora (§7) |
| Comissão por lavador | Jump Car, Wüst, WSoft | Sim, com 1 ou 2 lavadores por OS (O7a, O7c) |
| Pacotes, mensalista, fidelidade, cashback | Wüst, Lava já!, Lavify, LavaX (assinatura por porte) | Sim, **opcional por loja** (C3) |
| Convênio com empresa / frota faturada | Lavify, sistemas de frota | Sim, fase 2 (C4) |
| Agendamento | Jump Car, SisJato, Agende-Lave | Agenda interna **sim** (O11, Revisão 1); link público para o cliente agendar sozinho fica fora (§7) |
| Lembrete de retorno | Brilha Car, ClickLava | Sim (O9) |

Conclusão que guia as decisões: o que **todo** sistema do ramo tem é placa + preço por porte + fila + avaria com foto + WhatsApp. Isso é a fase 1. Fidelidade e mensalista são diferencial de venda e ficam **desligados por padrão** (o dono liga se usar — decisão do usuário, 12/11).

### 3.3. Como é a tela nos sistemas do ramo (pesquisa de 12/11/2026, tarde — Revisão 4)

Lidas as páginas de Garage/oficina.app, Jump Car e Lavacar Fácil (Lava já! fora do ar), mais Lavify, WSoft, Pretinho, WashAI, Elyxa, Purific Car e Urable. Ainda são páginas de venda.

| Ponto | Como fazem | O que tiramos |
|-------|-----------|---------------|
| Entrada | **Comanda** aberta "em poucos toques", no celular ou no balcão, com o carro ainda chegando (Garage); placa por foto/OCR (Lava já!, Jump Car) | Comanda de **uma tela** (U2); OCR continua fora (§7) |
| Dia de trabalho | Tela "Hoje" (Lavacar Fácil), "pátio em tempo real" (Lava já!); o cliente vê "carro em acabamento" | **Pátio é a tela principal** (U1) |
| Avarias | Checklist com fotos antes de lavar; Jump Car marca num **mapa das áreas**; Lavacar Fácil faz checklist de **entrada e saída** com assinatura | Checklist simples **por tipo de veículo**, com foto (U4) |
| Comissão | Liga quem lavou a cada serviço e calcula no fechamento (Garage, Jump Car); ninguém mostra divisão entre dois lavadores | O7c (Dividir/Inteira) é diferencial |
| WhatsApp | De nenhum (Garage: PDF à mão) a aviso automático de início e fim com as avarias (Jump Car) | `wa.me` no "Pronto" (O8) |
| Agenda | Link do cliente, bloqueio de horário, fila de espera, agenda por box e hora | Aba do módulo (U1); link público fora (§7) |
| Caixa e nota | Caixa do dia, PIX/cartão/maquininha, NFS-e | Já temos — vantagem nossa |

Conclusão: o formulário longo é exatamente o que esses sistemas vendem como "não precisa mais". Nossa vantagem real: comissão dividida, nota fiscal pronta e funcionar **local, sem internet**.

---

## 4. Princípios (valem para todas as specs)

Os mesmos da marcenaria (SPEC-00 da marcenaria, §4), adaptados:

| # | Princípio | Consequência prática |
|---|-----------|----------------------|
| PR1 | **Não quebrar o que funciona.** Informática, oficina, serigrafia, PDV e marcenaria continuam idênticas | Toda spec que toca código compartilhado (⚠️) tem a seção "Prova de não regressão" |
| PR2 | **A OS é o documento do lava-rápido.** Cada lavagem é uma OS comum | Nenhum status novo de OS, nenhuma tabela de OS paralela. Pagamento, reabertura, cancelamento e impressão seguem como estão |
| PR3 | **Padrões do StartBig** | SQLite síncrono, id inteiro, `HTTPException` com `detail`, camadas `endpoints → services → crud → models`, VeeValidate + Zod, TanStack Query |
| PR4 | **Dinheiro em centavos (`int`), percentual em basis points** | Nada de `float` em dinheiro |
| PR5 | **Uma camada por spec** | "A" = backend, "B" = frontend |
| PR6 | **Código em português e comentado** (CLAUDE.md) | Trechos das specs comentados linha a linha |
| PR7 | **Backend mexeu → sidecar de novo** | Toda spec A termina com `npm run build:sidecar` e o teto de 64 KB por arquivo do PyArmor trial |
| PR8 | **Migrações decidem pela presença do schema antigo** e **sem bifurcação** | `alembic heads` antes de cada migração; reencadear, nunca `alembic merge` |
| PR9 | **Recurso novo nasce por capacidade.** Nada de `if segmento == "lava_rapido"` | Ligar no lava-rápido = uma linha no registry; outro segmento pode ligar depois |
| PR10 | **Rapidez é requisito.** O pátio não espera | Toda tela B mede o caminho do atendente (cliques/tempo) no roteiro manual |

---

## 5. Glossário

| Termo | Definição |
|-------|-----------|
| Veículo | Objeto de serviço da OS do lava-rápido (placa, marca, modelo, cor, porte) |
| Porte | Categoria do veículo que define o **preço** e a **duração** do serviço (ex.: Hatch, SUV, Caminhão 3 eixos). Declarado no registry |
| Tabela de preço por porte | Para cada serviço, um preço (e duração) por porte. Sem linha para o porte, vale o preço padrão do serviço |
| Pátio | Os veículos que estão na loja hoje: na fila, lavando, prontos |
| Quadro do pátio | Tela com o pátio em colunas por status |
| Lavador | Funcionário responsável pela OS (`funcionario_id`) |
| Vistoria de entrada | Avarias registradas (com foto) antes de lavar |
| Plano mensal | Assinatura do cliente para uma placa: N lavagens (ou ilimitadas) por mês, por um valor fixo |
| Pacote | Lavagens pré-pagas (ex.: 10 lavagens), consumidas até acabar |
| Cartão fidelidade | A cada N lavagens pagas, uma grátis |
| Frota / convênio | Cliente PJ com várias placas, cobrado no fechamento do mês |

---

## 6. Decisões

Legenda da coluna **Status**: ✅ decidida pelo usuário · 🟡 recomendada (confirmar na revisão desta spec) · ❓ depende de resposta do cliente.

### 6.1. Fundação

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| F1 | Valor do segmento: `lava_rapido`; nome na tela: **"Lava-Rápido / Estética Automotiva"**. Entra em `SEGMENTOS` (`frontend/src/shared/constants/segmentos.ts`), `SEGMENTOS_VALIDOS` (`app/schemas/acesso/auth.py`), card e dica do onboarding (`sign-in/constants/segments.ts`) e `definicoes/__init__.py` | As listas são espelhadas; faltar uma foi o que derrubou o onboarding da serigrafia | ✅ |
| F2 | Objeto = **Veículo**; identificador = **placa** (`PLACA_REGEX` importada da oficina, não copiada), coluna `numero_serie`; marca/modelo/cor nas colunas reais | Mesmo desenho da oficina, que já está em produção | 🟡 |
| F3 | Três **tipos de trabalho**: **Carro**, **Moto**, **Pesado** (caminhão, ônibus, van grande). Cada um com seus campos (§6.2) e seus portes | O formulário muda conforme o veículo, como camisa × sacola na serigrafia | 🟡 |
| F4 | Tabelas novas com nome **genérico** (não `lava_*`) quando servem a qualquer segmento: `servico_precos_porte`, `planos_cliente`… Toda leitura ligada por capacidade (PR9) | Preço por porte e plano mensal servem a outros ramos (estética, pet shop); o nome do segmento no banco amarraria a peça a ele | 🟡 |
| F5 | **Nenhuma coluna nova em tabela existente** na fase 1, exceto se uma spec A justificar (como a `origem` da marcenaria) | Menor risco nas lojas em produção (PR1) | 🟡 |

### 6.2. Veículo e porte

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| P1 | **Preço por porte**: cada serviço tem uma tabela "porte → preço (e duração)". Ao incluir o serviço na OS, o sistema usa o preço do porte do veículo; sem linha para aquele porte, usa o `servicos.valor` (preço padrão). O atendente **pode alterar** o valor na OS, como hoje | É o padrão do mercado (§3.2). Cadastrar "Lavagem – SUV", "Lavagem – Hatch"… como serviços separados multiplica o catálogo por 10 e erra no balcão | ✅ (cliente: "cadastro no serviço, tranquilo") |
| P2 | ~~Portes fixos no registry.~~ **Revista por P2a.** | — | — |
| P2a | **Revisão 1:** a **lista de portes é da loja** (tabela `portes_veiculo`: nome, tipo de veículo, ordem, ativo), editável em Configurações › Serviços. O registry só traz a **lista inicial**, gravada na primeira vez que o segmento é usado — **Carro:** Hatch / Sedã / SUV / Picape / Van-utilitário · **Moto:** Até 300 cc / Acima de 300 cc · **Pesado:** Caminhão 2 eixos / 3 eixos / 4 eixos / 5 eixos ou mais / Ônibus-micro · **Outros:** Pequeno / Médio / Grande. Porte desativado some das escolhas, mas continua nos veículos e preços que já o usam | Cada lava-rápido divide os portes de um jeito (P/M/G, hatch/sedã, por eixo); lista fixa no código obrigaria a gerar um instalador para trocar um nome | 🟡 |
| P3 | O porte é **do veículo** (`objetos_servico.dados_adicionais.porte`), não da OS: na segunda visita já vem preenchido | O carro não muda de porte entre uma lavagem e outra | 🟡 |
| P4 | Campos por tipo — **Carro:** placa*, marca, modelo, cor, porte* · **Moto:** placa*, marca, modelo, cor, porte* · **Pesado:** placa*, marca, modelo, cor, porte*, carroceria (Baú / Sider / Graneleiro / Tanque / Cegonha / Outro), implemento/2ª placa (texto). Na OS (check-in): pertences deixados no veículo (texto), observação de entrada | O caminhão é lavado com carroceria; a 2ª placa da carreta é comum | 🟡 |
| P4a | **Revisão 1:** quarto tipo **"Outros"** (barco, jet ski, máquina agrícola, trailer, bicicleta): descrição*, marca, modelo, cor, porte*; **placa opcional**. Sem placa, o identificador é **gerado** a partir do número da OS (mecanismo da serigrafia, `gerar_identificador`). A Spec 01A confere se o identificador do segmento pode ser "placa quando houver, gerado quando não" sem mexer na oficina | O cliente lava "qualquer transporte" | 🟡 |
| P5 | **Duração** por porte (minutos), opcional, na mesma tabela de P1 | Alimenta a previsão de entrega (O4) | 🟡 |

### 6.3. Operação do pátio

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| O1 | **Entrada rápida**: placa → (veículo e dono já aparecem) → serviços → salvar. Meta: **≤ 30 s e ≤ 6 cliques** para cliente que já veio; placa nova abre o cadastro mínimo (nome + telefone) sem sair da tela | PR10. A busca pela placa já existe (`objetoPreSelecionado`); falta enxugar o formulário para o segmento | 🟡 |
| O2 | Rótulos de status: ABERTA → **"Na fila"**; EM_ANDAMENTO → **"Lavando"**; AGUARDANDO_RETIRADA → **"Pronto"**; FINALIZADA → **"Entregue"**. AGUARDANDO_PECAS e AGUARDANDO_APROVACAO **não aparecem** nos botões e filtros do segmento | Linguagem do pátio. Esconder status é mecanismo novo (o registry só renomeia hoje): vai na Spec 01A, por chave declarada, sem tocar nos outros segmentos | Revista por O2a |
| O2a | **Revisão 1:** o segmento usa **só três status**: ABERTA → **"Aberto"**, EM_ANDAMENTO → **"Em andamento"**, FINALIZADA → **"Finalizado"** (CANCELADA continua existindo pelo cancelamento de sempre). AGUARDANDO_PECAS, AGUARDANDO_APROVACAO e AGUARDANDO_RETIRADA **não aparecem** em botões, filtros e quadro. Mecanismo: chave opcional `status_usados` no registry (Spec 01A); quem não declara recebe a lista de hoje | Decisão do usuário: o pátio só precisa saber se o carro está esperando, sendo lavado ou entregue | Revista por O2b |
| O2b | **Revisão 2:** **quatro** status: ABERTA → **"Aberto"**, EM_ANDAMENTO → **"Em andamento"**, AGUARDANDO_RETIRADA → **"Pronto"**, FINALIZADA → **"Finalizado"**. AGUARDANDO_PECAS e AGUARDANDO_APROVACAO não aparecem (chave `status_usados`, Spec 01A). Nenhum status novo no enum: os valores gravados são os de sempre | O "Pronto" separa o carro lavado esperando o dono do carro entregue e pago — é o momento do WhatsApp | ✅ |
| O3 | **Quadro do pátio** (aba em Serviços, por capacidade `quadro_patio`): colunas **Aberto / Em andamento / Pronto / Finalizado hoje**, com as OS abertas (de hoje e as que ficaram de ontem); cartão com placa, modelo, porte, serviços, lavadores, tempo no pátio e previsão; avança o status com um clique; atualiza sozinho a cada 30 s | É o recurso que todo sistema do ramo anuncia (§3.2). Segue o padrão do quadro de produção da marcenaria | 🟡 |
| O4 | **Previsão de entrega** = abertura + soma das durações dos serviços (P5), gravada em `data_previsao` (coluna que já existe) e editável. Sem duração cadastrada, fica em branco | Responde "que horas fica pronto?" sem conta de cabeça | 🟡 |
| O5 | **Vistoria de entrada** com a capacidade `vistoria` e grupos próprios — **Externa:** riscos, amassados, para-brisa/vidros, faróis/lanternas, rodas/calotas, retrovisores, pintura queimada/oxidada · **Interna:** bancos/estofado, painel, tapetes, manchas/odores, objetos de valor · e `imagem_na_entrada` para fotos. Celular pelo QR (checklist mobile) | Reclamação de risco é a maior dor do ramo; foto antes de lavar é a defesa da loja | 🟡 |
| O6 | Lava-rápido **não** declara `diagnostico`, `garantia_prazo`, `garantia_itens`, `aprovacao_itens` nem `revisoes` por KM | Não há conserto, peça, laudo nem garantia em dias | 🟡 |
| O7 | **Lavador** = responsável da OS (`funcionario_id`). A comissão sobre serviço que já existe (funcionário → cargo) paga o lavador sem código novo. **Dividir uma OS entre dois lavadores fica fora da fase 1** (exigiria funcionário por item) | Reaproveita o que está em produção | Revista por O7a |
| O7a | **Revisão 1:** **responsável** da OS = quem abre (`funcionario_id`, como hoje). Além dele, a OS identifica os **lavadores** (1 ou 2; a tabela aceita mais) em tabela nova e genérica `ordem_servico_executores` (OS, funcionário), ligada pela capacidade `executores_os`. Os lavadores aparecem no formulário, no quadro e na impressão | Pedido do cliente: na loja pequena quem abre também lava; na grande, o atendente abre e dois lavadores executam | ✅ |
| O7b | **Comissão com lavadores:** a comissão de serviço passa a ir para os **lavadores**, dividida em partes iguais; sem lavador informado, vai para o responsável (como hoje). Só no segmento que declara `executores_os`; o relatório de comissão dos outros segmentos não muda | Quem lava é quem ganha por lavagem no ramo | Revista por O7c |
| O7c | **Revisão 2 — o dono decide.** Cada lavador continua com o **percentual de comissão de serviço** que já existe no funcionário/cargo (vazio = sem comissão; loja que não paga comissão não configura nada). Novo: **"Quando a lavagem tiver mais de um lavador"** → **Dividir** (cada um recebe o seu % sobre a sua parte: valor ÷ nº de lavadores) ou **Inteira** (cada um recebe o seu % sobre o valor todo). Fica no cadastro do **cargo** e pode ser trocada no **funcionário** (cascata funcionário → cargo → padrão **Dividir**, igual ao `comissao_modo` de hoje). Aparece só no segmento com `executores_os`. Sem lavador na OS, a comissão vai para o responsável, como hoje. A Spec 01A decide onde gravar (coluna nula em `cargos`/`funcionarios`, exceção registrada a F5, ou tabela própria) | Pedido do usuário: cada lava-rápido paga de um jeito, e quem decide é o dono | ✅ (regra) · 🟡 (onde gravar) |
| O8 | **Aviso pelo WhatsApp**: botão no cartão do quadro e na OS que abre `https://wa.me/55<telefone>?text=<mensagem>` com texto editável em Configurações (padrão: "Olá, {cliente}! Seu {veiculo} placa {placa} está pronto."). Sem API, sem custo, sem envio automático. Ao marcar **"Pronto"** (O2b), o sistema pergunta "Avisar o cliente pelo WhatsApp?" | O que o ramo mais pede; a API oficial custa por mensagem e exige conta comercial | ✅ |
| O9 | **Lembrete de retorno**: ao finalizar, `proxima_revisao_data` do veículo = hoje + N dias (configurável, padrão 30; 0 desliga). A lista do módulo Revisões mostra quem está "vencido", com o botão de WhatsApp de O8 | Reaproveita coluna e tela que existem; KM é ignorado no segmento | 🟡 (conferir na Spec 07 se a tela de Revisões funciona sem KM) |
| O10 | **Impressão**: cupom/ticket de entrada curto (placa, serviços, previsão, avarias marcadas) na térmica, e via de saída com a assinatura de retirada. Textos próprios em `textosImpressaoOS.ts` | O cliente sai com comprovante; a avaria marcada na via protege a loja | 🟡 |
| O10a | **Revisão 1:** as duas saídas que a OS já tem — **térmica** (`osToEscPos.ts`) e **A4/"Salvar como PDF"** (`OSPrintTemplate.vue`) — ganham o conteúdo do lava-rápido (porte, lavadores, avarias). O primeiro cliente não imprime; os próximos escolhem | Pedido do usuário pensando nos próximos clientes | ✅ |
| O11 | **Revisão 1 — Agenda** (aba própria em Serviços, capacidade `agenda_servicos`, como as abas Instalações e Revisões): agendamento com dia, hora, cliente, placa/veículo (ou só nome e telefone se for novo), serviços e duração prevista (pelo porte, P5); visão do **dia** em horários e da **semana**; aviso, sem trava, quando o horário passa da capacidade da loja (nº de boxes/vagas em Configurações); situações *Agendado → Chegou → Não veio / Cancelado*; **"Chegou" abre a OS** já preenchida pelo caminho da entrada rápida (O1); botão de WhatsApp de confirmação (O8). Tabela nova e genérica `agendamentos` | Pedido do usuário. A agenda da marcenaria não serve: ela agenda uma OS que já existe, e aqui o agendamento vem **antes** da OS | 🟡 (desenho) |

### 6.4. Comercial

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| C1 | Preço da OS sai de P1; desconto e acréscimo seguem como hoje | Nada novo no fechamento | ✅ |
| C1a | **Revisão 1:** **qualquer usuário** que está usando o sistema pode alterar o preço do item na OS (sem permissão extra) | Decisão do usuário | ✅ |
| C2 | Venda de produto no balcão (cheirinho, pretinho, flanela) **pelo PDV de hoje** ou como item de produto na OS | Já existe | 🟡 |
| C3 | **Planos, pacotes e fidelidade são opcionais por loja**: chave em Configurações, **desligada por padrão**; desligada, nenhuma tela muda. Três modalidades, cada uma ligável sozinha: **(a) plano mensal** por placa (N lavagens ou ilimitado, serviços cobertos, valor, dia de vencimento → conta a receber mensal); **(b) pacote pré-pago** (N lavagens, sem validade ou com validade); **(c) cartão fidelidade** (a cada N lavagens pagas, 1 grátis). Na OS da placa, o item coberto sai R$ 0,00 com a origem "plano/pacote/fidelidade" e baixa o saldo | Decisão do usuário (12/11): "fica a critério do cliente usar". O mercado vende plano **por porte** (LavaX), daí o vínculo com a placa. O primeiro cliente **não usa** hoje: fica para os próximos, depois da Agenda | ✅ (opcional) · 🟡 (desenho) |
| C4 | **Frota / convênio**: cliente PJ com várias placas marcado "fatura no mês"; a OS finaliza sem pagamento e entra num fechamento que gera **uma** conta a receber com o extrato das placas | Comum em lava-jato de caminhão; o cliente da transportadora não paga no balcão. O primeiro cliente **não tem**; fica para lava-rápidos maiores, por último | ✅ (por último) |
| C5 | **Fiscal**: NFS-e pelo módulo que já existe; o item da LC 116 e a alíquota de ISS são definidos com o contador do cliente antes da primeira nota | Não decidir enquadramento fiscal por conta própria | Revista por C5a |
| C5a | **Revisão 1 — Spec 09:** o segmento sai **preparado** para emitir, sem motor fiscal novo: (1) **NFS-e** da lavagem a partir da OS pelo módulo NFS-e de hoje, com o **código de serviço sugerido** no cadastro do serviço (provavelmente o item **14.01** da LC 116 — "limpeza, lustração… de veículos" —, **confirmar com o contador** de cada cliente) e a placa/veículo na discriminação; (2) **NFC-e/NF-e** dos produtos de balcão pelo PDV de hoje; (3) OS com serviço **e** produto: conferir se a nota sai pelos dois caminhos sem duplicar. A Spec 09 é uma **conferência** do que existe para este segmento, e só vira código se faltar algo | O primeiro cliente não emite, mas o próximo pode; é melhor descobrir a lacuna agora do que no balcão de outro cliente | 🟡 |

### 6.5. Interface própria (Revisão 4)

| # | Decisão | Motivo | Status |
|---|---------|--------|--------|
| U1 | Módulo próprio **`modules/lava-rapido/`**, ligado pela capacidade nova `operacao_patio` (declarada só pelo lava-rápido). No segmento, o menu **Serviços** abre as abas **Pátio · Agenda · Histórico** (Histórico = a lista de OS de sempre). **Pátio é a tela inicial.** Segue o padrão de `modules/marcenaria/` | O dia do lava-rápido é a fila de carros, não a lista de documentos (§3.3) | ✅ |
| U2 | **Nova entrada = comanda de uma tela, sem abas**, nesta ordem: placa (traz veículo e dono; placa nova pede nome e telefone ali mesmo) → tipo de veículo → porte → serviços em **botões** com o preço do porte → lavador (2º opcional) → avarias com foto → observação → **Entrar** / **Entrar e imprimir**. Tipo, porte e serviço são botões, não lista suspensa. Substitui O1 | PR10: meta ≤ 30 s e ≤ 6 cliques para cliente que já veio | ✅ |
| U3 | **Pátio**: colunas por status — ABERTA "**Aguardando**", EM_ANDAMENTO "**Lavando**", AGUARDANDO_RETIRADA "**Pronto**" — e "Entregues hoje" recolhido. Cartão: placa, veículo, porte, serviços, lavador, hora de entrada e previsão; um clique avança; no Pronto, **WhatsApp** e **Receber** (abre o pagamento de sempre). Atualiza sozinho. Substitui O3. Os rótulos Aguardando/Lavando passam a valer também em `rotulos_status` (lista, filtro, impressão) | Palavras do pátio; o usuário disse "pode usar quantos status precisar" | 🟡 rótulos com o usuário |
| U4 | **Avarias por tipo de veículo**: cada tipo declara a sua lista no registry (chave `vistoria` dentro do tipo; tipo que não declara usa a do segmento). Na comanda é um **checklist de marcar o que tem avaria**, com foto — não a vistoria item a item com estado. Moto: carenagem, tanque, banco, escapamento, guidão/manetes, retrovisores, faróis/piscas, rodas. Bicicleta: quadro/pintura, rodas/aros, câmbio/corrente, selim, guidão, freios. Substitui O5 | "Não dá para padronizar: lava carro, moto, caminhão, bicicleta" (usuário). Checklist de marcar é o que o ramo usa (§3.3) | 🟡 confirmar checklist simples |
| U5 | **Bicicleta** vira tipo próprio (sem placa; porte Infantil / Adulto / Elétrica), além de Carro, Moto, Caminhão/ônibus e Outros | Citada pelo usuário; em "Outros" pegaria vistoria e porte de carro | 🟡 |
| U6 | A **OS de abas** fica só como "**Ver detalhes**" da lavagem (no cartão do pátio e no Histórico) — fotos extras, reabrir, nota. Nenhuma tela do lava-rápido obriga a passar por ela | O documento continua o mesmo (PR2); só a porta de entrada muda | ✅ |

---

## 7. Fora da fase 1

| Assunto | Por quê |
|---------|---------|
| Agendamento **online pelo próprio cliente** (link público) | A agenda interna entra na fase 1 (O11, Revisão 1); o link público exige servidor na internet, e o ERP roda na rede da loja |
| Leitura de placa por câmera (OCR/LPR) | Hardware e custo; digitar a placa resolve |
| WhatsApp automático pela API oficial, campanhas e reativação em massa | Custo por mensagem e conta comercial da Meta |
| Cobrança recorrente automática no cartão (plano mensal) | Exige gateway de pagamento; o plano gera a conta a receber e a loja cobra como já cobra |
| Cashback | Fidelidade (C3c) cobre o caso comum |
| Lavador diferente **por item** da OS (um lava, outro aspira) | Os lavadores são da OS inteira (O7a); por item exigiria mexer em `ordem_servico_itens`, que todos os segmentos usam |
| Vídeo na vistoria | Tamanho de arquivo e backup; foto basta |
| Estética automotiva de vários dias (vitrificação, PPF, polimento) com etapas | O quadro mostra a OS aberta; etapas por serviço seriam outra spec |

---

## 8. Lista de specs

| Spec | Camada | O que entrega | ⚠️ Código compartilhado | Tamanho |
|------|--------|---------------|------------------------|---------|
| 00 | Documento | Este registro | — | — |
| 01A | Backend | `definicoes/lava_rapido.py` (4 tipos, campos, vistoria, rótulos), `status_usados` (O2b), identificador placa-ou-gerado (P4a), `SEGMENTOS_VALIDOS` — sem tabela nova (Revisão 3) | ⚠️ registry, criação e edição de OS (por chave declarada) | M |
| 10A | Backend | Lavadores da OS (`ordem_servico_executores`, capacidade `executores_os`) e comissão Dividir/Inteira (O7a, O7c) | ⚠️ relatório de comissão (por capacidade) | M |
| 10B | Frontend | Lavadores no formulário e na impressão; escolha Dividir/Inteira no cargo e no funcionário | ⚠️ formulário de OS, cargos, funcionários | M |
| 01B | Frontend | Segmento em `SEGMENTOS`, card do onboarding, status reduzidos nos botões/filtros, porte e lavadores no formulário, textos e conteúdo da impressão térmica e A4 (O10a) | ⚠️ constantes de segmento, formulário de OS, filtros, impressão | G |
| 02A | Backend | Tabelas `portes_veiculo` (P2a, com a lista inicial) e `servico_precos_porte` (+ migração), CRUD, rota "preço do serviço para este veículo", previsão (O4) | ⚠️ schemas de serviço (só acréscimo) | M |
| 02B | Frontend | Configurações › Portes; grade de portes no cadastro de serviço (por capacidade); ao incluir serviço na OS, preço do porte; previsão no formulário | ⚠️ cadastro de serviço, itens da OS | M |
| 03 | Frontend | Entrada rápida (O1) e cupom de entrada (O10) | ⚠️ fluxo de criação de OS | M |
| 04A | Backend | Rota do pátio (OS abertas com placa, porte, lavadores, tempos) e troca rápida de status | — | P |
| 04B | Frontend | Quadro do pátio (O3) + botão WhatsApp e texto em Configurações (O8) | ⚠️ abas de Serviços | M |
| 08A | Backend | Agenda (O11): tabela `agendamentos`, situações, capacidade da loja, "Chegou" → dados da OS | — | M |
| 08B | Frontend | Aba Agenda em Serviços (dia e semana), modal de agendamento, "Chegou" abre a entrada rápida, WhatsApp de confirmação | ⚠️ abas de Serviços | G |
| 09 | Conferência (A + B se faltar algo) | Fiscal do segmento (C5a): NFS-e da OS, código de serviço sugerido, produto pelo PDV | ⚠️ fiscal (só se faltar algo) | P |
| 05A | Backend | Planos, pacotes e fidelidade (C3): tabelas, saldo, baixa na OS, conta a receber do plano, chave em Configurações | ⚠️ ganchos de finalizar/reabrir/cancelar OS | G |
| 05B | Frontend | Configurações › Planos, cadastro do plano/pacote do cliente, aviso de saldo na OS, extrato | ⚠️ cliente, OS | G |
| 06A | Backend | Frota/convênio (C4): cliente "fatura no mês", fechamento → conta a receber | ⚠️ finalização de OS | M |
| 06B | Frontend | Marcação no cliente, tela de fechamento e extrato por placa | ⚠️ cliente | M |
| 07 | A + B | Lembrete de retorno (O9) sobre o módulo Revisões | ⚠️ revisões (oficina usa) | P |

---

## 9. Riscos

| Risco | Mitigação |
|-------|-----------|
| A oficina usa placa, vistoria e Revisões — mexer nelas quebra quem está faturando | Lava-rápido só **declara**; mudanças de motor são por capacidade com prova de não regressão (PR1, PR9) |
| Esconder status (O2) é mecanismo novo no registry | Chave opcional; segmento que não declara recebe a lista de hoje; teste de contrato para cada segmento existente |
| `ordem_servico.py` perto do teto de 64 KB do PyArmor trial | Código novo em `services/` próprios (`servico_preco_porte`, `planos`), nunca engordar o serviço da OS |
| Planos mexem em dinheiro (conta a receber, item a R$ 0,00) | Spec 05A com testes de reabrir/cancelar OS e devolução de saldo; desligado por padrão |
| Primeiro cliente fechado = pressão de prazo | Marco 1 é instalável sozinho; planos e frota entram depois sem reinstalar do zero |

## 10. Perguntas para o cliente — respondidas em 12/11/2026 (Revisão 1)

| # | Pergunta | Resposta | Decisão |
|---|----------|----------|---------|
| 1 | Quais veículos? | Qualquer transporte | P4a (tipo "Outros") |
| 2 | Tabela de preços | Cobra por porte; cadastra no serviço | P1 ✅, P2a |
| 3 | Mensalista, pacote, fidelidade? | Não usa; deixar pronto para o futuro | C3 opcional, depois da Agenda |
| 4 | Frota que paga no mês? | Não; pensar para lava-rápidos maiores | C4 por último |
| 5 | Um ou dois lavadores? | Na loja dele, ele e mais um; em loja grande, 1 ou 2 por carro; quem abre é o responsável | O7a, O7c |
| 6 | Impressora? | Não usa; os próximos terão térmica e A4/PDF | O10a |
| 7 | Nota fiscal? | Não usa; deixar preparado | C5a (Spec 09) |

**Ainda em aberto (para o primeiro cliente, sem bloquear a Spec 01A):** a tabela de preços dele (para cadastrar no piloto) e se ele usa celular no pátio para a vistoria.

## 11. Como usar este documento

Cada decisão 🟡 vira ✅ na revisão com o usuário; cada ❓ fecha com a resposta do cliente (§10). Mudança depois da aprovação entra como **Revisão N** no topo deste arquivo, com data e o que mudou. As specs citam as decisões pelo código e nunca as contradizem; se precisarem, este documento é revisado primeiro.
