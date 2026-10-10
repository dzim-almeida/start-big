# Spec 14 — Etiquetas por Volume do Móvel (Frontend)

| Campo        | Valor                                                                              |
|--------------|------------------------------------------------------------------------------------|
| Status       | Implementada em 09/10/2026                                                         |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ `shared/etiquetas` (só acréscimos)                |
| Dependências | Specs 12B (aba Produção), 13A (código do projeto e endereço da obra) · motor `frontend/src/shared/etiquetas/` (usado como é) |
| Bloqueia     | —                                                                                  |
| Referência   | SPEC-00: I7, P3, P4, FB2 · PR1, PR3, PR6                                           |

> **Implementação (09/10/2026) — o que o código acrescenta ou decide além do texto.**
> (1) **Motor (FB2):** só acréscimos — 7 campos novos na união `CampoEtiqueta` e a lista `CAMPOS_MOVEL`; `gerarMovel` ao lado de `gerarVolume`, com os mesmos ajudantes; `PRESETS_MOVEL` como lista própria. Um teste congela as chaves de `PRESETS`, `PRESETS_VOLUME` e `PRESETS_DANFE` e confere que os campos novos não entram nas listas de produto e de envio; os testes do motor que já existiam passam sem mudança.
> (2) **Onde está a OS:** projeto (o nº de série do objeto, PRJ), endereço da obra (`dados_adicionais.endereco_obra` do objeto) e cliente vêm da OS aberta no modal (o `OSFormTabsContent` passa para a aba Produção); a empresa, do cadastro (`useCompanyPrintInfo`). Nenhuma chamada nova à API.
> (3) **"Etiquetas"** fica no topo da aba Produção mesmo com a OS fechada (imprimir não muda nada), com os móveis prontos marcados. O menu "⋯" de TODO cartão (inclusive o do terceirizado, D9) ganhou "Imprimir etiquetas"; "Editar etapas" continua só no móvel da fábrica com a OS aberta.
> (4) **Oferta (D8):** quando um "concluir" deixa móveis prontos, o toast de sucesso traz "Imprimir etiquetas" com só esses móveis marcados ("Balcão ficou pronto." ou "3 móveis ficaram prontos.").
> (5) **Modelo lembrado (D11):** chave própria no `localStorage` deste computador (`startbig.marcenaria.etiqueta_modelo`), com `try/catch`; o store de impressão compartilhado não ganhou campo novo. Sem armazenamento, volta ao A4 em 4.
> (6) **Título do PDF:** "Etiquetas OS-…" durante a impressão pelo driver, devolvido no `afterprint`; na térmica direta (sem diálogo), devolvido na hora.

> **Revisão 1 (08/10/2026) — spec reescrita (SPEC-00 Revisão 15, FB2).** A versão de 06/10 desenhava formatos de folha, "começar na etiqueta nº", ajuste fino guardado no navegador, página de teste e impressão ESC/POS próprios. A branch recebeu em 08/10 o **motor de etiquetas** (`shared/etiquetas`), que já faz tudo isso: modelo neutro em milímetros, folhas A4/Carta (Pimaco/Avery), "pular N posições" da folha usada (`paginacao.ts`), calibração por terminal com "Imprimir teste" (store de impressão), impressão no driver ou **nativa** na térmica (ZPL/TSPL/PPLA), e até a etiqueta de **volume** de envio. Esta spec passa a só **acrescentar** ao motor os campos do móvel, um layout e três modelos prontos, e a montar a lista de etiquetas na aba Produção.

---

## 1. Objetivo

Imprimir uma **etiqueta por volume** de cada móvel embalado (I7), para o caminhão sair com tudo identificado e o montador saber, na obra, de que ambiente é cada caixa:

- **Código do projeto (PRJ)** e **número da OS**, em destaque.
- **Cliente** e **endereço da obra**.
- **Ambiente**, **móvel** e **medidas**.
- **Volume** "2 de 5".

Sem backend novo: os dados já chegam pela aba Produção (12A) e pela OS.

## 2. Escopo

**Dentro do escopo**
- Campos novos no catálogo do motor (`campos.ts`), um layout (`gerarMovel`) e três modelos prontos (`PRESETS_MOVEL`).
- Modal "Imprimir etiquetas" na aba Produção (todos os móveis, selecionados ou um só), com volumes por móvel.
- Impressão pelo `useImpressaoEtiquetas` do motor.

