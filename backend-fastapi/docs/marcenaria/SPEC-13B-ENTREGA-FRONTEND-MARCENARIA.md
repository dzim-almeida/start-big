# Spec 13B — Entrega e Instalação (Frontend)

| Campo        | Valor                                                                                         |
|--------------|-----------------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                               |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado (abas da OS e de Serviços, finalização) |
| Dependências | Specs 07 (impressão A4), 12B (padrão de abas, `openExistingOS` com aba), 13A (API)            |
| Bloqueia     | —                                                                                             |
| Referência   | SPEC-00: I1, I2, I3, I4, I5, I5a, I6, T8a, P2, P3, P4 · PR1, PR3, PR6                         |

---

## 1. Objetivo

1. **Aba "Entrega"** na OS: um cartão por ambiente, com o agendamento, o termo para imprimir, o registro do resultado, as fotos e as pendências.
2. **Termo de Entrega A4 por ambiente** (I1): o papel que o montador leva para a obra.
3. **Aba "Instalações"** em Serviços (T8a): quem instala onde, por dia.
4. **Aviso na finalização** da OS quando há ambiente não entregue ou pendência aberta (I3), sem travar.

## 2. Escopo

**Dentro do escopo**
- `OSEntregaTab` e modais (agendar, registrar, pendência, checklist).
- `TermoEntregaPrint` (A4, preto e branco).
- `InstalacoesTab` em Serviços.
- Bloco de aviso no `OSFinalizarModal` (capacidade `orcamento_tecnico`).

**Fora do escopo**
- Agenda em calendário (fase 2).
- Etiquetas (Spec 14).

---

## 3. Arquivos afetados

```
frontend/src/modules/
├── order-service/
│   ├── ordens/components/form/OSFormTabsContent.vue          # ALTERAR ⚠️ — aba 'entrega'
│   ├── ordens/components/OSFinalizarModal.vue                 # ALTERAR ⚠️ — bloco de aviso por capacidade
│   └── views/OrdemServicoView.vue                             # ALTERAR ⚠️ — aba "Instalações"
└── marcenaria/entrega/
    ├── services/entrega.service.ts · agenda.service.ts       # CRIAR
    ├── schemas/entrega.schema.ts                              # CRIAR
    ├── composables/useEntregaDaOS.ts · useInstalacoes.ts      # CRIAR
    └── components/
        ├── OSEntregaTab.vue                                   # CRIAR
        ├── EntregaAmbienteCard.vue                            # CRIAR
        ├── AgendarModal.vue                                   # CRIAR
        ├── RegistrarEntregaModal.vue                          # CRIAR
        ├── PendenciaModal.vue · ResolverPendenciaModal.vue    # CRIAR
        ├── EditarChecklistModal.vue                           # CRIAR — usa ListaTextosEditavel
        ├── TermoEntregaPrint.vue                              # CRIAR — A4 (Teleport)
        ├── AvisoEntregaFinalizacao.vue                        # CRIAR — bloco do OSFinalizarModal
        └── InstalacoesTab.vue                                 # CRIAR — aba em Serviços
```

---

## 4. Decisões

