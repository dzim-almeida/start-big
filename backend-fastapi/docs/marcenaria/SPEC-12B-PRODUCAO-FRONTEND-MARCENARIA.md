# Spec 12B — Produção: Aba na OS e Quadro da Fábrica (Frontend)

| Campo        | Valor                                                                                   |
|--------------|-----------------------------------------------------------------------------------------|
| Status       | Implementada em 09/10/2026                                                              |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado (abas da OS e da tela de Serviços) |
| Dependências | Specs 01B (rótulos de status), 08B (padrão de aba), 11B (terceirizados), 12A (API)      |
| Bloqueia     | —                                                                                       |
| Referência   | SPEC-00: P1, P1a, P2, P2a, P2b, P3, P4, E6a, T1 · PR1, PR3, PR6                         |

> **Implementação (09/10/2026) — o que o código acrescenta ou decide além do texto.**
> (1) **"Concluir em todos" com o "Feito por":** o botão manda as etapas pendentes daquele nome para `POST /etapas/concluir` (um POST só, caso 05), e não para `/concluir-em-todos`, que não aceita o responsável: assim o D6 vale também no lote. O nome é comparado sem diferenciar maiúsculas, como o backend.
> (2) **Iniciar:** pelo botão direito no chip ou pelo "⋯" que aparece ao passar o mouse; abre um modal pequeno ("Quem vai fazer"), que já vem com o "Feito por". "Iniciar selecionadas" usa o mesmo modal. Reabrir (no menu do chip concluído) não pede confirmação: o menu já é o passo deliberado, e reabrir por engano se desfaz com um clique.
> (3) **"Feito por" (D6):** vale para a sessão (até fechar o sistema), não só para a aba; "Eu (usuário logado)" manda sem o campo, e o backend usa o funcionário do usuário. A lista é a dos funcionários do próprio modal de OS (sem permissão de ver funcionários, o select some).
> (4) **Otimista (D11):** a recarga automática pausa com modal aberto e enquanto há gravação no ar (uma leitura velha desfaria a marcação na tela). No erro, a tela volta ao estado anterior na hora e a aba relê a API.
> (5) **Pergunta de status (D12, D13):** `aplicarStatusSalvo` foi extraído para `useOSAplicarStatus` (testável sozinho) e entra no contexto do modal. As abas recebem a função por prop (`aplicarStatus`); sem ela, a pergunta não aparece. A pergunta também aparece na aba Separação, quando o conferir ou o voltar de um terceirizado (11B) trazem sugestão.
> (6) **Aba inicial (§7.1):** `openExistingOS(os, comReopen, { abaInicial })` — o terceiro parâmetro é opcional e as chamadas de hoje não mudam. O modal lê o pedido ao abrir e o limpa; uma aba que o segmento não tem cai em "objeto".
> (7) **`ListaTextosEditavel` em `shared/components/ui/`** (com a regra `errosDosItens` ao lado, reexportada de `marcenariaForm.ts`). Dois props opcionais novos: `ids` (v-model:ids, a identidade que anda com o item ao mover e remover) e `travados` + `motivoTravado`. Sem eles, Configurações › Marcenaria fica igual (teste).
> (8) **Terceirizado no cartão (D7):** a API da 12A não manda o nome da central na produção; o cartão mostra "Central · Pedido enviado · chega 20/10" (o nome e o telefone ficam na seção da Separação).
> (9) **Quadro:** os filtros (status, "Só atrasadas", busca) são aplicados na tela sobre a lista da API, que já vem na ordem da previsão. "Atrasada" = a OS tem móvel não pronto com a previsão vencida (`moveis_atrasados` da 12A).

---

## 1. Objetivo

1. **Aba "Produção"** na OS: os móveis com as etapas, para marcar o que foi feito com o menor número de cliques, inclusive em lote.
2. **Perguntar** a mudança de status da OS quando a produção começa e quando termina (P2, P2b), e aplicar com um clique.
3. **Quadro da fábrica** na tela de Serviços: todas as OS em produção, com o progresso e o que vem a seguir.

A tela é do **computador fixo da fábrica** (P3): botões grandes, sem preço (P4).

## 2. Escopo

**Dentro do escopo**
- `OSProducaoTab` (aba da OS) e componentes.
- Editor das etapas de um móvel.
- Pergunta de status e a troca de status.
- Aba "Produção" na tela de Serviços (capacidade `orcamento_tecnico`).

**Fora do escopo**
- Relatórios de tempo e produtividade (fase 2).

---

## 3. Arquivos afetados

