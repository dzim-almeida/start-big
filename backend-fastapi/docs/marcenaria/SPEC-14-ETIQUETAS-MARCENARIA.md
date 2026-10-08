# Spec 14 — Etiquetas por Móvel (Frontend)

| Campo        | Valor                                                                              |
|--------------|------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                    |
| Camada       | Frontend (Vue 3 + TypeScript)                                                      |
| Dependências | Specs 12B (aba Produção), 13A (código do projeto e endereço da obra)               |
| Bloqueia     | —                                                                                  |
| Referência   | SPEC-00: I7, P3, P4 · PR1, PR3, PR6                                                |

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
- Modal "Imprimir etiquetas" na aba Produção (todos os móveis, selecionados ou um só).
- Três formatos: folha A4 comum (4 por folha, para cortar), folha adesiva A4 de 10 etiquetas, e impressora térmica (uma etiqueta por corte).
- Ajuste fino da posição para folhas adesivas, guardado por computador.

**Fora do escopo**
- Impressora de etiquetas dedicada (Zebra, Argox: linguagens ZPL/EPL).
- Etiqueta por **peça** (I7: só com importação 3D, fase 2).
- Código de barras ou QR para conferência na entrega (fase 2: hoje nada lê esse código).

---

## 3. Arquivos afetados

```
frontend/src/modules/marcenaria/etiquetas/
├── types/etiqueta.types.ts                 # CRIAR — DadosEtiqueta, FormatoEtiqueta
├── utils/montarEtiquetas.ts                # CRIAR — móveis × volumes → lista de etiquetas
├── utils/etiquetaEscPos.ts                 # CRIAR — etiqueta para a térmica (EscPosBuilder)
├── constants/formatos.ts                   # CRIAR — medidas de cada formato
├── composables/useImprimirEtiquetas.ts     # CRIAR
└── components/
    ├── ImprimirEtiquetasModal.vue          # CRIAR
    └── EtiquetasPrint.vue                  # CRIAR — folhas A4 (Teleport, preto e branco)
frontend/src/modules/marcenaria/producao/components/
├── OSProducaoTab.vue                       # ALTERAR — botão "Etiquetas"
└── MovelProducaoCard.vue                   # ALTERAR — "Imprimir etiquetas" no menu
```

Nenhum arquivo compartilhado muda: a térmica usa `useImpressao().imprimirCupom` e o `EscPosBuilder` como são.

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | **Uma etiqueta por volume.** No modal, cada móvel tem o campo **"Volumes"**, que começa com a **quantidade** do móvel (3 aéreos = 3 volumes) e pode ser mudado (um guarda-roupa sai em 5 caixas). As etiquetas são numeradas por móvel: "Volume 2 de 5" | I7 fala em "volumes embalados". O número de caixas só se sabe na embalagem |
| D2 | Conteúdo, nesta ordem de destaque: **PRJ-000031 · OS-2026-000512** (maior); **móvel** (negrito); ambiente; medidas "L 700 × A 2200 × P 600 mm"; **Volume 2 de 5**; cliente; endereço da obra (cortado em 2 linhas); nome da empresa (pequeno, no rodapé) | O código e a OS identificam no depósito; móvel e ambiente orientam a montagem; o endereço orienta o motorista |
| D3 | **Formatos:** (a) **A4 comum, 4 por folha** (105 × 148 mm, cortar com tesoura e colar com fita) — o padrão, funciona em qualquer impressora; (b) **Folha adesiva A4, 10 por folha** (101,6 × 50,8 mm, o tamanho mais comum de folha adesiva A4 com 10 etiquetas); (c) **Térmica** (largura da bobina configurada, uma etiqueta por corte) — só quando a impressora térmica está configurada | Quem ainda não comprou etiqueta adesiva imprime no papel comum no primeiro dia. ⚠️ As medidas de (b) devem ser conferidas com a folha que a fábrica comprar antes do piloto |
| D4 | **Começar na posição** (só no formato adesivo): "Começar na etiqueta nº [1..10]", para aproveitar a folha já usada pela metade | Folha adesiva é cara; ninguém joga fora 6 etiquetas boas |
| D5 | **Ajuste fino** (formato adesivo): deslocamento horizontal e vertical em milímetros (−10 a +10), guardado **no navegador deste computador** (com `try/catch`; sem armazenamento, volta a 0). Botão "Imprimir página de teste" com as bordas das etiquetas desenhadas | Cada impressora puxa o papel com uma pequena diferença; é configuração da máquina, não do orçamento (a mesma lógica da bobina, que é por máquina) |
| D6 | O formato escolhido também fica guardado no computador (padrão: A4 comum) | O computador da fábrica sempre usa a mesma coisa (P3) |
| D7 | Térmica: texto em ESC/POS pelo `EscPosBuilder` (o caminho das vias de cupom), com o código e o móvel em fonte dupla, uma etiqueta por corte. Sem impressora térmica configurada, a opção não aparece | Reaproveita a impressão direta que a loja já usa |
| D8 | **Onde:** botão **"Etiquetas"** no topo da aba Produção (abre o modal com todos os móveis prontos marcados, e os demais desmarcados) e **"Imprimir etiquetas"** no menu de cada cartão de móvel. Quando um móvel fica pronto (a última etapa concluída), um aviso discreto oferece "Imprimir as etiquetas de {móvel}?" | A etiqueta vai na embalagem, que é a última etapa; a oferta aparece na hora em que ela é útil, sem abrir modal sozinha |
| D9 | Móvel terceirizado também pode ter etiqueta (a central entrega sem a identificação da marcenaria) | O montador precisa identificar todas as caixas da obra |
| D10 | **Nenhum preço** na etiqueta | P4 |
| D11 | Preto e branco, fonte sem serifa grande, sem logo na etiqueta adesiva (a logo colorida em impressora a jato gasta tinta e não ajuda a identificar a caixa); a logo aparece só no formato A4 comum | `check:print-bw`; legibilidade no depósito |