### 4.1. Aba Entrega

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Aba **"Entrega"** no modal da OS, depois de "Produção" (ordem final: Serviços e Peças → Separação → Produção → Entrega → Orçamento), só com `temOrcamentoTecnico` e fora da criação | T1; mesmo mecanismo das abas anteriores |
| D2 | Topo: "1 de 3 ambientes entregues · 2 pendências abertas", o botão **"Agendar instalação"** e a lista de agendamentos da OS (data, hora, ambientes, montadores; atrasados em vermelho; editar e excluir quando permitido) | I5a |
| D3 | Um **cartão por ambiente** com: situação (Pendente / Conforme / Com ressalvas), o agendamento ("Instalação 03/11 às 08:00 · Carlos, Davi"), os móveis, e os botões **"Imprimir termo"** e **"Registrar entrega"** (pendente) ou **"Corrigir registro"** (registrado). Registrado: data, montadores, recebido por, marcações do checklist resumidas ("12 ok · 1 não"), observações, pendências e fotos | I1, I6 |
| D4 | "Imprimir termo" do ambiente e, no topo, **"Imprimir termos do agendamento"** (todos os ambientes de um agendamento, um por página) | O montador sai com um termo por ambiente da visita, sem imprimir um a um |
| D5 | **Registrar entrega:** modal com Conforme / Com ressalvas (botões grandes), data (hoje), montadores (já marcados os do agendamento), recebido por, o checklist com três estados por item (✓ / ✗ / em branco, todos em branco no início), observações, pendências (uma por linha; obrigatória com ressalvas) e as fotos (dois campos: **"Foto do termo assinado"** e **"Fotos da montagem"**, vários arquivos) | I1, 13A D4, D7. O que vem do papel é digitado na ordem do papel |
| D6 | Registrar sem foto do termo: o modal pergunta "Registrar sem a foto do termo assinado?" antes de enviar | 13A D8: avisar sem travar, na hora certa |
| D7 | Pendências do cartão com **"Resolver"** (como foi resolvido, data) e **"Reabrir"**; **"+ Pendência"** sempre disponível, mesmo com a OS finalizada | 13A D6 |
| D8 | "Editar checklist" no cartão pendente (usa o `ListaTextosEditavel`) | I2 |
| D9 | Quando a resposta traz `todos_entregues`, a aba pergunta "Todos os ambientes foram entregues. Finalizar a OS agora?" e abre o fluxo de finalização de sempre (`OSFinalizarModal`) | P2: sugere; a finalização tem as regras de pagamento dela |
| D10 | OS fechada: só pendências editáveis; o resto somente leitura | 13A |
| D11 | Nenhum preço na aba nem no termo | P4 |

### 4.2. Termo de Entrega (I1)

| # | Decisão | Motivo |
|---|---------|--------|
| D12 | A4, preto e branco, pelo caminho de impressão das outras vias (`imprimirComPagina('A4')`, Teleport, `check:print-bw`). Conteúdo: cabeçalho da empresa; "TERMO DE ENTREGA E INSTALAÇÃO"; OS e código do projeto (PRJ); cliente e telefone; endereço da obra; **ambiente**; data agendada e montadores; a lista de móveis do ambiente (nome, medidas, quantidade); o **checklist** com as colunas "OK" e "Não OK" para marcar à caneta; "Pendências / observações" com 6 linhas em branco; a declaração "Recebi os móveis acima, instalados e em condições de uso, ressalvadas as pendências anotadas."; assinaturas **Cliente / recebedor** (com nome e documento à mão) e **Montador**; data | I1: o papel é o que o montador usa na obra |
| D13 | Um termo cabe numa página na maioria dos ambientes; com muitos móveis, a lista quebra de página, e o bloco do checklist + pendências + assinaturas fica junto (`break-inside: avoid`), como na proposta (07 D13) | O que se assina precisa estar na mesma folha das assinaturas |
| D14 | Nome sugerido do PDF (para quem salvar em vez de imprimir): "Termo OS-2026-000512 - Cozinha Gourmet" (mesmo mecanismo do título da 07 D5) | Consistência com a proposta |

### 4.3. Aba Instalações (T8a)

| # | Decisão | Motivo |
|---|---------|--------|
| D15 | Aba **"Instalações"** em Serviços, depois de "Produção" (ordem: Ordens, Cadastro de Serviços, Produção, Instalações, Terceirizados), só com `temOrcamentoTecnico` | T8a |
| D16 | Atalhos de período **Hoje · Amanhã · Esta semana · Próximos 30 dias** (padrão: Esta semana), filtro por montador e "Só atrasadas". Lista agrupada **por dia** ("Segunda, 03/11"), cada linha com hora, OS (abre na aba Entrega), cliente, endereço da obra, ambientes e montadores, e a situação das entregas | "Quem instala onde amanhã" (I5), lido de cima para baixo |
| D17 | Botão "Imprimir a lista do dia" (A4, um bloco por agendamento, com o endereço) | A equipe sai de manhã com o roteiro em papel (P3) |

### 4.4. Finalização ⚠️