**Fora do escopo**
- Modelo de etiqueta **da loja** para o móvel (editor visual): os modelos desta fase são só os prontos. Fica para quando o uso pedir.
- Etiqueta por **peça** (I7: só com importação 3D, fase 2).
- Código de barras ou QR para conferência na entrega: o motor já desenha (`ElementoBarras`, `ElementoQr`), mas nada lê esse código nesta fase.
- Qualquer mudança no comportamento das etiquetas de produto e de envio (FB2).

---

## 3. Arquivos afetados

```
frontend/src/
├── shared/etiquetas/                          ⚠️ só acréscimos (FB2)
│   ├── campos.ts                              # ALTERAR — 7 campos novos + CAMPOS_MOVEL
│   ├── layoutEnvio.ts                         # ALTERAR — export gerarMovel (ao lado de gerarVolume)
│   ├── presets.ts                             # ALTERAR — PRESETS_MOVEL (lista própria)
│   └── __tests__/movel.spec.ts                # CRIAR
└── modules/marcenaria/etiquetas/
    ├── utils/montarEtiquetas.ts               # CRIAR — móveis × volumes → ValoresEtiqueta[]
    └── components/ImprimirEtiquetasModal.vue  # CRIAR
frontend/src/modules/marcenaria/producao/components/
├── OSProducaoTab.vue                          # ALTERAR — botão "Etiquetas"
└── MovelProducaoCard.vue                      # ALTERAR — "Imprimir etiquetas" no menu
```

Usados como são: `useImpressaoEtiquetas` (impressão no driver ou nativa), `EtiquetasImpressao.vue` (as folhas), `useImpressaoStore` (calibração do terminal: `etiqueta_deslocamento_x_mm`/`_y_mm`), `paginar` ("pular N posições").

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `campos.ts`, `layoutEnvio.ts`, `presets.ts` | Declarar o que a etiqueta do móvel pode mostrar e um desenho pronto | Mudar os campos, layouts e presets que existem |
| `montarEtiquetas.ts` | Transformar móveis e volumes em valores de campo | Desenhar |
| `ImprimirEtiquetasModal.vue` | Escolher modelo, móveis, volumes e posição inicial | Calibrar a impressora (é a tela do motor) |

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | **Uma etiqueta por volume.** No modal, cada móvel tem o campo **"Volumes"**, que começa com a **quantidade** do móvel (3 aéreos = 3 volumes) e pode ser mudado (um guarda-roupa sai em 5 caixas). Numeração por móvel: "VOLUME 2 DE 5" | I7. O número de caixas só se sabe na embalagem |
| D2 | **Campos novos** em `CampoEtiqueta` (acréscimo à união): `os.numero`, `projeto.codigo`, `projeto.endereco_obra`, `cliente.nome`, `movel.nome`, `movel.ambiente`, `movel.medidas`. Reusa os que existem: `volume.contador`, `volume.rotulo`, `empresa.nome`. Lista `CAMPOS_MOVEL` com os rótulos para tela | Os campos de envio (`destinatario.*`, `envio.*`) têm outro sentido; reaproveitá-los confundiria quem editar um modelo um dia |
| D3 | **Layout `gerarMovel(pagina)`** em `layoutEnvio.ts`, ao lado de `gerarVolume` e com os mesmos ajudantes (`empilhar`, `rotulo`): PRJ e OS (maior), móvel (negrito), ambiente, medidas, VOLUME N DE T (negrito, centro), cliente, endereço da obra (até 2 linhas), empresa (pequeno). Abaixo de 90 mm de altura, a versão compacta (sem empresa e com o endereço em 1 linha), como a `gerarVolume` faz | O código e a OS identificam no depósito; móvel e ambiente orientam a montagem; o endereço orienta o motorista |
| D4 | **Modelos prontos `PRESETS_MOVEL`**, numa lista **própria** (não entram em `PRESETS` nem em `PRESETS_VOLUME`), com `fonte: 'volume'` (o tipo `FonteEtiqueta` não muda): "Móvel — folha A4 em 4" (105 × 148,5 mm, impressora comum, o padrão), "Móvel 100 × 150 mm" e "Móvel 100 × 50 mm" (térmica) | Lista própria = a tela de envio e o editor de modelos da loja não mudam (eles leem `PRESETS_VOLUME`/`PRESETS`). Sem fonte nova = sem mudança no backend (`schemas/modelo_etiqueta.py`) |
| D5 | **Folha usada pela metade:** o campo "Começar na posição" alimenta o `pular` do motor (só em folha) | Já é do motor (`paginacao.ts`) |
| D6 | **Calibração:** a do terminal, pela tela que o motor já tem ("Impressora de etiquetas", com "Imprimir teste"). A marcenaria não guarda ajuste próprio | Calibração é da máquina, não do móvel; uma só para produto, envio e móvel |
| D7 | **Térmica:** quando o terminal tem impressora de etiquetas configurada para impressão direta, o motor imprime nativo (ZPL/TSPL/PPLA); senão, pelo driver. A marcenaria não escreve ESC/POS | Já é do motor (`useImpressaoEtiquetas`, `nativo/`) |
| D8 | **Onde:** botão **"Etiquetas"** no topo da aba Produção (abre o modal com os móveis prontos marcados e os demais desmarcados) e **"Imprimir etiquetas"** no menu de cada cartão de móvel. Quando um móvel fica pronto (a última etapa concluída), um aviso discreto oferece "Imprimir as etiquetas de {móvel}?" | A etiqueta vai na embalagem, a última etapa |
| D9 | Móvel terceirizado também pode ter etiqueta | A central entrega sem a identificação da marcenaria |
| D10 | **Nenhum preço** na etiqueta | P4 |
| D11 | O modelo escolhido fica lembrado no computador (como o motor faz com o modelo de envio), com `try/catch`; sem armazenamento, volta ao A4 em 4 | O computador da fábrica sempre usa o mesmo (P3) |
| D12 | Permissão: a da OS (`servico`), a mesma da aba Produção. A linha "Etiquetas" dos cargos (do motor) **não** é exigida | Quem embala é a fábrica, que trabalha na OS |