```
frontend/src/modules/
├── order-service/
│   ├── ordens/components/form/OSFormTabsContent.vue          # ALTERAR ⚠️ — aba 'producao'
│   ├── ordens/context/useOSFormView.context.ts               # ALTERAR ⚠️ — aplicarStatusSalvo
│   └── views/OrdemServicoView.vue                            # ALTERAR ⚠️ — aba "Produção"
└── marcenaria/producao/
    ├── services/producao.service.ts                          # CRIAR
    ├── schemas/producao.schema.ts                            # CRIAR
    ├── composables/useProducaoDaOS.ts                        # CRIAR
    ├── composables/useQuadroProducao.ts                      # CRIAR
    └── components/
        ├── OSProducaoTab.vue                                 # CRIAR
        ├── MovelProducaoCard.vue                             # CRIAR
        ├── EtapaChip.vue                                     # CRIAR
        ├── EditarEtapasModal.vue                             # CRIAR — usa ListaTextosEditavel (04B)
        ├── SugestaoStatusModal.vue                           # CRIAR
        └── QuadroProducaoTab.vue                             # CRIAR — aba em Serviços
```

`ListaTextosEditavel` (04B §6.6) sobe para `shared/components/` nesta spec, como a 04B previu.

---

## 4. Decisões

### 4.1. Aba Produção

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Aba **"Produção"** no modal da OS, depois de "Separação" (ordem: Serviços e Peças → Separação → Produção → Orçamento), só com `temOrcamentoTecnico` e fora da criação | T1; mesmo mecanismo das 08B e 10B |
| D2 | Topo: barra de progresso da OS ("14 de 25 etapas · 2 de 6 móveis prontos"), a previsão de entrega ("entrega prevista 05/11 · faltam 12 dias", em vermelho se passou) e a barra **"Concluir em todos:"** com um botão por etapa que ainda tem pendências ("Corte (4)", "Borda (6)", …) | P1a: o atalho do lote é o que a fábrica mais vai usar; o número diz quantos móveis ainda faltam naquela etapa |
| D3 | Um **cartão por móvel** (agrupados por ambiente): nome, medidas, quantidade, e as etapas como **chips** em linha na ordem: cinza (pendente), azul (em execução, com o nome de quem está fazendo), verde ✓ (concluída). A próxima etapa pendente tem borda destacada | Leitura de relance, de longe, na tela da fábrica |
| D4 | **Clique no chip** pendente ou em execução: conclui (com confirmação só se a etapa não for a próxima: "Concluir Montagem antes de Borda?"). Clique no chip concluído: menu com **Reabrir**. Botão direito / "⋯" no chip: **Iniciar** (escolhendo o responsável) | P1a: concluir é o caso comum e deve custar um clique; a confirmação só aparece no caso estranho (fora de ordem), sem travar |
| D5 | **Modo seleção** (botão "Selecionar"): marcar chips de vários móveis e "Concluir selecionadas" / "Iniciar selecionadas" | P1a, lote livre |
| D6 | Responsável: por padrão o funcionário logado; um select "Feito por" no topo da aba muda o padrão para a sessão (o computador da fábrica costuma ter um usuário só, usado por várias pessoas) | P3: um computador, várias pessoas. Sem isso, toda etapa sairia no nome do mesmo usuário |
| D7 | Cartão do móvel **terceirizado**: sem chips; mostra a situação da 11B ("Pedido enviado · chega 20/10") e fica verde "Pronto" quando conferido | E6a |
| D8 | Menu do cartão: **"Editar etapas"** abre o editor de lista (incluir, renomear, remover, reordenar; etapa concluída sem remover/renomear, com o motivo no `title`). Móvel `sem_etapas`: aviso e botão **"Aplicar etapas padrão"** | P1, 12A D3, D6 |
| D9 | Filtro "Esconder móveis prontos" (desligado por padrão; ligado, mostra "2 móveis prontos escondidos") | OS de 30 móveis: no fim da obra, só o que falta interessa |
| D10 | OS fechada: tudo somente leitura | 12A D13 |
| D11 | Recarrega a cada `REFETCH_REALTIME` com a aba aberta e sem modal; marcação feita é aplicada na tela **antes** da resposta (otimista) e desfeita com aviso se falhar | Dois marceneiros marcando em sequência; a resposta otimista faz o clique parecer instantâneo no computador da fábrica |

### 4.2. Pergunta de status (P2, P2b)

