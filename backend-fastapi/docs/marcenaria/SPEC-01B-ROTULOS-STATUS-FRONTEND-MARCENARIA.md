# Spec 01B — Rótulos de Status por Segmento (Frontend)

| Campo        | Valor                                                                |
|--------------|----------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                      |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado                |
| Dependências | Spec 01A (contrato com `rotulos_status`)                             |
| Bloqueia     | Spec 03B                                                             |
| Referência   | SPEC-00: P2a, PR1, PR6 · SPEC-01A §4.1                               |

> **Revisão 1 (06/10/2026) — decisão do usuário:** a correção do rótulo de **desfecho** na lista e no filtro (§8) **entra nesta spec**. É a única mudança visível fora da marcenaria: a serigrafia passa a mostrar na lista o mesmo texto que já vê ao finalizar e imprimir ("Não produzido", "Perda na produção"). Exceção aprovada ao PR1, registrada na SPEC-00 (Revisão 2).

---

## 1. Objetivo

Fazer as telas do frontend mostrarem o texto de status que o segmento declarou em `definicao.rotulos_status` (Spec 01A), mantendo **intactos** os valores enviados à API, as cores, a ordem e as chaves de filtro.

Na marcenaria, a lista, o filtro, o modal da OS, o histórico do cliente, o dashboard e o relatório passam a dizer "Em Produção", "Aguardando Material" e "Aguardando Entrega". Nos outros segmentos, nenhuma tela muda.

## 2. Escopo

**Dentro do escopo**
- Tipo do contrato (`rotulos_status`).
- Composable novo `useRotulosStatusOS`, com fallback enquanto o contrato carrega.
- `getEstadoOS` aceitando rótulos opcionais (continua função pura).
- Opções do select de status e do filtro, montadas com o rótulo do segmento.
- Rótulo de **desfecho** (`rotulos_situacao`) no badge e no filtro (§8, Revisão 1).
- Telas: lista de OS, resumo da OS, histórico do cliente, modal de status, dashboard (Atividade de Hoje e título "Aguardando Retirada") e relatório de desempenho de OS.
- Testes (vitest) e roteiro manual.

**Fora do escopo**
- Backend (Spec 01A).
- Impressão A4 e cupom: **não imprimem status** (conferido em `OSPrintTemplate.vue`, `OSPrintCupom.vue` e `osToEscPos.ts`). O desfecho impresso já usa `rotulos_situacao`.
- Widget "OS por status" do dashboard: já recebe `status_label` pronto do backend (Spec 01A). Só conferir.
- Status de venda e de contas a pagar/receber (outros enums).

---

## 3. Arquivos afetados

```
frontend/src/modules/
├── order-service/
│   ├── shared/
│   │   ├── segmento/
│   │   │   ├── segmentDefinition.type.ts        # ALTERAR — tipo de rotulos_status
│   │   │   ├── useRotulosStatusOS.ts            # CRIAR — composable dos rótulos
│   │   │   └── __tests__/
│   │   │       └── useRotulosStatusOS.spec.ts   # CRIAR
│   │   └── utils/
│   │       ├── formatters.ts                    # ALTERAR — getEstadoOS(status, situacao, rotulos?)
│   │       └── __tests__/
│   │           └── formatters.spec.ts           # CRIAR — getEstadoOS
│   ├── ordens/
│   │   ├── constants/ordemServico.constants.ts  # ALTERAR — montadores das opções/filtro
│   │   ├── components/OSTable.vue               # ALTERAR — badge e filtro
│   │   ├── components/form/OSSummaryCard.vue    # ALTERAR — badge do resumo
│   │   ├── components/form/OSClientHistoryModal.vue # ALTERAR — badge do histórico
│   │   ├── composables/modal/useOSSelectOptions.ts  # ALTERAR — select de status
│   │   ├── components/OSPrintTemplate.vue       # CONFERIR — não imprime status
│   │   ├── components/OSPrintCupom.vue          # CONFERIR — idem
│   │   ├── components/osToEscPos.ts             # CONFERIR — idem
│   │   └── docs/order-service.md                # ALTERAR — seção "Rótulos de status"
├── home/components/dashboard/
│   ├── AtividadeHoje.vue                        # ALTERAR — rótulo curto das OS
│   ├── OSAguardandoRetiradaTable.vue            # ALTERAR — título do card
│   └── OSPorStatusWidget.vue                    # CONFERIR — usa status_label do backend
└── reports/components/
    └── OSPerformanceSection.vue                 # ALTERAR — rótulo do status
```

