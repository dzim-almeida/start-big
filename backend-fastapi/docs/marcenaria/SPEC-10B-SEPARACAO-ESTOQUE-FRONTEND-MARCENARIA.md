# Spec 10B — Separação de Material e Lista de Compras (Frontend)

| Campo        | Valor                                                                                  |
|--------------|----------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                        |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado (abas da OS, tela de Produtos)   |
| Dependências | Specs 06B (busca de insumo), 08B (padrão de aba na OS), 10A (API)                      |
| Bloqueia     | Spec 11B (o terceirizado aparece na mesma aba)                                         |
| Referência   | SPEC-00: E1, E2, E2a, E3, E3a, E4, E5, P3, P4, T1 · PR1, PR3, PR6                      |

---

## 1. Objetivo

1. **Aba "Separação"** na OS da marcenaria: a lista do que tirar do estoque, na ordem das prateleiras, com retirar, devolver e concluir, e com o **leitor de código de barras**.
2. **Lista de compras** em Produtos: o que falta para as OS abertas, por fornecedor, para imprimir e levar ao telefone.
3. **Disponível** na busca de insumo do orçamento: quanto há de verdade, descontado o que já está prometido.

A tela é usada no **computador fixo da fábrica** (P3): números grandes, poucos cliques, tudo pelo teclado quando houver leitor.

## 2. Escopo

**Dentro do escopo**
- `OSSeparacaoTab` e componentes.
- Aba "Lista de compras" em Produtos (capacidade `orcamento_tecnico`) e a impressão A4.
- Coluna de disponível na busca de insumo (06B).

**Fora do escopo**
- Terceirizados (11B, mesma aba depois).
- Pedido de compra (E5).

---

## 3. Arquivos afetados

```
frontend/src/modules/
├── order-service/ordens/components/form/OSFormTabsContent.vue   # ALTERAR ⚠️ — aba 'separacao'
├── products/
│   ├── shared/constants/tabs.constants.ts                       # ALTERAR ⚠️ — aba por capacidade
│   └── views/ProductsView.vue                                   # ALTERAR ⚠️ — conteúdo da aba nova
└── marcenaria/
    ├── separacao/
    │   ├── services/separacao.service.ts                        # CRIAR
    │   ├── schemas/separacao.schema.ts                          # CRIAR
    │   ├── composables/useSeparacao.ts                          # CRIAR — query + ações
    │   ├── composables/useLeitorCodigo.ts                       # CRIAR — leitura por teclado
    │   └── components/
    │       ├── OSSeparacaoTab.vue                               # CRIAR
    │       ├── SeparacaoLinha.vue                               # CRIAR
    │       ├── RetirarModal.vue · DevolverModal.vue             # CRIAR
    │       └── SeparacaoResumo.vue                              # CRIAR — orçado × real
    ├── compras/
    │   ├── services/listaCompras.service.ts                     # CRIAR
    │   ├── components/ListaComprasPanel.vue                     # CRIAR
    │   └── components/ListaComprasPrint.vue                     # CRIAR — A4 (Teleport, preto e branco)
    └── orcamentos/components/modais/InsumoBusca.vue             # ALTERAR — coluna "Disponível"
```

---

## 4. Decisões