---

## 5. Dados

```ts
/** Valores de UMA etiqueta = um volume de um móvel (D1). Nada de preço (D10). */
export function valoresDoVolumeDoMovel(
  movel: MovelProducao,              // da 12A: nome, ambiente, medidas
  volume: number,                    // 1, 2, 3...
  totalVolumes: number,              // "de 5"
  comum: { os: string; projeto: string; enderecoObra: string; cliente: string; empresa: string },
): ValoresEtiqueta {
  return {
    'os.numero': comum.os,                                            // "OS-2026-000512"
    'projeto.codigo': comum.projeto,                                  // "PRJ-000031"
    'projeto.endereco_obra': comum.enderecoObra,
    'cliente.nome': comum.cliente,
    'movel.nome': movel.nome,
    'movel.ambiente': movel.ambiente,
    'movel.medidas': formatarMedidasProposta(                         // "L 700 × A 2200 × P 600 mm" (07)
      movel.medidas.largura_mm, movel.medidas.altura_mm, movel.medidas.profundidade_mm),
    'volume.contador': `${volume}/${totalVolumes}`,                   // mesmo formato do envio
    'volume.rotulo': `VOLUME ${volume} DE ${totalVolumes}`,
    'empresa.nome': comum.empresa,
  };
}

/** Móveis escolhidos × volumes → etiquetas na ordem: ambiente, móvel, volume. */
export function montarEtiquetas(
  moveis: Array<{ movel: MovelProducao; volumes: number }>,
  comum: Parameters<typeof valoresDoVolumeDoMovel>[3],
): ValoresEtiqueta[] {
  return moveis.flatMap(({ movel, volumes }) =>
    Array.from({ length: volumes }, (_, i) => valoresDoVolumeDoMovel(movel, i + 1, volumes, comum)),
  );
}
```

Fontes: móveis, ambientes e medidas de `GET /os/{n}/producao` (12A); código do projeto, endereço da obra e cliente da **OS aberta no modal** (objeto `numero_serie` e `dados_adicionais.endereco_obra`; cliente); empresa de `useCompanyPrintInfo`.

Impressão (o mesmo caminho da tela de Produtos):

```ts
const { trabalho, imprimir } = useImpressaoEtiquetas();      // motor
const impressao = useImpressaoStore();                        // calibração do terminal (D6)

await imprimir({
  definicao: modeloEscolhido.value.definicao,                 // um dos PRESETS_MOVEL (D4)
  etiquetas: montarEtiquetas(selecionados.value, comum.value),
  pular: comecarNaPosicao.value - 1,                          // D5: só vale em folha
  deslocamentoX: impressao.config.etiqueta_deslocamento_x_mm,
  deslocamentoY: impressao.config.etiqueta_deslocamento_y_mm,
});
```

