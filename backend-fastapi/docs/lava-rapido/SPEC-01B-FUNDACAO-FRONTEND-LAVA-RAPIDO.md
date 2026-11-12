# Spec 01B — Fundação do Segmento Lava-Rápido (Frontend)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026 (roteiro manual da §10 pendente)           |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado da OS            |
| Dependências | Spec 01A (contrato com `status_usados`, `gerado_se_vazio`)            |
| Bloqueia     | Specs 02B, 03, 04B                                                    |
| Referência   | SPEC-00: F1–F5, O2b, O10a, PR1, PR3, PR8 · SPEC-01A D4, D5, D8         |

---

## 1. Objetivo

Fazer o segmento lava-rápido **aparecer e funcionar na tela**:

- escolhê-lo no onboarding;
- abrir uma OS escolhendo o tipo de veículo (Carro, Moto, Caminhão/ônibus, Outros), com placa e porte;
- ver só os 4 status do fluxo (Aberta, Em Andamento, **Pronto**, Finalizada);
- imprimir as vias térmica e A4 com o vocabulário de lava-rápido.

Nos outros segmentos, **nenhuma tela muda** (PR1).

## 2. Escopo

**Dentro**
- Segmento na lista única `SEGMENTOS`, com card e dica no onboarding.
- Tipo do contrato: `identificador.gerado_se_vazio` e `status_usados`.
- Status escondidos por `status_usados` no select do modal e no filtro da lista.
- Exigência na tela dos campos obrigatórios do tipo (placa e porte), só onde o backend completa o vazio.
- Pacote de textos de impressão `LAVA_RAPIDO` (bobina e A4).
- Ícone do objeto (carro).
- Backend: `rotulo_objeto_anterior` = "Veículo já cadastrado" (D9).

**Fora** (outras specs)
- Preço e duração por porte → 02A/02B.
- Entrada rápida e cupom de entrada → 03.
- Lavadores e comissão → 10A/10B.
- Quadro do pátio e WhatsApp → 04A/04B.

## 3. Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `shared/constants/segmentos.ts` | `'lava_rapido'` na lista |
| `modules/sign-in/constants/segments.ts` | card + dica |
| `modules/sign-in/components/icons/SegmentIcons.vue` | ícone `car` |
| `order-service/shared/segmento/segmentDefinition.type.ts` | `gerado_se_vazio?`, `status_usados?` |
| `order-service/shared/segmento/useRotulosStatusOS.ts` | filtro por `status_usados` + fallback do lava |
| `order-service/shared/segmento/camposObrigatorios.ts` (novo) | função pura + composable da exigência |
| `order-service/ordens/components/OSFormModal.vue` | chama a exigência antes de salvar |
| `order-service/shared/segmento/textosImpressaoOS.ts` | pacote `LAVA_RAPIDO` |
| `order-service/shared/segmento/useObjetoLabels.ts` | ícone `Car` |
| `backend: definicoes/lava_rapido.py` | `rotulo_objeto_anterior` |

## 4. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | `'lava_rapido'` entra em `SEGMENTOS` logo após `oficina_mecanica`. Card "Lava-Rápido / Estética Automotiva", ícone de carro | Lista única: o compilador cobra card e dica (`Record<Segmento, …>`) |
| D2 | `gerado_se_vazio` e `status_usados` entram **opcionais** no tipo | Contrato antigo (sidecar velho) e os outros segmentos não os mandam |
| D3 | O filtro por `status_usados` mora **só** em `useRotulosStatusOS` — o select do modal e o filtro da lista já passam por ele | Um ponto só; nenhum componente ganha `if` |
| D4 | Ausente `status_usados` = todos os status, exatamente como hoje. Desfechos (`SEM_REPARO`, `CONDENADO`) nunca são filtrados | PR1: serigrafia, oficina, informática e marcenaria não mudam |
| D5 | Enquanto o contrato carrega, fallback do lava ("Pronto" e os 4 status), mesmo padrão do `ROTULOS_STATUS_FALLBACK_POR_SEGMENTO` | A lista não abre com "Aguardando Retirada" e troca para "Pronto" |
| D6 | Campos com `obrigatorio` do tipo escolhido são **exigidos na tela** só quando o identificador é `gerado_se_vazio` | É o único caso em que o backend aceita a placa vazia (gera `VEI-…`) e não confere o porte (JSON). Nos outros segmentos a aba dinâmica continua como está |
| D7 | A exigência bloqueia o salvar com um toast "Preencha: Placa, Porte." | Mesmo canal de aviso que o formulário já usa para o 422 do backend |
| D8 | Pacote de impressão próprio: substantivo "veículo", cláusula da vistoria de entrada (avaria pré-existente), de objetos pessoais e de peças soltas ou não originais; prazo de retirada com os dias da configuração, como os outros | O texto do cliente é proposta; a palavra final é do dono da loja |
| D9 | `rotulo_objeto_anterior` declarado no backend ("Veículo já cadastrado") | O padrão monta "Veículo já cadastrad**a**" (escrito para "Arte") |
| D10 | Porte, carroceria e placa do implemento **não** ganham componente: são `opcao`/`texto` desenhados pelo `CampoDinamico` | Segmento novo custa declaração, não Vue |
| D11 | Nenhum `if (segmento === 'lava_rapido')` em componente. O nome do segmento só aparece nos mapas de fallback e de ícone, como já acontece com os outros | Regra do registry |