**Responsabilidade de cada camada:**

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `useRotulosStatusOS.ts` | Lê o contrato (ou o fallback) e responde "qual texto mostrar para este status" | Cores, ordem, regras |
| `formatters.getEstadoOS` | Junta status + desfecho + rótulos recebidos por parâmetro | Ler contrato ou store (continua pura e testável) |
| `ordemServico.constants.ts` | Textos e cores **padrão**; montadores de opções e filtro | Saber de segmento |
| Componentes | Chamam o composable e exibem | Ter mapa próprio de rótulos de OS |

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | `OS_ESTADO_CONFIG` continua sendo a fonte **única** de cores e do texto **padrão**. O segmento só **substitui o `label`** | Cores e ordem iguais em todo segmento; o comentário do arquivo já proíbe mapas locais |
| D2 | `getEstadoOS` ganha um 3º parâmetro **opcional** com os rótulos. Sem ele, devolve exatamente o que devolve hoje | Função continua pura; quem não passa nada (ou outro segmento) não muda |
| D3 | Composable novo `useRotulosStatusOS`, com **fallback por segmento** enquanto o contrato carrega | Mesmo padrão do `useCapacidades`: evita a lista abrir com "Em Andamento" e trocar para "Em Produção" um instante depois |
| D4 | O fallback **repete** os textos da Spec 01A. Quando o contrato chega, ele manda | Igual ao `FALLBACK_POR_SEGMENTO` existente. Divergência entre os dois só aparece por uma fração de segundo |
| D5 | O **valor** de cada opção (select e filtro) continua sendo o código do enum | O filtro salvo em `localStorage` (`STORAGE_KEY_OS_FILTER`) e a API usam o código; trocar o valor apagaria o filtro salvo |
| D6 | Telas com texto **curto** próprio (Atividade de Hoje: "P/ Retirada", "Andamento") só trocam o texto quando o segmento declara um rótulo; senão, mantêm o delas | Não uniformizar os curtos dos outros segmentos (PR1) |
| D7 | `rotuloStatusProprio()` devolve `undefined` quando o segmento não renomeia; `rotuloStatus()` já devolve o texto final com o padrão | Os dois casos de uso aparecem: telas com padrão próprio (D6) e telas que usam o padrão de `OS_ESTADO_CONFIG` |
| D8 | Nenhum `if (segmento === 'marcenaria')` em componente. O único lugar que conhece o nome do segmento é o mapa de fallback, como em `useCapacidades.ts` | Regra do registry |

---

## 5. Contrato consumido

`GET /api/v1/ordens-servico/definicao-campos` (Spec 01A §5.1), já lido por `useOSFieldDefinition()`. Na marcenaria:

```json
"rotulos_status": {
  "EM_ANDAMENTO": { "rotulo": "Em Produção", "curto": "Em produção" },
  "AGUARDANDO_PECAS": { "rotulo": "Aguardando Material", "curto": "Aguard. material" },
  "AGUARDANDO_RETIRADA": { "rotulo": "Aguardando Entrega", "curto": "Aguard. entrega" }
}
```

Nos outros segmentos a chave não existe. O tipo do contrato é uma `interface` TypeScript (sem zod), então a chave nova não quebra nenhuma validação.

---

## 6. Especificação técnica

### 6.1. Tipo — `segmentDefinition.type.ts`

