# Spec 10B — Separação de Material (Frontend)

| Campo        | Valor                                                                                  |
|--------------|----------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                        |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado (abas da OS)                     |
| Dependências | Specs 06B (busca de insumo), 08B (padrão de aba na OS, fábrica retirada do modal), 10A (API) |
| Bloqueia     | Spec 11B (o terceirizado aparece na mesma aba)                                         |
| Referência   | SPEC-00: E1b, E2, E2a, E3b, E4, E5a, P3, P4, T1, FB2 · PR1, PR3, PR6                   |

> **Revisão 1 (08/10/2026) — spec reescrita (SPEC-00 Revisão 15).** Com a 10A reescrita: (1) a aba trabalha sobre as **peças embutidas** da OS, e a coluna "Disponível" vira **"No estoque p/ esta OS"**, o número que o Compras calcula na fila das OS abertas; (2) a aba **"Lista de compras" em Produtos sai**: a lista entre OS é a tela **Necessidades** do Compras (E5a), e a aba Separação ganha **"Faltas desta OS"** (imprimir) e, com o módulo Compras, o atalho para as Necessidades; (3) o leitor aceita o código de barras de **embalagem** (bipar a caixa de 10 = 10 unidades), como a separação da fábrica fazia; (4) cada escrita manda a `quantidade_separada` que a tela tinha (10A D16). A tela de Produtos **não muda**.

---

## 1. Objetivo

1. **Aba "Separação"** na OS da marcenaria: a lista do que tirar do estoque, na ordem das prateleiras, com retirar, devolver, concluir e o **leitor de código de barras**.
2. **Faltas desta OS:** o que o estoque não cobre, para imprimir e levar ao telefone; com o módulo Compras, um atalho para as Necessidades.
3. **Disponível** na busca de insumo do orçamento: quanto há de verdade, descontado o que já está prometido.

A tela é usada no **computador fixo da fábrica** (P3): números grandes, poucos cliques, tudo pelo teclado quando houver leitor.

## 2. Escopo

**Dentro do escopo**
- `OSSeparacaoTab` e componentes.
- Faltas desta OS (painel e impressão A4).
- Coluna de disponível na busca de insumo (06B).

**Fora do escopo**
- Terceirizados (11B, mesma aba depois).
- Lista de compras entre OS, pedido de compra: **Compras** (Necessidades), como é (E5a).
- Tela de Produtos: não muda.

---

## 3. Arquivos afetados

```
frontend/src/modules/
├── order-service/ordens/components/form/OSFormTabsContent.vue   # ALTERAR ⚠️ — aba 'separacao'
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
    │       ├── SeparacaoResumo.vue                              # CRIAR — orçado × real
    │       ├── FaltasDaOS.vue                                   # CRIAR — painel das faltas
    │       └── FaltasPrint.vue                                  # CRIAR — A4 (Teleport, preto e branco)
    └── orcamentos/components/modais/InsumoBusca.vue             # ALTERAR — coluna "Disponível"
```

---

## 4. Decisões