## 5. Contrato consumido

```jsonc
"identificador": { "nome": "placa", "label": "Placa", "regex": null, "gerado_se_vazio": true, "prefixo": "VEI" },
"status_usados": ["ABERTA","EM_ANDAMENTO","AGUARDANDO_RETIRADA","FINALIZADA","CANCELADA"],
"rotulos_status": { "AGUARDANDO_RETIRADA": { "rotulo": "Pronto", "curto": "Pronto" } },
"rotulo_objeto_anterior": "Veículo já cadastrado",
"tipos": [ { "id": "carro", "campos": [ { "nome": "placa", "obrigatorio": true, "origem": "coluna", "coluna": "numero_serie" }, { "nome": "porte", "tipo": "opcao", "obrigatorio": true }, … ] }, … ]
```

## 6. Especificação técnica

### 6.1. Status — `useRotulosStatusOS.ts`

```ts
const usados = computed<string[] | null>(() => isPending ? FALLBACK[segmento] ?? null : definicao?.status_usados ?? null);
const usado = (chave) => !usados.value || !ehStatusDoEnum(chave) || usados.value.includes(chave);
statusOptions      = montarOpcoesStatus(texto).filter((o) => usado(o.value));
statusFilterConfig = Object.fromEntries(Object.entries(montarFiltroStatus(texto)).filter(([k]) => usado(k)));
```

### 6.2. Exigência — `camposObrigatorios.ts`

- `camposObrigatoriosVazios(campos, valores)`: função pura; devolve os **rótulos** dos campos `obrigatorio` cujo valor está vazio (string em branco, `null`, `undefined`, lista vazia).
- `useCamposObrigatoriosDoTipo()`: lê o contrato; devolve `faltando(objetoForm, objetoDados, osDados)`. Devolve `[]` quando o identificador não é `gerado_se_vazio` (D6). Resolve o valor de cada campo pelo mesmo critério da aba dinâmica (`coluna` → form; `escopo os` → dados da OS; senão dados do objeto).

### 6.3. `OSFormModal.vue`

No `handleLocalSubmit`, antes de criar ou de salvar a OS inteira (não no modo só-texto da reabertura):

```ts
const faltando = faltandoNoFormulario(objetoFormData.value, objetoDados.value, osDados.value);
if (faltando.length) { toast.error(`Preencha: ${faltando.join(', ')}.`); return; }
```

## 7. Prova de não regressão (⚠️ PR1)

- `useRotulosStatusOS.spec.ts`: testes existentes continuam iguais; novos provam que **sem** `status_usados` as listas são idênticas a `OS_STATUS_OPTIONS`/`OS_STATUS_FILTER_CONFIG`.
- `textosImpressaoOS.spec.ts`: snapshots de oficina, informática e serigrafia intactos.
- `camposObrigatorios.spec.ts`: segmento sem `gerado_se_vazio` (serigrafia, marcenaria) → nunca exige nada.
- `npx vue-tsc --noEmit` e suíte do vitest inteira antes e depois.

## 8. Limitações conhecidas

- A placa é gravada como digitada (o `CampoDinamico` não põe em maiúsculas). A busca e a deduplicação não sofrem: o backend compara pela forma normalizada (`identificador_pesquisavel`).
- OS que já esteja num status fora de `status_usados` (impossível no lava, que nasce agora) mostraria "--" no select.

## 9. Critérios de aceite

1. O onboarding mostra o card "Lava-Rápido / Estética Automotiva" e cadastra a empresa.
2. Nova OS: escolhe Carro/Moto/Caminhão/Outros; Carro sem placa ou sem porte não salva e avisa o que falta; Outros sem placa salva e ganha `VEI-…`.
3. Select de status e filtro da lista sem "Aguardando Peças" e "Aguardando Aprovação"; "Pronto" no lugar de "Aguardando Retirada".
4. Vias térmica e A4 falam de veículo, placa e pedido do cliente.
5. Oficina, informática, serigrafia e marcenaria: nada muda (testes da §7).

## 10. Casos de teste

### `useRotulosStatusOS.spec.ts`
- L1 — lava (contrato): select sem `AGUARDANDO_PECAS`/`AGUARDANDO_APROVACAO`, com "Pronto".
- L2 — lava (contrato): filtro sem os dois, com `SEM_REPARO` e `CONDENADO`.
- L3 — lava (carregando): fallback já esconde os dois e diz "Pronto".
- L4 — contrato sem `status_usados`: listas idênticas às constantes padrão.

### `camposObrigatorios.spec.ts`
- C1 — vazio, espaço, `null`, lista vazia contam como vazio; `0` e `false` não.
- C2 — Carro sem placa e sem porte → `["Placa", "Porte"]`.
- C3 — Outros sem placa → `[]` (placa não obrigatória).
- C4 — segmento sem `gerado_se_vazio` → `[]` sempre.

### `textosImpressaoOS.spec.ts`
- T1 — pacote do lava fala "veículo" e não fala de backup, chip ou estampa.

### Roteiro manual (dev)
1. Criar empresa lava-rápido pelo onboarding.
2. Abrir OS de carro sem placa → aviso; com placa e porte → salva.
3. Abrir OS "Outros" sem placa → salva com `VEI-…`.
4. Mudar status para Pronto; conferir lista, filtro e dashboard.
5. Imprimir térmica e A4.