```ts
/** Texto de um status da OS declarado pelo segmento (Spec 01A). */
export interface RotuloStatus {
  /** Texto completo: lista, filtro, modal, relatório. */
  rotulo: string;
  /** Texto abreviado: dashboard. */
  curto: string;
}

// Dentro de SegmentDefinition, ao lado de rotulos_situacao:
  /**
   * Texto de cada STATUS da OS, por chave do enum. Opcional: ausente = textos
   * padrão de OS_ESTADO_CONFIG. Só o texto muda; o valor enviado à API é o
   * mesmo enum de todos os segmentos.
   */
  rotulos_status?: Partial<Record<OsStatusEnumDataType, RotuloStatus>>;
```

### 6.2. Formatador — `formatters.ts`

```ts
/** Rótulos que o segmento declarou; todos opcionais (Spec 01B, D2). */
export interface RotulosEstadoOS {
  status?: Partial<Record<OsStatusEnumDataType, RotuloStatus>>;
  /** Desfecho: `rotulos_situacao` do contrato (ex.: SEM_REPARO -> "Não produzido"). */
  situacao?: Record<string, string>;
}

export function getEstadoOS(
  status: OsStatusEnumDataType | null | undefined,
  situacao?: OsEquipSituacaoEnumDataType | null,
  rotulos?: RotulosEstadoOS,                       // novo e opcional: sem ele, nada muda
): OsEstadoConfig {
  // Regra do desfecho: QUANDO ele aparece continua igual a hoje (não alterar).
  if (status === 'FINALIZADA' && situacao && situacao !== 'REPARADO') {
    const padraoDesfecho = OS_ESTADO_CONFIG[situacao];        // cores e texto de conserto
    const textoDesfecho = rotulos?.situacao?.[situacao];       // "Não produzido", se o segmento declarou
    // Sem rótulo do segmento: o mesmo objeto de hoje. Com rótulo: troca só o texto (§8).
    return textoDesfecho ? { ...padraoDesfecho, label: textoDesfecho } : padraoDesfecho;
  }
  const chave = status ?? 'ABERTA';                       // OS sem status = Aberta, como hoje
  const padrao = OS_ESTADO_CONFIG[chave] ?? OS_ESTADO_CONFIG.ABERTA; // cores e texto padrão
  const proprio = rotulos?.status?.[chave as OsStatusEnumDataType];  // texto do segmento, se houver
  // Copia o padrão e troca SÓ o label; as cores continuam as mesmas (D1).
  return proprio ? { ...padrao, label: proprio.rotulo } : padrao;
}
```

**Atenção:** quando não há rótulo próprio, a função devolve **o mesmo objeto** de hoje (não uma cópia). Isso mantém o comportamento idêntico para os outros segmentos.

### 6.3. Montadores — `ordemServico.constants.ts`

Transformar a montagem de `OS_STATUS_OPTIONS` e `OS_STATUS_FILTER_CONFIG` em funções que recebem quem dá o texto. As constantes continuam existindo, montadas com o texto padrão, e produzem **exatamente** o mesmo resultado de hoje.

```ts
/** Ordem do fluxo no select de status (igual à de hoje). */
const OS_STATUS_ORDEM = [
  'ABERTA', 'EM_ANDAMENTO', 'AGUARDANDO_PECAS', 'AGUARDANDO_APROVACAO',
  'AGUARDANDO_RETIRADA', 'FINALIZADA', 'CANCELADA',
] as const;

/** Quem decide o texto: por padrão, o label de OS_ESTADO_CONFIG. */
type TextoDoEstado = (chave: OsEstadoKey) => string;
const textoPadrao: TextoDoEstado = (chave) => OS_ESTADO_CONFIG[chave].label;

export function montarOpcoesStatus(texto: TextoDoEstado = textoPadrao) {
  // value = código do enum (vai para a API); label = texto exibido (D5)
  return OS_STATUS_ORDEM.map((value) => ({ value, label: texto(value) }));
}

export function montarFiltroStatus(texto: TextoDoEstado = textoPadrao): Record<string, FilterOption> {
  return Object.fromEntries(
    (Object.keys(OS_ESTADO_CONFIG) as OsEstadoKey[])
      .filter((key) => !OS_FILTRO_OCULTOS.includes(key))   // CANCELADA continua fora
      .map((key) => [
        key,                                               // chave = código (D5)
        { label: texto(key), class: OS_ESTADO_CONFIG[key].badge, color: OS_ESTADO_CONFIG[key].dot },
      ]),
  );
}

// Constantes de sempre, agora montadas pelas funções: mesmo conteúdo de antes.
export const OS_STATUS_OPTIONS = montarOpcoesStatus();
export const OS_STATUS_FILTER_CONFIG = montarFiltroStatus();
```