| # | Decisão | Motivo |
|---|---------|--------|
| D18 | No `OSFinalizarModal`, com `temOrcamentoTecnico`, um bloco **âmbar e informativo** (`AvisoEntregaFinalizacao`) carregado de `/entrega/resumo`: "Ambientes ainda não entregues: Closet." e/ou "Pendências abertas: Porta do aéreo 2 desalinhada." O botão de finalizar continua habilitado | I3: avisa, não trava. Mesmo lugar do bloco de "itens pendentes" que já existe no modal (que trava; este não) |
| D19 | Sem a capacidade, o bloco não existe e nenhuma chamada é feita | PR1 |

---

## 5. Contratos consumidos

Spec 13A §6. Do sistema: `imprimirComPagina`, `aguardarImagensDaImpressao`, `useCompanyPrintInfo`, `PrintCompanyHeader`, `PrintSignatures`, `ListaTextosEditavel` (já em `shared` desde a 12B), `openExistingOS(os, { abaInicial })` (12B), funcionários ativos.

---

## 6. Telas

### 6.1. Aba Entrega

```
Entrega   1 de 3 ambientes entregues · 2 pendências abertas                   [Agendar instalação]
Agendamentos
  03/11 08:00  Cozinha Gourmet, Sala          Carlos, Davi        [Imprimir termos] [Editar] [Excluir]
  10/11 —      Closet                         Carlos               ⚠ atrasado

┌ COZINHA GOURMET · Com ressalvas · entregue em 03/11 · Carlos, Davi · recebido por Ana (síndica) ┐
│ Checklist: 12 ok · 1 não ok        Fotos: [termo] [m1] [m2] [+]                                 │
│ Pendências: ○ Porta do aéreo 2 desalinhada   [Resolver]      [+ Pendência]                      │
│                                                     [Imprimir termo] [Corrigir registro]        │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
┌ CLOSET · Pendente · instalação 10/11                         [Imprimir termo] [Registrar entrega] ┐
```

### 6.2. Termo (A4)

```
[logo] Marcenaria Exemplo · CNPJ · contato            TERMO DE ENTREGA E INSTALAÇÃO
                                                      OS-2026-000512 · PRJ-000031
Cliente: Studio Arquitetura & Interiores Ltda · (85) 3333-4444
Obra: Av. das Américas, 4200 — Residencial Alpha Ville - Apto 802
Ambiente: COZINHA GOURMET        Instalação: 03/11/2026 · Montadores: Carlos, Davi

Móveis
  Torre Quente ............................. L 700 × A 2200 × P 600 mm   1 un.
  Armário aéreo ............................ L 800 × A 700 × P 350 mm    3 un.

Vistoria                                                        OK    Não OK
  Alinhamento de portas e gavetas                               [ ]    [ ]
  …
Pendências / observações
  ________________________________________________________________ (6 linhas)

Recebi os móveis acima, instalados e em condições de uso, ressalvadas as pendências anotadas.
____________________________                ____________________________
Cliente / recebedor (nome e doc.)            Montador
Data: ___/___/______
```

---

## 7. Especificação técnica

### 7.1. Abas ⚠️

- `OSFormTabsContent`: `'entrega'` em `TabType`, depois de `'producao'`, mesma condição; fora do `<fieldset>` travável.
- `OrdemServicoView`: `{ id: 'instalacoes', label: 'Instalações' }` depois de `'producao'`; `mostrarBotaoAdicionar` devolve `false` para ela.

### 7.2. Aviso na finalização — `OSFinalizarModal.vue` ⚠️

```vue
<!-- Marcenaria: entrega incompleta AVISA, mas não impede finalizar (I3).
     Sem a capacidade, o componente nem é montado (nenhuma chamada a /marcenaria). -->
<AvisoEntregaFinalizacao
  v-if="temOrcamentoTecnico && osNumber"
  :numero-os="osNumber"
/>
```

`AvisoEntregaFinalizacao` faz a query do resumo (13A D15) só quando montado, e não emite nada para o modal: o botão de finalizar não depende dele.

### 7.3. Impressão de vários termos

```ts
/** Um termo por ambiente do agendamento, cada um começando numa página nova (D4). */
async function imprimirTermosDoAgendamento(agendamento: Agendamento) {
  termosParaImprimir.value = entregas.value.filter((e) => agendamento.ambiente_ids.includes(e.ambiente_id));
  document.title = `Termos ${numeroOs.value} - ${formatarData(agendamento.data)}`;   // nome do PDF
  await nextTick();                                                                // os termos entram no DOM
  await aguardarImagensDaImpressao();                                              // logo da empresa
  imprimirComPagina('A4', { folha: 'A4' });
}
```