O modal monta `<EtiquetasImpressao v-if="trabalho" v-bind="trabalho" />`, como `EtiquetasTab.vue` faz.

## 6. Modal

```
Imprimir etiquetas — OS-2026-000512                                              [×]
Modelo   [Móvel — folha A4 em 4 ▾]

Móveis                                                              Volumes
 [x] Armário aéreo (Cozinha Gourmet) ............................... [ 3 ]
 [x] Guarda-roupa casal (Dormitório casal) ......................... [ 5 ]
 [ ] Ilha (Cozinha Gourmet) — em produção ........................... [ 1 ]

Começar na posição [ 1 ]   (só em folha)          8 etiquetas · 2 folhas   [Cancelar] [Imprimir]
```

- Contagem de etiquetas e de folhas em tempo real (`etiquetasPorPagina` do motor; conta simples de quantidade, não de dinheiro).
- Volumes de 1 a 50 por móvel.
- Título do documento durante a impressão: "Etiquetas OS-2026-000512" (nome sugerido do PDF, como na 07).

---

## 7. Prova de não regressão (⚠️ PR1)

1. `npm run test` (inclui os testes do motor: `motor`, `nativo`, `embalagem`, `render`, `envio`, `editor`) e `npx vue-tsc --noEmit`.
2. `npm run check:print-bw` com o layout novo.
3. Produtos › Etiquetas: mesmos modelos na lista de produto e de envio (snapshot das chaves de `PRESETS` e `PRESETS_VOLUME`); uma etiqueta de produto e uma de volume impressas iguais às de antes.
4. Vias de OS e venda (A4 e cupom) iguais depois de imprimir etiquetas.

## 8. Limitações conhecidas

- Só os modelos prontos (D4); a loja não edita o modelo do móvel nesta fase.
- O número de volumes não é guardado: reimprimir pede de novo (começa com a quantidade).
- Sem código de barras ou QR (nada lê esse código na fase 1).

---

## 9. Critérios de aceite

- [x] "Etiquetas" na aba Produção abre o modal com os móveis prontos marcados; o menu do móvel abre só com ele.
- [x] Volumes por móvel geram "VOLUME N DE T" certos, na ordem ambiente → móvel → volume.
- [x] A4 em 4 numa impressora comum; 100 × 150 e 100 × 50 na térmica (nativa quando configurada); "Começar na posição" pula as já usadas na folha.
- [x] A calibração do terminal vale para as etiquetas do móvel.
- [x] Etiquetas de produto e de envio iguais às de antes.
- [x] Oferta de etiquetas quando um móvel fica pronto.
- [x] Nenhum preço; preto e branco. Código comentado (PR6).

## 10. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `montarEtiquetas` com aéreo × 3 e guarda-roupa × 5 | 8 etiquetas; "VOLUME 1 DE 3"…"VOLUME 3 DE 3", "VOLUME 1 DE 5"…"VOLUME 5 DE 5" |
| 02 | `valoresDoVolumeDoMovel` | Nenhuma chave de preço; medidas no formato da proposta |
| 03 | `gerarMovel` em 105 × 148,5 e em 100 × 50 | Versão completa e versão compacta; todos os elementos dentro da página |
| 04 | `PRESETS` e `PRESETS_VOLUME` | Mesmas chaves de antes (snapshot) |
| 05 | `PRESETS_MOVEL` | 3 modelos, `fonte: 'volume'`, chaves `preset:movel-*` |
| 06 | Modal, folha A4 em 4, começar na 3, 8 etiquetas | `pular = 2`; 3 folhas no `paginar` |
| 07 | Modal, térmica configurada para impressão direta | `imprimir` vai pelo caminho nativo do motor |
| 08 | Concluir a última etapa de um móvel | Aviso "Imprimir as etiquetas de {móvel}?" |
| 09 | Móvel terceirizado | Pode ser marcado no modal |

### Roteiro manual (computador da fábrica)

1. Imprimir 8 etiquetas no A4 em 4; cortar e conferir.
2. Folha usada pela metade: começar na posição 3.
3. Térmica (se houver): calibrar em "Impressora de etiquetas" e imprimir 3 etiquetas 100 × 50.
4. Concluir a Embalagem de um móvel e aceitar a oferta.
5. Produtos › Etiquetas: uma etiqueta de produto e uma de envio, iguais às de antes.