### 6.4. Composable — `useRotulosStatusOS.ts`

```ts
import { computed } from 'vue';

import { useSegmento } from '@/shared/composables/useSegmento';
import { OS_ESTADO_CONFIG, montarFiltroStatus, montarOpcoesStatus } from '../../ordens/constants/ordemServico.constants';
import type { OsEquipSituacaoEnumDataType, OsStatusEnumDataType } from '../../ordens/schemas/enums/osEnums.schema';
import { getEstadoOS } from '../utils/formatters';
import type { RotuloStatus } from './segmentDefinition.type';
import { useOSFieldDefinition } from './useOSFieldDefinition.queries';

type RotulosStatus = Partial<Record<OsStatusEnumDataType, RotuloStatus>>;

/**
 * Textos usados SÓ enquanto o contrato carrega (D3, D4). Repete a declaração
 * do backend (app/core/segmentos/definicoes/marcenaria.py). Quando o contrato
 * chega, ele manda. Mudou lá? Mude aqui também.
 */
const ROTULOS_STATUS_FALLBACK_POR_SEGMENTO: Record<string, RotulosStatus> = {
  marcenaria: {
    EM_ANDAMENTO: { rotulo: 'Em Produção', curto: 'Em produção' },
    AGUARDANDO_PECAS: { rotulo: 'Aguardando Material', curto: 'Aguard. material' },
    AGUARDANDO_RETIRADA: { rotulo: 'Aguardando Entrega', curto: 'Aguard. entrega' },
  },
};

export function useRotulosStatusOS() {
  const { data, isPending } = useOSFieldDefinition();  // contrato do segmento (já em cache)
  const { segmento } = useSegmento();                  // segmento da empresa logada

  /** Rótulos em vigor: fallback enquanto carrega, contrato depois. */
  const rotulosStatus = computed<RotulosStatus>(() => {
    if (isPending.value) return ROTULOS_STATUS_FALLBACK_POR_SEGMENTO[segmento.value ?? ''] ?? {};
    return data.value?.definicao?.rotulos_status ?? {};   // sem a chave = nenhum rótulo próprio
  });

  /** Texto declarado pelo segmento, ou undefined (D7). Para telas com padrão próprio. */
  function rotuloStatusProprio(status: OsStatusEnumDataType, curto = false): string | undefined {
    const proprio = rotulosStatus.value[status];
    if (!proprio) return undefined;
    return curto ? proprio.curto : proprio.rotulo;
  }

  /** Texto final: o do segmento ou o padrão de OS_ESTADO_CONFIG. */
  function rotuloStatus(status: OsStatusEnumDataType): string {
    return rotuloStatusProprio(status) ?? OS_ESTADO_CONFIG[status].label;
  }

  /** Desfecho: o contrato já traz `rotulos_situacao` (serigrafia e marcenaria). */
  const rotulosSituacao = computed<Record<string, string>>(
    () => data.value?.definicao?.rotulos_situacao ?? {},
  );

  /** getEstadoOS já com os rótulos do segmento (cores intactas). */
  function estadoOS(
    status: OsStatusEnumDataType | null | undefined,
    situacao?: OsEquipSituacaoEnumDataType | null,
  ) {
    return getEstadoOS(status, situacao, { status: rotulosStatus.value, situacao: rotulosSituacao.value });
  }

  /** Texto usado pelos montadores: status do fluxo E desfechos (SEM_REPARO/CONDENADO). */
  const texto = (chave: string) =>
    rotulosStatus.value[chave as OsStatusEnumDataType]?.rotulo   // status renomeado
    ?? rotulosSituacao.value[chave]                              // desfecho renomeado (§8)
    ?? OS_ESTADO_CONFIG[chave as keyof typeof OS_ESTADO_CONFIG].label; // padrão

  const statusOptions = computed(() => montarOpcoesStatus(texto));      // select do modal
  const statusFilterConfig = computed(() => montarFiltroStatus(texto)); // menu de filtro

  return { rotuloStatus, rotuloStatusProprio, estadoOS, statusOptions, statusFilterConfig };
}
```