### 4.1. Aba Separação

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Aba **"Separação"** no modal da OS, entre "Serviços e Peças" e "Orçamento", **só** com `temOrcamentoTecnico` e fora da criação (mesmo mecanismo da 08B D19). A query só roda com a aba aberta | T1; os outros segmentos não mudam e não chamam `/marcenaria/...` |
| D2 | Topo da aba: campo **"Ler código"** sempre focado ao abrir a aba, barra de progresso ("3 de 12 itens separados") e filtro "Mostrar só pendentes" (ligado por padrão) | Quem separa quer ver o que falta. Com leitor, o foco certo dispensa o mouse |
| D3 | Cada linha: **localização** em destaque à esquerda (é o que guia o caminho), nome, código, e três números grandes: **Sugerido**, **Retirado**, **Disponível**; abaixo, em letra menor, os móveis que usam ("Torre Quente 1,54 · Aéreo 1,98"). Botão principal **"Retirar"**; menu com **Devolver**, **Concluir**/**Reabrir** | E3a, D6/D7 da 10A. A localização primeiro porque a ordem da lista é a do depósito |
| D4 | Quantidades com a unidade do produto e as casas da unidade (`formatarQuantidade` de `quantidade.ts`): "4 un", "26,35 m" | Mesmo critério do resto do sistema; "1,4 un" de chapa nunca aparece porque o sugerido já é inteiro |
| D5 | **Retirar** abre um modal pequeno com a quantidade **já preenchida** (sugerido − retirado) e selecionada; Enter confirma. Se o disponível não cobre, aviso âmbar no modal: "Estoque insuficiente: há 1 un disponível. A retirada vai deixar o estoque negativo." e o botão vira "Retirar mesmo assim" | E2a: não trava, mas avisa antes. Enter confirma porque a mão está no leitor |
| D6 | Linha concluída: esmaecida, com ✓ e "Retirado 4 un"; some com o filtro "só pendentes" | O progresso aparece sem poluir |
| D7 | Alertas da linha: `SEM_SALDO` (âmbar, "Falta no estoque"), `ESTOQUE_NEGATIVO` (vermelho, "Estoque negativo: conferir a contagem"), `SEM_CADASTRO` (cinza, "Produto excluído do cadastro: não baixa estoque", sem botões) | 10A D5, D9 |
| D8 | **Nenhum preço** em lugar nenhum da aba, para ninguém | P4 |
| D9 | OS finalizada ou cancelada: aba somente leitura, com a frase "A OS está {status}: a separação não pode mais ser alterada." | 10A D13 |
| D10 | **Orçado × real** (`SeparacaoResumo`), recolhido por padrão no fim da aba: por produto, planejado, retirado e a diferença ("+12%"), com o total de produtos acima do orçado. Visível para todos (é quantidade, não preço) | E3: é o número que diz se a perda configurada está certa |
| D11 | Conflito (`409 REVISAO_DESATUALIZADA`): toast "Outra pessoa alterou este item. A lista foi atualizada." e recarrega; a retirada **não** é refeita sozinha | 10A D26. Refazer sozinho poderia retirar duas vezes |
| D12 | A aba recarrega a cada `REFETCH_REALTIME` enquanto aberta e sem modal aberto | Duas pessoas separando a mesma OS veem o progresso uma da outra |

### 4.2. Leitor de código (E4)

| # | Decisão | Motivo |
|---|---------|--------|
| D13 | O leitor é um teclado: o campo "Ler código" recebe os caracteres e o **Enter**. Ao ler, a tela chama `/separacao/ler`, **rola até a linha**, a destaca por 2 s e **abre o "Retirar"** com a quantidade preenchida | E4. Um bipe, um Enter, e a retirada está feita |
| D14 | Produto que não é da OS: som curto de erro (o `beep` do navegador, sem arquivo) e a mensagem "Este produto não faz parte desta OS." no próprio campo, que é limpo e continua focado. Linha já concluída: "Este item já foi separado." | O marceneiro está olhando para a chapa, não para a tela; o som avisa |
| D15 | Modo **"Cada leitura soma 1"** (alternável, desligado por padrão): cada bipe retira 1 unidade da linha, sem abrir o modal; um contador mostra "MDF Branco TX 18mm: 3 de 4" | Ferragem embalada uma a uma: 40 bipes é mais rápido que digitar 40 sem errar |
| D16 | Se o foco sair do campo (clique em outra coisa), qualquer leitura completa (caracteres rápidos terminados em Enter) **com o modal fechado** volta para o campo | Leitor que "digita" num lugar errado é o erro mais comum de balcão |

### 4.3. Lista de compras (E5)

| # | Decisão | Motivo |
|---|---------|--------|
| D17 | Aba **"Lista de compras"** em Produtos, depois de "Fornecedores", **só** com `temOrcamentoTecnico` e permissão de produtos | É tarefa de quem cuida do estoque; nos outros segmentos a tela de Produtos fica igual |
| D18 | Grupos por fornecedor (com telefone e e-mail do cadastro para ligar), cada item com comprar, estoque, reservado, as OS (links que abrem a OS) e a localização. Interruptor **"Incluir reposição do estoque mínimo"** | 10A D20, D21 |
| D19 | **Imprimir** (A4, preto e branco, pelo mesmo caminho das outras vias): um bloco por fornecedor, com caixas para marcar à caneta. Com `view_custos`, a coluna "Último preço" e o total estimado; sem, não aparecem | O pedido ainda é feito por telefone ou WhatsApp (E5) |
| D20 | Lista vazia: "Nada a comprar: o estoque cobre todas as OS abertas." | Uma lista vazia é uma boa notícia e precisa parecer uma |

### 4.4. Disponível no orçamento

| # | Decisão | Motivo |
|---|---------|--------|
| D21 | Na busca de insumo do orçamento (06B D26), cada resultado mostra "Estoque 6 · disponível 2" (uma chamada a `/estoque/disponivel` com os ids da página de resultados, depois que a busca responde). Disponível negativo em vermelho: "faltam 3" | E1a regra 3: este é um dos três lugares onde a reserva é calculada. O vendedor sabe na hora se vai precisar comprar |

---

## 5. Contratos consumidos

Spec 10A §6 (separação, leitor, lista de compras, disponível). Do sistema: `formatarQuantidade`/`siglaUnidade` (`shared/utils/quantidade.ts`), `useCapacidades`, `imprimirComPagina`, `useCompanyPrintInfo`, `getUniqueOS` + `openExistingOS`.

---

## 6. Telas

### 6.1. Aba Separação

```
Separação de material                          [▒▒▒▒▒░░░░░░░] 3 de 12 separados
Ler código: [_______________]   [ ] Cada leitura soma 1     [x] Mostrar só pendentes

CORREDOR A · PRAT. 2   MDF Branco TX 18mm  MDF-BR-18
                       Sugerido 4 un   Retirado 0 un   Disponível 5 un      [Retirar] [⋯]
                       Torre Quente 1,54 · Armário aéreo 1,98

CORREDOR A · PRAT. 3   Fita de borda branca 22 mm  FITA-22
   ⚠ Falta no estoque  Sugerido 26,35 m   Retirado 0 m   Disponível 10 m  [Retirar] [⋯]

SEM LOCALIZAÇÃO        Corrediça telescópica 450 mm
                       Sugerido 6 par  Retirado 6 par  ✓                          [⋯]

▸ Orçado × real (2 produtos acima do orçado)
```

### 6.2. Lista de compras

```
Lista de compras                       [ ] Incluir reposição do estoque mínimo   [Imprimir]

Madeireira Central · (85) 3333-0000 · vendas@madeireira.com
  [ ] MDF Branco TX 18mm     comprar 7 un   estoque 2 · reservado 9   OS-…512, OS-…515   Corredor A
  [ ] MDF Freijó 18mm        comprar 2 un   …
Sem fornecedor
  [ ] Puxador perfil 3 m     comprar 4 un   …
```

---

## 7. Especificação técnica

### 7.1. Aba — `OSFormTabsContent.vue` ⚠️

Mesmo padrão da 08B §7.1: `'separacao'` em `TabType`, empurrada antes de `'orcamento'` quando `temOrcamentoTecnico && !isCreateMode`, renderizada **fora** do `<fieldset>` travável (a aba tem as próprias regras de edição, D9).

### 7.2. Leitor — `useLeitorCodigo.ts`

```ts
/**
 * Reconhece uma leitura de código vinda de um leitor que "digita".
 * Leitor: caracteres chegam com menos de 30 ms entre si e terminam em Enter.
 * Pessoa digitando: mais devagar — o campo continua funcionando como campo comum.
 */