| # | Decisão | Motivo |
|---|---------|--------|
| D12 | Quando a resposta traz `sugestao_status`, abre `SugestaoStatusModal`: "A produção começou. Mover a OS para **Em Produção**?" ou "Todos os móveis estão prontos. Mover a OS para **Aguardando Entrega**?", com **"Mover"** e **"Agora não"** | P2, P2b: a decisão é do usuário. O rótulo vem do backend (01A), não do enum |
| D13 | "Mover" grava **só o status** da OS (`updateOrderService` com `{status}`) e atualiza no formulário aberto apenas o campo de status (`aplicarStatusSalvo`), sem tocar em outras alterações não salvas do modal | O marceneiro não pode perder uma observação digitada na outra aba por ter aceitado a sugestão |
| D14 | "Agora não": nada muda; a pergunta não volta até a próxima mudança de situação (12A D17) | Pergunta repetida vira clique automático |

### 4.3. Quadro da fábrica

| # | Decisão | Motivo |
|---|---------|--------|
| D15 | Aba **"Produção"** na tela de Serviços, **antes** de "Terceirizados", só com `temOrcamentoTecnico` (mesmo mecanismo da 11B D11) | O quadro é a primeira coisa que a fábrica abre de manhã |
| D16 | Uma linha por OS em aberto: número (abre a OS **na aba Produção**), cliente, projeto, status (rótulo do segmento), barra de progresso, "2 de 6 móveis prontos", próxima etapa mais comum ("Montagem em 4 móveis"), previsão e atraso. Ordenado pela **previsão** (a mais próxima primeiro) | 12A D18. A ordem pela previsão é a ordem de prioridade da fábrica |
| D17 | Filtros: status, "Só atrasadas", busca por cliente/projeto | O mínimo para uma fábrica com 20 obras |
| D18 | Recarrega a cada `REFETCH_DASHBOARD` (30 s) | É um quadro de parede |

---

## 5. Contratos consumidos

Spec 12A §6. Do sistema: `updateOrderService` (só `status`), `getUniqueOS` + `openExistingOS` (com a aba inicial), funcionários ativos (`getEmployeesAll`), `useCapacidades`, `ListaTextosEditavel` (04B).

---

## 6. Telas

### 6.1. Aba Produção

```
Produção   ▒▒▒▒▒▒▒░░░░░ 14 de 25 etapas · 2 de 6 móveis prontos   Entrega prevista 05/11 · faltam 12 dias
Feito por: [João Silva ▾]                                        [Selecionar]  [ ] Esconder prontos
Concluir em todos:  [Corte (2)] [Borda (4)] [Furação (5)] [Montagem (6)] [Embalagem (6)]

COZINHA GOURMET
┌ Armário aéreo · 800×700×350 · 3×                                                        ⋯ ┐
│ [✓ Corte] [✓ Borda] [● Furação · Pedro] [Montagem] [Embalagem]                           │
└───────────────────────────────────────────────────────────────────────────────────────────┘
┌ Torre Quente · 700×2200×600 · 1×   Central Madeiranit · Pedido enviado · chega 20/10       ┐
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2. Quadro (Serviços › Produção)

```
OS              Cliente         Projeto              Status         Progresso      Prontos  Próxima           Entrega
OS-2026-000512  Studio Arq…     Res. Alpha Ville 802 Em Produção    ▒▒▒▒▒░░ 56%    2 de 6   Montagem (4)      05/11 (12 dias)
OS-2026-000498  Maria Souza     Casa Praia           Em Produção    ▒▒▒▒▒▒▒ 90%    5 de 6   Embalagem (1)     ⚠ 03/10 (5 dias atrasada)
```

---

## 7. Especificação técnica

### 7.1. Abas ⚠️

- `OSFormTabsContent`: `'producao'` em `TabType`, empurrada depois de `'separacao'` com a mesma condição; fora do `<fieldset>` travável.
- `useOSCreateFlow().openExistingOS(os, { abaInicial: 'producao' })`: parâmetro **opcional** novo; sem ele, abre na aba de hoje (`'objeto'`). Usado pelo quadro (D16).
- `OrdemServicoView`: `tabOptions` ganha `{ id: 'producao', label: 'Produção' }` antes de `'terceirizados'`, com a mesma condição; `mostrarBotaoAdicionar` devolve `false` para ela.

### 7.2. Aplicar status sem perder o formulário — `useOSFormView` ⚠️

```ts
/**
 * Grava SÓ o status da OS e reflete no modal aberto (12B D13).
 * Os demais campos editados e ainda não salvos ficam como estão.
 */