### 6.5. Telas

| Arquivo | Hoje | Depois |
|---------|------|--------|
| `OSTable.vue` | `getEstadoOS(os.status, os.situacao_equipamento)`; `:filter-config="OS_STATUS_FILTER_CONFIG"` | `estadoOS(...)`; `:filter-config="statusFilterConfig"` |
| `OSSummaryCard.vue` | `getEstadoOS(props.status, props.situacaoEquipamento)` | `estadoOS(...)` |
| `OSClientHistoryModal.vue` | `getEstadoOS(...)` | `estadoOS(...)` |
| `useOSSelectOptions.ts` | filtra `OS_STATUS_OPTIONS` | filtra `statusOptions.value` (mesma regra de FINALIZADA/CANCELADA) |
| `AtividadeHoje.vue` | `statusConfig[item.status]?.label` | `rotuloStatusProprio(item.status, true) ?? statusConfig[item.status]?.label` — **só** para itens de OS; itens de venda não mudam (D6) |
| `OSAguardandoRetiradaTable.vue` | título fixo "Aguardando Retirada" | `rotuloStatus('AGUARDANDO_RETIRADA')`. Nos outros segmentos o texto é o mesmo de hoje |
| `OSPerformanceSection.vue` | `statusLabel(s)` monta o texto a partir do código | `rotuloStatusProprio(s) ?? statusLabel(s)` |

**Atividade de Hoje:** a lista mistura vendas e OS, e `FINALIZADA` existe nas duas. O item traz `tipo: 'venda' | 'os'` (`home/schemas/dashboard.schema.ts`). Aplicar o rótulo **só** quando `item.tipo === 'os'`. Como a marcenaria não renomeia `FINALIZADA`, o risco hoje é baixo, mas a regra precisa estar no código para o próximo segmento que renomear.

### 6.6. Documentação — `order-service.md`

Nova seção "Rótulos de status por segmento", explicando: o enum não muda; o texto vem de `useRotulosStatusOS`; nenhum componente cria mapa próprio de rótulos de OS; o fallback precisa acompanhar o backend.

---

## 7. Prova de não regressão (⚠️ PR1)

1. **Testes:** `npm run test` inteiro antes e depois; `npx vue-tsc --noEmit` = 0 erros (o `npm run build` não roda o type-check).
2. **Igualdade das constantes:** os casos 01 e 02 comparam `OS_STATUS_OPTIONS` e `OS_STATUS_FILTER_CONFIG` com um snapshot **gerado antes da mudança** (via `git show HEAD:` do arquivo).
3. **Olho na tela** (o projeto já aprendeu que teste não pega tudo): em informática, oficina e serigrafia, com o backend em `fastapi dev` e `npm run tauri dev`, comparar **antes × depois**: lista de OS (badges e filtro), modal da OS (select de status e resumo), histórico do cliente, dashboard (Atividade de Hoje, OS por status, título "Aguardando Retirada") e relatório de OS. Diferença esperada: **zero**.
4. **Varredura** que o type-check não faz: nenhum componente PascalCase sem import nos arquivos tocados.

## 8. Correção do desfecho na lista e no filtro (aprovada em 06/10)