### 4.1. Aba Separação

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Aba **"Separação"** no modal da OS, entre "Serviços e Peças" e "Orçamento", **só** com `temOrcamentoTecnico` e fora da criação (mesmo mecanismo da 08B D19). A query só roda com a aba aberta | T1; os outros segmentos não mudam e não chamam `/marcenaria/...` |
| D2 | Topo da aba: campo **"Ler código"** sempre focado ao abrir a aba, barra de progresso ("3 de 12 itens separados") e filtro "Mostrar só pendentes" (ligado por padrão) | Quem separa quer ver o que falta. Com leitor, o foco certo dispensa o mouse |
| D3 | Cada linha: **localização** em destaque à esquerda, nome, código, e três números grandes: **Sugerido**, **Retirado**, **No estoque p/ esta OS** (`no_estoque` do Compras, 10A D17); abaixo, em letra menor, os móveis que usam ("Balcão 2,2"). Botão principal **"Retirar"**; menu com **Devolver**, **Concluir**, **Não usado**, **Reabrir** | E3b. A localização primeiro porque a ordem da lista é a do depósito |
| D4 | Quantidades com a unidade do produto e as casas da unidade (`formatarQuantidade` de `shared/utils/quantidade.ts`): "3 un", "26,35 m" | Mesmo critério do resto do sistema |
| D5 | **Retirar** abre um modal pequeno com a quantidade **já preenchida** (a falta) e selecionada; Enter confirma. Se o estoque não cobre ("No estoque p/ esta OS" menor), aviso âmbar no modal: "Estoque insuficiente para esta OS: há 1 un. A retirada pode deixar o estoque negativo." e o botão vira "Retirar mesmo assim". Acima da falta, aviso "Acima do sugerido (3 un)" | E2a: não trava, mas avisa antes |
| D6 | **Concluir** (usou menos) pede confirmação mostrando o efeito: "A OS passa a consumir 2 un (o que foi retirado). A finalização não baixará mais nada deste produto." **Não usado** (nada retirado): "Este produto não será usado nesta OS." | 10A D10/D11: o usuário entende o que a ação faz no estoque |
| D7 | Linha concluída ou não usada: esmaecida, com ✓ "Retirado 2 un" ou "Não usado"; some com o filtro "só pendentes" | O progresso aparece sem poluir |
| D8 | Alertas da linha: `SEM_COBERTURA` (âmbar, "Falta no estoque"), `ESTOQUE_NEGATIVO` (vermelho, "Estoque negativo: conferir a contagem"), `ACIMA_DO_SUGERIDO` (cinza). Itens `sem_cadastro`: bloco cinza no fim, "Produto excluído do cadastro: não baixa estoque", sem botões | 10A D3, D7, D8 |
| D9 | **Nenhum preço** em lugar nenhum da aba, para ninguém | P4 |
| D10 | OS finalizada ou cancelada: aba somente leitura, com a frase "A OS está {status}: a separação não pode mais ser alterada." | 10A D14 |
| D11 | **Orçado × real** (`SeparacaoResumo`), recolhido por padrão no fim da aba: por produto, planejado, retirado e a diferença ("+12%"). Visível para todos (é quantidade, não preço) | E3: é o número que diz se a perda configurada está certa |
| D12 | Toda escrita manda `separada_esperada_milesimos` (o retirado que a tela mostrava). Conflito (`409 REVISAO_DESATUALIZADA`): toast "Outra pessoa alterou este item. A lista foi atualizada." e recarrega; a retirada **não** é refeita sozinha | 10A D16 |
| D13 | A aba recarrega a cada `REFETCH_REALTIME` enquanto aberta e sem modal aberto | Duas pessoas separando a mesma OS veem o progresso uma da outra |

### 4.2. Leitor de código (E4)

| # | Decisão | Motivo |
|---|---------|--------|
| D14 | O leitor é um teclado: o campo "Ler código" recebe os caracteres e o **Enter**. Ao ler, a tela chama `/separacao/ler`, **rola até a linha**, a destaca por 2 s e **abre o "Retirar"** com a quantidade preenchida (a falta) | E4. Um bipe, um Enter, e a retirada está feita |
| D15 | Produto que não é da OS: som curto de erro e a mensagem "Este produto não faz parte desta OS." no próprio campo, que é limpo e continua focado. Linha já concluída: "Este item já foi separado." | O marceneiro está olhando para a chapa, não para a tela |
| D16 | Modo **"Cada leitura retira"** (alternável, desligado por padrão): cada bipe retira, sem abrir o modal, **o fator do código lido** (1 para o produto; 10 para a embalagem de 10), com o contador "MDF Branco TX 18mm: 3 de 4". Produto de unidade fracionada (metro, quilo) sempre abre o modal | Ferragem embalada: 40 bipes é mais rápido que digitar 40; a caixa conta as unidades dela. "1 metro por bipe" não corresponde a nada real |
| D17 | Se o foco sair do campo, qualquer leitura completa (caracteres rápidos terminados em Enter) **com o modal fechado** volta para o campo | Leitor que "digita" num lugar errado é o erro mais comum de balcão |

### 4.3. Faltas e Compras (E5a)