async function aplicarStatusSalvo(status: OsStatusEnumDataType) {
  const numero = currentOSData.value?.numero_os;
  if (!numero) return;
  const os = await updateOrderService({ numero_os: numero, status });   // PATCH só com o status
  currentOSData.value = { ...currentOSData.value!, status: os.status }; // o "persistido" passa a ter o novo status
  form.status.value = os.status;                                        // o campo da tela também
}
```

O "tem alterações não salvas" do modal compara com o persistido; como os dois recebem o mesmo status, a troca não aparece como alteração pendente.

### 7.3. Marcação otimista

```ts
async function concluirEtapas(ids: number[]) {
  const anterior = structuredClone(dados.value);              // para desfazer se falhar
  marcarLocalmente(ids, 'CONCLUIDA');                          // a tela muda na hora (D11)
  try {
    const resposta = await postConcluir(numeroOs.value, ids, feitoPor.value);
    dados.value = resposta;                                     // a resposta é a verdade
    if (resposta.sugestao_status) abrirSugestao(resposta.sugestao_status);   // D12
  } catch (erro) {
    dados.value = anterior;                                     // volta como estava
    toast.error('Não foi possível marcar a etapa', mensagemDoErro(erro));
  }
}
```

---

## 8. Prova de não regressão (⚠️ PR1)

1. `npm run test` e `npx vue-tsc --noEmit`.
2. Abas do modal de OS e da tela de Serviços nos outros segmentos iguais às de hoje (snapshots).
3. `openExistingOS(os)` sem o parâmetro novo abre na aba "objeto", como hoje (painel de notificações, dashboard, lista).
4. Configurações › Marcenaria continua editando etapas e checklist com o `ListaTextosEditavel` no novo lugar.

## 9. Limitações conhecidas

- O "Feito por" (D6) confia em quem está no computador; não há login por pessoa na fábrica nesta fase.
- Sem tempo por etapa nem relatório de produtividade.

---

## 10. Critérios de aceite

- [x] Aba Produção só na marcenaria, com progresso, previsão, "Concluir em todos" e um cartão por móvel com os chips.
- [x] Um clique conclui; fora de ordem pede confirmação; reabrir pelo menu; iniciar com responsável; seleção em lote.
- [x] "Feito por" muda o responsável das próximas marcações.
- [x] Terceirizado aparece com a situação e fica pronto quando conferido.
- [x] Editar etapas de um móvel; aplicar etapas padrão quando faltam.
- [x] Pergunta de "Em Produção" e de "Aguardando Entrega"; "Mover" troca só o status sem perder o resto do formulário.
- [x] Quadro em Serviços › Produção, ordenado pela previsão, abrindo a OS na aba Produção.
- [x] Nenhum preço. Prova de não regressão (§8). Código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Abas da OS na marcenaria | … Serviços e Peças, Separação, Produção, Orçamento |
| 02 | Abas da OS na informática | Iguais às de hoje |
| 03 | Clique no chip da próxima etapa | Conclui sem confirmação |
| 04 | Clique num chip que não é o próximo | Confirmação "Concluir Montagem antes de Borda?" |
| 05 | "Concluir em todos: Corte (2)" | Um POST; os 2 chips ficam verdes |
| 06 | Falha de rede ao concluir | Chip volta ao estado anterior; toast |
| 07 | Resposta com `sugestao_status` | Modal com o rótulo "Em Produção" |
| 08 | "Mover" com observação não salva no formulário | Status gravado; observação continua pendente e não é enviada |
| 09 | "Feito por" = Pedro, concluir | Requisição com o funcionário Pedro |
| 10 | Móvel `sem_etapas` | Aviso e "Aplicar etapas padrão" |
| 11 | `EditarEtapasModal` com etapa concluída | Sem remover nem renomear nela |
| 12 | Quadro: ordem | Pela previsão, a mais próxima primeiro |
| 13 | Quadro: clique na OS | Modal da OS aberto na aba Produção |
| 14 | `openExistingOS` sem `abaInicial` | Aba "objeto" |

### Roteiro manual (computador da fábrica)

1. OS aprovada com 6 móveis (1 terceirizado): "Concluir em todos: Corte"; aceitar "Em Produção".
2. Trocar o "Feito por" e concluir Borda em 3 móveis pelo modo seleção.
3. Incluir "Pintura" num móvel; tentar remover uma etapa concluída.
4. Concluir tudo com o terceirizado só recebido (sem pergunta); conferir o terceirizado (pergunta "Aguardando Entrega").
5. Serviços › Produção com 3 OS; abrir uma pelo quadro.
6. Informática: §8.