Hoje, uma OS finalizada como `SEM_REPARO` aparece na lista com o badge **"Sem Reparo"**, em **qualquer** segmento. Mas a marcenaria e a serigrafia declaram `rotulos_situacao`, e a finalização e a impressão já dizem **"Não produzido"**. O usuário vê uma palavra ao finalizar e outra na lista.

| | Marcenaria | Serigrafia (em produção nas lojas) |
|---|---|---|
| Finalização e impressão (hoje) | "Não produzido" | "Não produzido" |
| Lista e filtro (hoje) | "Sem Reparo" ❌ | "Sem Reparo" ❌ |
| Lista e filtro (com a correção) | "Não produzido" | "Não produzido" |

**Como corrigir** (já incorporado às §6.2 e §6.4): `RotulosEstadoOS` ganha `situacao?: Record<string, string>`; `getEstadoOS` usa esse texto no ramo do desfecho; o composable passa `definicao.rotulos_situacao`; o `texto` dos montadores usa o mesmo mapa para `SEM_REPARO` e `CONDENADO`. Cerca de 10 linhas.

**Exceção ao PR1:** a correção **muda a lista e o filtro da serigrafia**, que já está nas lojas. Não quebra nada (o filtro continua usando o código, D5) e só aproxima a lista do que a loja já vê na finalização e na impressão. Informática e oficina não declaram `rotulos_situacao` e não mudam. Aprovado pelo usuário em 06/10/2026.

**Nota da entrega para a serigrafia:** avisar as lojas de serigrafia, na atualização, que "Sem Reparo" e "Condenado" passam a aparecer na lista como "Não produzido" e "Perda na produção", os mesmos nomes da finalização.

## 9. Limitações conhecidas

- **Fallback duplicado.** Os textos da marcenaria ficam no backend e no fallback do frontend. Se alguém mudar só um lado, a diferença aparece por uma fração de segundo ao abrir a tela. É o mesmo custo aceito em `useCapacidades.ts`.
- **Textos curtos de outros segmentos não são uniformizados.** O dashboard tem dois estilos de abreviação ("Aguard. retirada" no widget, "P/ Retirada" na Atividade de Hoje). Unificar mudaria a tela dos outros segmentos; fica fora.

---

## 10. Critérios de aceite

- [ ] Na marcenaria, lista, filtro, select de status, resumo da OS, histórico do cliente, título do card do dashboard e relatório mostram "Em Produção", "Aguardando Material" e "Aguardando Entrega".
- [ ] Na Atividade de Hoje da marcenaria, as OS mostram "Em produção", "Aguard. material" e "Aguard. entrega".
- [ ] O valor enviado à API ao trocar o status continua o código do enum.
- [ ] Um filtro salvo antes da mudança continua funcionando depois (mesma chave).
- [ ] As cores de cada status são as mesmas em todos os segmentos.
- [ ] Ao abrir o app na marcenaria, a lista **não pisca** de "Em Andamento" para "Em Produção" (fallback).
- [ ] Informática e oficina: nenhuma diferença na prova da §7.
- [ ] Serigrafia: a **única** diferença é o desfecho na lista e no filtro ("Não produzido", "Perda na produção"), como na §8.
- [ ] Marcenaria: OS finalizada sem produzir aparece como "Não produzido" na lista e no filtro.
- [ ] Nenhum componente ganhou mapa próprio de rótulos de OS nem `if` por nome de segmento.
- [ ] `npm run test` verde e `npx vue-tsc --noEmit` sem erros.
- [ ] Código novo comentado (PR6).

## 11. Casos de teste

### `ordemServico.constants.ts` — `ordens/constants/__tests__/ordemServico.constants.spec.ts`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `OS_STATUS_OPTIONS` | Igual ao snapshot de antes da mudança (valores, textos e ordem) |
| 02 | `OS_STATUS_FILTER_CONFIG` | Igual ao snapshot de antes (chaves, textos, classes; sem `CANCELADA`) |
| 03 | `montarOpcoesStatus(texto)` com um `texto` que devolve `"X"` | Todos os `label` = `"X"`; os `value` continuam os códigos |
| 04 | `montarFiltroStatus(texto)` | Chaves continuam os códigos do enum |