export function useLeitorCodigo(aoLer: (codigo: string) => void, ativo: Ref<boolean>) {
  let buffer = '';                                  // caracteres da leitura em curso
  let ultimo = 0;                                   // instante da última tecla (ms)

  useEventListener(document, 'keydown', (e: KeyboardEvent) => {
    if (!ativo.value) return;                       // aba fechada ou modal aberto: não captura
    const agora = performance.now();
    if (agora - ultimo > 30) buffer = '';           // pausa longa: começa outra leitura
    ultimo = agora;
    if (e.key === 'Enter' && buffer.length >= 4) {  // leitura completa (códigos curtos demais são digitação)
      aoLer(buffer);
      buffer = '';
      e.preventDefault();                           // o Enter do leitor não confirma outra coisa
    } else if (e.key.length === 1) {
      buffer += e.key;                              // só caracteres visíveis entram no código
    }
  });
}
```

- O campo "Ler código" também chama `aoLer` no Enter quando o usuário digita à mão (código de etiqueta rasgada).
- `ativo` = aba aberta **e** nenhum modal da separação aberto (D16).

### 7.3. Retirar pelo leitor

```ts
async function aoLer(codigo: string) {
  try {
    const linha = await lerCodigo(numeroOs.value, codigo);             // GET /separacao/ler
    if (linha.concluida) return avisar('Este item já foi separado.');  // D14
    destacar(linha.produto_id);                                        // rola e destaca 2 s
    if (somaUm.value) {                                                // D15: retira 1 direto
      await retirar(linha.produto_id, 1000, linha.revisao);            // 1 unidade = 1000 milésimos
    } else {
      abrirRetirar(linha);                                             // D13: modal com o padrão
    }
  } catch (erro) {
    if (status(erro) === 404) avisarComSom('Este produto não faz parte desta OS.');   // D14
    else throw erro;
  }
}
```

No modo "soma 1", produto de unidade fracionada (metro, quilo) **não** soma 1: abre o modal, porque "1 metro por bipe" não corresponde a nada real.

### 7.4. Aba em Produtos ⚠️

```ts
// tabs.constants.ts — a lista de hoje continua igual; a aba nova é acrescentada pela tela.
export const TAB_OPTIONS: TabOption[] = [ /* ...os de hoje... */ ];
export const TAB_LISTA_COMPRAS: TabOption = { id: 'compras', label: 'Lista de compras' };