---

## 5. Dados

```ts
/** Uma etiqueta = um volume de um móvel (D1). Nada de preço (D10). */
export interface DadosEtiqueta {
  codigoProjeto: string;      // "PRJ-000031" (objeto da OS)
  numeroOs: string;           // "OS-2026-000512"
  movel: string;              // "Guarda-roupa casal"
  ambiente: string;           // "Dormitório casal"
  medidas: string;            // "L 2400 × A 2600 × P 600 mm" (formatarMedidasProposta, 07)
  volume: number;             // 2
  totalVolumes: number;       // 5
  cliente: string;
  enderecoObra: string;
  empresa: string;            // nome fantasia
}
```

Fontes: móveis, ambientes e medidas de `GET /os/{n}/producao` (12A); código do projeto, endereço da obra e cliente da **OS aberta no modal** (objeto `numero_serie` e `dados_adicionais.endereco_obra`; cliente); empresa de `useCompanyPrintInfo`.

```ts
/** Móveis escolhidos × volumes → etiquetas na ordem: ambiente, móvel, volume. */
export function montarEtiquetas(
  moveis: Array<{ movel: MovelProducao; volumes: number }>,
  comum: Omit<DadosEtiqueta, 'movel' | 'ambiente' | 'medidas' | 'volume' | 'totalVolumes'>,
): DadosEtiqueta[] {
  return moveis.flatMap(({ movel, volumes }) =>
    Array.from({ length: volumes }, (_, i) => ({
      ...comum,
      movel: movel.nome,
      ambiente: movel.ambiente,
      medidas: formatarMedidasProposta(movel.medidas.largura_mm, movel.medidas.altura_mm, movel.medidas.profundidade_mm),
      volume: i + 1,                 // 1, 2, 3...
      totalVolumes: volumes,         // "de 5"
    })),
  );
}
```

## 6. Formatos — `constants/formatos.ts`

```ts
/** Medidas em milímetros. A folha é sempre A4 (210 × 297). */
export const FORMATOS = {
  A4_4: { nome: 'A4 comum — 4 por folha (cortar)', colunas: 2, linhas: 2,
          largura: 105, altura: 148.5, margemTopo: 0, margemEsquerda: 0, espacoH: 0, espacoV: 0 },
  A4_10: { nome: 'Folha adesiva A4 — 10 por folha (101,6 × 50,8 mm)', colunas: 2, linhas: 5,
           largura: 101.6, altura: 50.8, margemTopo: 21.5, margemEsquerda: 2.15, espacoH: 2.5, espacoV: 0 },  // (297 − 5×50,8)/2 e (210 − 2×101,6 − 2,5)/2
  TERMICA: { nome: 'Impressora térmica (uma por corte)' },
} as const;
```