No template, cada `TermoEntregaPrint` depois do primeiro leva `break-before: page`. Título restaurado no `afterprint`, como na 07 §6.3.

---

## 8. Prova de não regressão (⚠️ PR1)

1. `npm run test`, `npx vue-tsc --noEmit`, `npm run check:print-bw`.
2. Abas do modal de OS e da tela de Serviços nos outros segmentos iguais às de hoje (snapshots).
3. `OSFinalizarModal` na informática, oficina e serigrafia: o mesmo conteúdo e o mesmo comportamento; nenhuma chamada a `/marcenaria/...`; o bloco de itens pendentes da oficina continua travando como hoje.
4. Vias de OS (entrada, entrega, cupom) iguais depois de imprimir um termo.

## 9. Limitações conhecidas

- Sem calendário semanal (I5).
- O termo é preenchido à mão na obra e passado a limpo na fábrica (P3).

---

## 10. Critérios de aceite

- [ ] Aba Entrega só na marcenaria, com resumo, agendamentos e um cartão por ambiente.
- [ ] Agendar com data, hora, ambientes e montadores; aviso de montador ocupado; atrasado em vermelho; editar e excluir quando permitido.
- [ ] Imprimir o termo de um ambiente e os termos de um agendamento (um por página), em A4 preto e branco, sem preço.
- [ ] Registrar Conforme ou Com ressalvas com checklist em três estados, pendências, recebido por e fotos; pergunta quando falta a foto do termo; corrigir depois.
- [ ] Pendências resolvidas e reabertas, e novas depois da finalização.
- [ ] Último ambiente entregue oferece finalizar a OS.
- [ ] Aba Instalações por dia, com atalhos de período, montador e atrasadas, e impressão da lista do dia.
- [ ] Finalização avisa ambiente não entregue e pendência aberta sem travar.
- [ ] Prova de não regressão (§8). Código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Abas da OS na marcenaria | … Produção, Entrega, Orçamento |
| 02 | Abas em Serviços na marcenaria | Ordens, Cadastro, Produção, Instalações, Terceirizados |
| 03 | Mesmas telas na informática | Iguais às de hoje |
| 04 | `RegistrarEntregaModal` com ressalvas sem pendência | Erro no campo de pendências |
| 05 | Mesmo modal sem foto do termo | Pergunta do D6 antes de enviar |
| 06 | Montadores do modal | Pré-marcados os do agendamento do ambiente |
| 07 | `AgendarModal` com `MONTADOR_OCUPADO` na resposta | Aviso com quem e onde; agendamento salvo |
| 08 | `TermoEntregaPrint` | Sem preço; checklist com OK/Não OK; 6 linhas; duas assinaturas |
| 09 | Imprimir termos de um agendamento com 2 ambientes | 2 termos; o segundo começa em página nova |
| 10 | Resposta com `todos_entregues` | Pergunta "Finalizar a OS agora?" |
| 11 | `OSFinalizarModal` na marcenaria com pendência aberta | Bloco âmbar; botão de finalizar habilitado |
| 12 | `OSFinalizarModal` na informática | Sem o bloco; sem chamada à marcenaria |
| 13 | `InstalacoesTab` "Amanhã" | Só os agendamentos de amanhã, agrupados no dia |
| 14 | Clique na OS da lista de instalações | OS aberta na aba Entrega |

### Roteiro manual (dev)

1. OS com 3 ambientes prontos: agendar cozinha e sala para amanhã (Carlos, Davi) e closet para ontem.
2. Serviços › Instalações: "Amanhã" e "Só atrasadas"; imprimir a lista do dia.
3. Imprimir os termos do agendamento de amanhã; conferir o papel.
4. Registrar a cozinha com ressalvas, com foto do termo e duas da montagem; registrar a sala sem foto (pergunta).
5. Tentar finalizar a OS: ver o aviso do closet e da pendência; cancelar; resolver a pendência; registrar o closet; aceitar "Finalizar a OS agora?".
6. Criar uma pendência nova com a OS finalizada.
7. Informática: §8.