| # | Decisão | Motivo |
|---|---------|--------|
| D18 | Botão **"Faltas desta OS"** no topo da aba (com a contagem, "3 faltas"; desabilitado sem faltas): abre o painel com produto, quanto falta, localização e o fornecedor principal (nome e telefone, para ligar), e **"Imprimir"** (A4, preto e branco, pelo caminho das outras vias) | E5a. O pedido ainda é feito por telefone ou WhatsApp quando a loja não tem o Compras |
| D19 | Com o módulo COMPRAS e acesso a ele (`useAcessoCompras().podeVer`): no painel, o botão **"Ver nas Necessidades"**, que leva à rota `purchases-needs` do Compras. Sem o módulo, o botão não aparece | FB2: a lista entre OS e o pedido são do Compras. O painel "Compras desta OS" do Compras já aparece na aba Serviços e Peças da OS para quem tem o módulo |
| D20 | Painel vazio: "Nada a comprar: o estoque cobre esta OS." | Uma lista vazia é uma boa notícia |

### 4.4. Disponível no orçamento

| # | Decisão | Motivo |
|---|---------|--------|
| D21 | Na busca de insumo do orçamento (06B D26), cada resultado mostra "Estoque 6 · disponível 2" (uma chamada a `/estoque/disponivel` com os ids da página de resultados, depois que a busca responde). Disponível negativo em vermelho: "faltam 3" | E1b: a conta é a reserva do Compras. O vendedor sabe na hora se vai precisar comprar |

---

## 5. Contratos consumidos

Spec 10A §6 (separação, leitor, faltas, disponível). Do sistema: `formatarQuantidade`/`siglaUnidade` (`shared/utils/quantidade.ts`), `useCapacidades`, `useAcessoCompras` (`modules/compras/shared/composables`), `imprimirComPagina`, `useCompanyPrintInfo`, a rota `purchases-needs`.

---

## 6. Telas

### 6.1. Aba Separação

```
Separação de material             [Faltas desta OS (1)]   [▒▒▒▒▒░░░░░░░] 1 de 2 separados
Ler código: [_______________]   [ ] Cada leitura retira     [x] Mostrar só pendentes

CORREDOR A · PRAT. 2   MDF Branco TX 18mm  MDF-BR-18
                       Sugerido 3 un   Retirado 0 un   No estoque p/ esta OS 3 un   [Retirar] [⋯]
                       Balcão 2,2

SEM LOCALIZAÇÃO        Corrediça Tandem (par)
                       Sugerido 6 par  Retirado 6 par  ✓                                     [⋯]

▸ Orçado × real (1 produto acima do orçado)
```

### 6.2. Faltas desta OS

```
Faltas da OS-2026-000512 · Studio Arquitetura            [Ver nas Necessidades] [Imprimir]
  MDF Branco TX 18mm     faltam 2 un   Corredor A   Madeireira Central · (85) 3333-0000
```

---

## 7. Especificação técnica

### 7.1. Aba — `OSFormTabsContent.vue` ⚠️

Mesmo padrão da 08B §7.1: `'separacao'` em `TabType`, empurrada antes de `'orcamento'` quando `temOrcamentoTecnico && !isCreateMode`, renderizada **fora** do `<fieldset>` travável (a aba tem as próprias regras de edição, D10).

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
- `ativo` = aba aberta **e** nenhum modal da separação aberto (D17).

### 7.3. Retirar pelo leitor

```ts
async function aoLer(codigo: string) {
  try {
    const { linha, fator } = await lerCodigo(numeroOs.value, codigo);   // GET /separacao/ler (10A D20)
    if (linha.concluida) return avisar('Este item já foi separado.');    // D15
    destacar(linha.item_id);                                            // rola e destaca 2 s
    if (cadaLeituraRetira.value && !ehFracionada(linha.unidade)) {      // D16
      await retirar(linha.item_id, fator * 1000, linha.separada_milesimos);   // o fator da embalagem, em milésimos
    } else {
      abrirRetirar(linha);                                              // D14: modal com a falta
    }
  } catch (erro) {
    if (status(erro) === 404) avisarComSom('Este produto não faz parte desta OS.');   // D15
    else throw erro;
  }
}
```