O CSS da folha usa essas medidas em `mm` com `position: absolute` por etiqueta, mais o deslocamento do D5. ⚠️ As margens de `A4_10` são as da folha mais comum desse tamanho e precisam ser conferidas com a folha comprada (a página de teste do D5 serve para isso).

## 7. Modal

```
Imprimir etiquetas — OS-2026-000512                                              [×]
Formato  (•) A4 comum — 4 por folha   ( ) Folha adesiva — 10 por folha   ( ) Térmica

Móveis                                                              Volumes
 [x] Armário aéreo (Cozinha Gourmet) ............................... [ 3 ]
 [x] Guarda-roupa casal (Dormitório casal) ......................... [ 5 ]
 [ ] Ilha (Cozinha Gourmet) — em produção ........................... [ 1 ]

Começar na etiqueta nº [ 1 ]   Ajuste: horizontal [ 0 ] mm  vertical [ 0 ] mm   (só adesiva)
[Página de teste]                                   8 etiquetas · 1 folha   [Cancelar] [Imprimir]
```

- Contagem de etiquetas e de folhas em tempo real (conta simples de quantidade, não de dinheiro).
- Volumes de 1 a 50 por móvel.
- Imprimir: A4 pelo `imprimirComPagina('A4')` com o título "Etiquetas OS-2026-000512" (nome do PDF, como na 07); térmica pelo `imprimirCupom` com os bytes de todas as etiquetas.

---

## 8. Prova de não regressão (PR1)

1. `npm run check:print-bw` com o template novo.
2. Vias de OS e venda (A4 e cupom) iguais depois de imprimir etiquetas.
3. Nenhum arquivo compartilhado alterado.

## 9. Limitações conhecidas

- Sem impressora de etiquetas dedicada (ZPL/EPL).
- O número de volumes não é guardado: reimprimir pede de novo (começa com a quantidade).
- Sem código de barras ou QR (nada lê esse código na fase 1).

---

## 10. Critérios de aceite

- [ ] "Etiquetas" na aba Produção abre o modal com os móveis prontos marcados; o menu do móvel abre só com ele.
- [ ] Volumes por móvel geram "Volume N de T" certos, na ordem ambiente → móvel → volume.
- [ ] A4 comum: 4 por folha, com logo; adesiva: 10 por folha, começando na posição escolhida e com o ajuste fino aplicado; página de teste com as bordas.
- [ ] Térmica: uma etiqueta por corte, só com impressora configurada.
- [ ] Formato e ajuste lembrados no computador.
- [ ] Oferta de etiquetas quando um móvel fica pronto.
- [ ] Nenhum preço; preto e branco. Código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `montarEtiquetas` com aéreo × 3 e guarda-roupa × 5 | 8 etiquetas; "1 de 3"…"3 de 3", "1 de 5"…"5 de 5" |
| 02 | Formato adesivo, começar na nº 7, 8 etiquetas | Folha 1 com as posições 7–10; folha 2 com 4 |
| 03 | Ajuste +2 mm horizontal | Todas as etiquetas deslocadas 2 mm |
| 04 | Navegador sem armazenamento | Ajuste 0 e formato A4 comum, sem erro |
| 05 | Sem impressora térmica | Opção "Térmica" ausente |
| 06 | `etiquetaEscPos` | Bytes com o código em fonte dupla e um corte por etiqueta |
| 07 | Concluir a última etapa de um móvel | Aviso "Imprimir as etiquetas de {móvel}?" |
| 08 | Móvel terceirizado | Pode ser marcado no modal |
| 09 | `EtiquetasPrint` | Sem "R$"; só cores neutras |

### Roteiro manual (computador da fábrica)

1. Imprimir 8 etiquetas em A4 comum; cortar e conferir.
2. Folha adesiva: página de teste; ajustar 1–2 mm; imprimir começando na nº 7.
3. Térmica (se houver): imprimir 3 etiquetas.
4. Concluir a Embalagem de um móvel e aceitar a oferta.