// ProductsView.vue
const { temOrcamentoTecnico } = useCapacidades();
const abas = computed(() => (temOrcamentoTecnico.value ? [...TAB_OPTIONS, TAB_LISTA_COMPRAS] : TAB_OPTIONS));
```

Na aba `compras`, o botão do topo ("Adicionar Produto"/"Adicionar Fornecedor") dá lugar a "Imprimir", e o título/descrição do cabeçalho viram "Lista de compras" / "O que falta para atender as OS abertas".

---

## 8. Prova de não regressão (⚠️ PR1)

1. `npm run test`, `npx vue-tsc --noEmit`, `npm run check:print-bw`.
2. Informática, oficina, serigrafia: abas do modal de OS iguais (snapshot); tela de Produtos com as mesmas duas abas e os mesmos botões.
3. Nenhuma chamada a `/marcenaria/...` nesses segmentos.
4. O leitor do PDV continua funcionando na venda (o `useLeitorCodigo` só escuta com a aba Separação aberta).

## 9. Limitações conhecidas

- O som de erro depende do navegador do app permitir áudio sem interação prévia; sem som, fica a mensagem.
- Leitor que **não** manda Enter no fim precisa ser configurado para mandar (é o padrão de fábrica da maioria).

---

## 10. Critérios de aceite

- [ ] Aba Separação só na marcenaria, com as linhas na ordem da localização, só pendentes por padrão, sem preço.
- [ ] Retirar com Enter, com o aviso de estoque insuficiente; devolver e concluir funcionam; o progresso e o disponível atualizam.
- [ ] Leitor: bipe abre o "Retirar" da linha certa; produto de fora avisa com som; "soma 1" retira 1 a cada bipe nas unidades inteiras.
- [ ] Orçado × real mostra a diferença por produto.
- [ ] Lista de compras por fornecedor, com e sem reposição do mínimo, imprimível; preço só com custos.
- [ ] Busca de insumo do orçamento mostra estoque e disponível.
- [ ] Prova de não regressão (§8); código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `OSFormTabsContent`, informática | Abas iguais (snapshot) |
| 02 | `OSFormTabsContent`, marcenaria | "Separação" antes de "Orçamento" |
| 03 | `ProductsView`, informática | 2 abas (snapshot) |
| 04 | `ProductsView`, marcenaria | 3 abas |
| 05 | `useLeitorCodigo`: "7891234" em 70 ms + Enter | `aoLer('7891234')` uma vez |
| 06 | Mesmo, digitado com 200 ms entre teclas | Não chama `aoLer` pelo ouvinte global |
| 07 | `useLeitorCodigo` com `ativo = false` | Não chama |
| 08 | Leitura de produto de fora | Mensagem do D14; campo limpo e focado |
| 09 | "Soma 1" em produto `UN` / em produto `M` | Retira 1000 / abre o modal |
| 10 | `RetirarModal` com disponível menor que a quantidade | Aviso âmbar e "Retirar mesmo assim" |
| 11 | `409 REVISAO_DESATUALIZADA` ao retirar | Toast do D11; recarrega; nenhuma nova tentativa |
| 12 | OS finalizada | Sem botões; frase do D9 |
| 13 | `SeparacaoLinha` com `SEM_CADASTRO` | Sem botões; texto do D7 |
| 14 | `ListaComprasPanel` vazio | Texto do D20 |
| 15 | `ListaComprasPrint` sem `view_custos` | Sem coluna de preço nem total |
| 16 | `InsumoBusca` com disponível −3 | "faltam 3" em vermelho |

### Roteiro manual (computador da fábrica, com leitor USB)

1. OS aprovada com o cenário B: abrir a aba, conferir a ordem por localização.
2. Bipar o MDF: o "Retirar" abre com 4; Enter. Bipar uma ferragem com "soma 1" seis vezes.
3. Bipar um produto que não está na OS.
4. Devolver 1 chapa; concluir a fita com menos que o sugerido; ver o orçado × real.
5. Em outro computador, abrir a mesma aba e retirar; ver o progresso aparecer no primeiro.
6. Produtos › Lista de compras com duas OS disputando a mesma chapa; imprimir.
7. Informática: §8.