`ehFracionada` usa a mesma lista de `shared/utils/quantidade.ts` (`UNIDADES_FRACIONADAS`).

---

## 8. Prova de não regressão (⚠️ PR1)

1. `npm run test`, `npx vue-tsc --noEmit`, `npm run check:print-bw`.
2. Informática, oficina, serigrafia: abas do modal de OS iguais (snapshot). A tela de Produtos não foi tocada.
3. Nenhuma chamada a `/marcenaria/...` nesses segmentos.
4. O leitor do PDV continua funcionando na venda (o `useLeitorCodigo` só escuta com a aba Separação aberta).

## 9. Limitações conhecidas

- O som de erro depende do navegador do app permitir áudio sem interação prévia; sem som, fica a mensagem.
- Leitor que **não** manda Enter no fim precisa ser configurado para mandar (é o padrão de fábrica da maioria).
- Sem o módulo Compras, cada OS imprime as próprias faltas; não há lista consolidada (E5a).

---

## 10. Critérios de aceite

- [ ] Aba Separação só na marcenaria, com as linhas na ordem da localização, só pendentes por padrão, sem preço.
- [ ] Retirar com Enter, com os avisos de estoque insuficiente e de acima do sugerido; devolver, concluir, não usado e reabrir com o efeito explicado; o progresso e a cobertura atualizam.
- [ ] Leitor: bipe abre o "Retirar" da linha certa; embalagem retira o fator no modo "cada leitura retira"; produto de fora avisa com som.
- [ ] Orçado × real por produto.
- [ ] Faltas desta OS com fornecedor e impressão; "Ver nas Necessidades" só com o módulo Compras.
- [ ] Busca de insumo do orçamento mostra estoque e disponível.
- [ ] Prova de não regressão (§8); código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `OSFormTabsContent`, informática | Abas iguais (snapshot) |
| 02 | `OSFormTabsContent`, marcenaria | "Separação" antes de "Orçamento" |
| 03 | `useLeitorCodigo`: "7891234" em 70 ms + Enter | `aoLer('7891234')` uma vez |
| 04 | Mesmo, digitado com 200 ms entre teclas | Não chama `aoLer` pelo ouvinte global |
| 05 | `useLeitorCodigo` com `ativo = false` | Não chama |
| 06 | Leitura de produto de fora | Mensagem do D15; campo limpo e focado |
| 07 | "Cada leitura retira" com produto `UN` / embalagem de 10 / produto `M` | Retira 1000 / 10000 milésimos / abre o modal |
| 08 | `RetirarModal` com cobertura menor que a quantidade | Aviso âmbar e "Retirar mesmo assim" |
| 09 | `409 REVISAO_DESATUALIZADA` ao retirar | Toast do D12; recarrega; nenhuma nova tentativa |
| 10 | OS finalizada | Sem botões; frase do D10 |
| 11 | Linha `sem_cadastro` | Bloco cinza; sem botões |
| 12 | `FaltasDaOS` sem faltas | Texto do D20 |
| 13 | `FaltasDaOS` sem o módulo Compras / com | Sem / com "Ver nas Necessidades" |
| 14 | `FaltasPrint` | Só cores neutras; nenhum preço |
| 15 | `InsumoBusca` com disponível −3 | "faltam 3" em vermelho |
| 16 | Concluir com 2 de 3 retiradas | Confirmação com o efeito (D6); linha esmaecida "Retirado 2 un" |

### Roteiro manual (computador da fábrica, com leitor USB)

1. OS aprovada com o cenário B: abrir a aba, conferir a ordem por localização.
2. Bipar o MDF: o "Retirar" abre com 3; Enter. Bipar a caixa da corrediça com "cada leitura retira".
3. Bipar um produto que não está na OS.
4. Devolver 1 chapa; concluir com menos; marcar um produto como não usado; ver o orçado × real.
5. Em outro computador, abrir a mesma aba e retirar; ver o progresso aparecer no primeiro.
6. Duas OS disputando a mesma chapa: "Faltas desta OS" na mais nova; imprimir. Com o módulo Compras, "Ver nas Necessidades".
7. Informática: §8.