### `formatters.ts` — `shared/utils/__tests__/formatters.spec.ts`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 05 | `getEstadoOS(s)` sem rótulos, para cada status | Mesmo objeto de `OS_ESTADO_CONFIG[s]` (comparação por identidade) |
| 06 | `getEstadoOS('AGUARDANDO_RETIRADA', null, { status: marcenaria })` | `label = 'Aguardando Entrega'`, `badge` e `dot` iguais aos do padrão |
| 07 | `getEstadoOS('ABERTA', null, { status: marcenaria })` | `label = 'Aberta'` |
| 08 | `getEstadoOS('FINALIZADA', 'SEM_REPARO', { status: marcenaria, situacao: { SEM_REPARO: 'Não produzido' } })` | `label = 'Não produzido'`, cores de `SEM_REPARO` |
| 08a | `getEstadoOS('FINALIZADA', 'CONDENADO')` sem rótulos | Mesmo objeto de `OS_ESTADO_CONFIG.CONDENADO` (informática e oficina) |
| 08b | `getEstadoOS('ABERTA', 'SEM_REPARO', { situacao: { SEM_REPARO: 'Não produzido' } })` (OS reaberta) | `'Aberta'`: o desfecho só aparece em OS finalizada, como hoje |
| 09 | `getEstadoOS(null)` | `ABERTA`, como hoje |
| 10 | `getEstadoOS('EM_ANDAMENTO', null, {})` | Padrão `'Em Andamento'` |

### `useRotulosStatusOS.ts` — `shared/segmento/__tests__/useRotulosStatusOS.spec.ts`

Com `useOSFieldDefinition` e `useSegmento` substituídos por mocks.

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 11 | Contrato carregando, segmento `marcenaria` | `rotuloStatus('AGUARDANDO_RETIRADA') = 'Aguardando Entrega'` (fallback) |
| 12 | Contrato carregando, segmento `assistencia_tecnica` | `rotuloStatus('AGUARDANDO_RETIRADA') = 'Aguardando Retirada'` |
| 13 | Contrato carregado com `rotulos_status` | Usa o contrato, mesmo que o fallback diga outra coisa |
| 14 | Contrato carregado sem a chave | Todos os textos padrão |
| 15 | `rotuloStatusProprio('ABERTA')` na marcenaria | `undefined` |
| 16 | `rotuloStatusProprio('AGUARDANDO_PECAS', true)` na marcenaria | `'Aguard. material'` |
| 17 | `statusOptions` na marcenaria | Mesmos `value` e ordem de `OS_STATUS_OPTIONS`; `label` trocado só nos três status |
| 18 | `statusFilterConfig` na marcenaria | Mesmas chaves de `OS_STATUS_FILTER_CONFIG`; `SEM_REPARO` com o texto `'Não produzido'` |
| 18a | `statusFilterConfig` com contrato sem `rotulos_situacao` (informática) | `SEM_REPARO = 'Sem Reparo'`, `CONDENADO = 'Condenado'` |

### Roteiro manual (dev)

1. Empresa de **marcenaria**: abrir a lista de OS. Os badges mostram os textos novos desde o primeiro quadro.
2. Abrir uma OS e trocar o status para "Aguardando Material". No DevTools, a requisição envia `AGUARDANDO_PECAS`.
3. Filtrar por "Aguardando Entrega", fechar e reabrir o app. O filtro continua aplicado.
4. Dashboard: card "Aguardando Entrega", Atividade de Hoje com "Aguard. entrega" e widget "OS por status" com "Aguard. entrega".
5. Relatório de OS: status com os textos novos.
6. Finalizar uma OS da marcenaria como "Não produzido". Na lista e no filtro aparece "Não produzido".
7. Repetir 1–5 em **informática e oficina**: nada mudou. Na **serigrafia**, só o desfecho na lista e no filtro mudou (§8).
