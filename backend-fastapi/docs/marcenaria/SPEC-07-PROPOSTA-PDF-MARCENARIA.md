# Spec 07 — Proposta Comercial em PDF (Frontend)

| Campo        | Valor                                                                          |
|--------------|--------------------------------------------------------------------------------|
| Status       | Implementada em 09/10/2026                                                     |
| Camada       | Frontend (Vue 3 + TypeScript)                                                  |
| Dependências | Spec 06B (editor, `montarDadosProposta`), Spec 06A Revisão 2 (dados do cliente no detalhe, evento de envio) |
| Bloqueia     | Spec 08B (a proposta aprovada reaproveita o template)                          |
| Referência   | SPEC-00: T5, T3f, C6, C7, C9, C3, O3, O7, P4 · PR1, PR3, PR6                   |

> **Implementação (09/10/2026) — o que o código acrescenta ou decide além do texto.**
> (1) **`DadosProposta` nasceu completo na 06B** (o tipo da §6.1 já era usado pela visão do cliente); aqui entram o template, o fluxo e o nome do arquivo. A faixa "VERSÃO SUBSTITUÍDA pela v3" usa o número da versão mais nova, que o editor já busca para a faixa de status.
> (2) **"Tudo gravado" (D4)** é: salvamento automático sem campo pendente, fila vazia e sem conflito. A fila nunca rejeita (um erro não trava as próximas), por isso a conferência é pelo estado, não por exceção.
> (3) **Modal de envio:** "Enviar e gerar proposta" (principal) e "Só marcar como enviado" (secundário) ficam no rodapé, ao lado de "Cancelar"; a dica do D8 fica acima, com "Não mostrar de novo" (chave no navegador, com `try/catch`). O envio que falha (422) não imprime nada.
> (4) **Limpeza de segurança:** se o `afterprint` não vier, título e documento voltam ao normal em 2 minutos (o mesmo cuidado do pedido de compra).
> (5) **Cabeçalho repetido nas páginas seguintes (D13):** ficou de fora, como a §6.2 permite; as quebras (móvel inteiro, título com o primeiro móvel, fechamento junto) estão no CSS escopado em `.proposta`.

> **Revisão 1 (08/10/2026) — correção do exemplo.** O desenho da §6.2 tinha um ambiente "Dormitório casal" de R$ 1.425,00 que fazia a soma dos ambientes com a instalação (R$ 11.150,15) não bater com o subtotal (R$ 9.725,15), contrariando a D10. O desenho passa a ser o cenário B da Spec 05: Cozinha Gourmet (Torre Quente e 2 Balcões) + instalação.

---

## 1. Objetivo

Gerar a **proposta comercial** do orçamento: o documento que o cliente recebe, assina e guarda. Ela sai pelo mesmo caminho de impressão A4 que OS e vendas já usam, e o diálogo de impressão do Windows oferece **"Salvar como PDF"**, que é o arquivo enviado por WhatsApp ou e-mail.

A proposta mostra ambientes, móveis com descrição e medidas, **total por ambiente**, instalação, desconto, total, sinal, saldo, prazo de entrega, validade, observações e o espaço de aceite. **Nunca** mostra custo, margem, insumo, parâmetro ou preço por móvel (T5).

## 2. Escopo

**Dentro do escopo**
- Template A4 da proposta (`PropostaPrintTemplate.vue`).
- Botão **"Proposta"** no cabeçalho do editor, em qualquer status, com marca d'água conforme o status (D6).
- Botão **"Enviar e gerar proposta"** no modal de envio (o espaço que a 06B deixou, 06B §7.9).
- Nome do arquivo sugerido no "Salvar como PDF" (D5).
- Testes e roteiro manual.

**Fora do escopo**
- Gerar o arquivo PDF sem o diálogo de impressão, guardar o PDF no servidor ou mandar por e-mail/WhatsApp de dentro do sistema (§8).
- QR do PIX para o sinal (§8).
- Fotos, anexos e imagens 3D na proposta.
- Proposta da aprovação parcial (só os móveis aprovados): Spec 08B.

---

## 3. Arquivos afetados

```
frontend/src/modules/marcenaria/orcamentos/
├── components/print/
│   ├── PropostaPrintTemplate.vue        # CRIAR — o documento A4 (Teleport para o body)
│   └── __tests__/PropostaPrintTemplate.spec.ts
├── composables/useImprimirProposta.ts   # CRIAR — esvazia a fila, monta os dados, imprime
├── utils/dadosProposta.ts               # ALTERAR — tipo completo da proposta (criado na 06B)
├── utils/nomeArquivoProposta.ts         # CRIAR — título do documento → nome do PDF
├── components/editor/EditorCabecalho.vue # ALTERAR — botão "Proposta"
└── components/modais/EnviarModal.vue    # ALTERAR — "Enviar e gerar proposta"
```

Nenhum arquivo compartilhado muda. Reaproveitados sem alteração: `PrintCompanyHeader`, `PrintFooter`, `PrintSignatures`, `useCompanyPrintInfo`, `imprimirComPagina`, `aguardarImagensDaImpressao`, `print-a4.css`.

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `dadosProposta.ts` | Copiar do detalhe **só** o que o cliente pode ver, já formatado para leitura | Buscar dado; formatar HTML |
| `PropostaPrintTemplate.vue` | Desenhar o documento a partir de `DadosProposta` | Ler o detalhe do orçamento (recebe só `DadosProposta`) |
| `useImprimirProposta` | Esvaziar a fila de escrita, montar os dados, trocar o título, chamar a impressão, restaurar | Decidir o status do orçamento |

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | A proposta é um **template HTML A4** impresso com `window.print()`, como OS e vendas. O PDF sai pelo destino **"Salvar como PDF"** do diálogo de impressão do Windows | PR3: é o caminho que o sistema já tem, com cabeçalho da empresa, regra de preto e branco (`check:print-bw`) e quebras de página testadas. Um gerador de PDF próprio (no backend com `fpdf2`, ou no frontend com uma biblioteca nova) duplicaria o layout e o cabeçalho da empresa, e o arquivo cairia numa pasta escondida do app (`salvarArquivo` grava em `AppLocalData`), longe de onde o vendedor anexa no WhatsApp. Decidido: SPEC-00 T5a (Revisão 8) |
| D2 | **Sempre A4, folha inteira**, sem o modal de formato, sem cupom e sem meia folha. Não usa o perfil de comprovante (`usePerfilComprovante`) | A proposta tem várias páginas e é documento de venda, não comprovante de balcão. O perfil foi feito para OS e venda |
| D3 | O template recebe **só** `DadosProposta` (06B §7.13), nunca o detalhe. O tipo `DadosProposta` não tem campo de custo, margem, insumo, parâmetro nem preço por móvel; um teste compara as chaves (caso 01) | P4 e T5 por construção: mesmo quem vê os custos não consegue imprimi-los por engano. É a mesma fonte da visão do cliente (T3f) |
| D4 | Antes de imprimir, a **fila de escrita é esvaziada** (06B D7). Se houver conflito ou erro de gravação, a impressão não acontece e a mensagem diz por quê | O PDF tem que mostrar o que está gravado. Uma proposta com um desconto que não foi salvo seria um documento falso |
| D5 | Durante a impressão, `document.title` vira **"Proposta ORC-2026-000084 v2 - Studio Arquitetura"** e volta ao normal no `afterprint`. O diálogo usa o título como nome sugerido do arquivo | Sem isso, o PDF se chama "StartBig.pdf" e o vendedor renomeia um por um. Caracteres inválidos em nome de arquivo (`\ / : * ? " < > \|`) viram espaço; o nome do cliente é cortado em 40 caracteres |
| D6 | Botão **"Proposta"** em qualquer status. Conforme o status, uma faixa no topo do documento (texto, sem cor): `RASCUNHO` → **"PRÉVIA — proposta ainda não enviada"** e validade "15 dias a partir do envio"; `VENCIDO` → **"PROPOSTA VENCIDA em 21/10/2026"**; `RECUSADO` → **"PROPOSTA RECUSADA"**; `SUBSTITUIDO` → **"VERSÃO SUBSTITUÍDA pela v3"**. `ENVIADO` e `APROVADO` saem sem faixa | Reimprimir é comum (cliente perdeu, pediu de novo). A faixa impede que uma versão velha ou uma prévia circule como se valesse |
| D7 | **Enviar e gerar proposta** (botão principal do modal de envio): primeiro o `POST /enviar`, depois a impressão com os dados **já enviados** (validade gravada). Botão secundário **"Só marcar como enviado"** (quando a proposta foi gerada antes, ou entregue de outro jeito) | T5: o envio leva à proposta sem obrigar. Imprimir **depois** do envio garante que a data de validade no papel é a gravada. Cancelar o diálogo de impressão não desfaz o envio; o botão "Proposta" reimprime |
| D8 | O modal de envio mostra, uma vez por computador, a dica: "Na janela de impressão, escolha **Salvar como PDF** em Destino para gerar o arquivo e enviar por WhatsApp ou e-mail." com "Não mostrar de novo" (preferência no navegador, com `try/catch`) | O caminho do PDF pelo diálogo não é óbvio para quem nunca usou; depois da primeira vez, a dica vira ruído |
| D9 | **Ambiente sem móveis não aparece** na proposta. Orçamento sem nenhum móvel imprime só cabeçalho, cliente e "Nenhum móvel incluído" (só acontece na prévia; o envio exige móvel, 06A D13) | Ambiente vazio no documento do cliente parece erro |
| D10 | **Valores:** o total de cada ambiente é o **subtotal bruto** do ambiente (06A §6.2). A instalação, quando houver, é uma linha própria com preço (C3). Depois vêm Subtotal, Desconto (com o % quando o modo for percentual: "Desconto (5%)"), **Total**. Todos os números vêm da API (C8); a soma dos ambientes e da instalação bate com o subtotal porque o motor arredonda só no preço de cada móvel (C6) | O cliente confere a soma na calculadora; ela tem que fechar |
| D11 | **Condições:** "Sinal na aprovação: R$ 3.695,56 (40%)" e "Saldo: R$ 5.543,33" (quando o sinal for zero, só "Total a pagar"). "Prazo de entrega: 30 dias corridos após a aprovação" (O7). "Validade: até 21/10/2026". A forma e o momento de pagar o saldo **não** são inventados: entram pelas **observações da proposta** | O sistema não sabe se o saldo é na entrega, em parcelas ou no cartão. Escrever uma regra que a loja não combinou criaria um compromisso por engano |
| D12 | **Aceite:** "Declaro estar de acordo com esta proposta e autorizo a execução." e duas assinaturas (`PrintSignatures`): **Cliente** (com o nome) e **{nome fantasia da empresa}** (com o nome do vendedor), mais "Data: ___/___/______" | O cliente que aceita no papel volta com a proposta assinada; o documento serve de pedido |
| D13 | **Quebra de página:** cada móvel não se divide entre páginas; o título do ambiente não fica sozinho no fim da página; o bloco de valores, condições e aceite fica junto. Na segunda página em diante, uma linha discreta no topo repete "Proposta ORC-2026-000084 v2 · Studio Arquitetura" | Um projeto de 3 ambientes passa de uma página. Sem estas regras, o total cai numa página e o aceite em outra |
| D14 | Medidas como "L 700 × A 2200 × P 600 mm"; quantidade "1 un." só quando for maior que 1 aparece em destaque ("3 un.") | O cliente lê largura, altura e profundidade sem legenda à parte |
| D15 | Observações da proposta preservam as **quebras de linha** digitadas (`white-space: pre-line`) | É onde a loja escreve a forma de pagamento e as condições em linhas separadas |

---

## 5. Contratos consumidos

Detalhe do orçamento (06A §6.2) com a **Revisão 2** da 06A, feita junto com esta spec:

| Mudança na 06A | Para quê |
|----------------|----------|
| `cliente` no detalhe passa a trazer `telefone` (celular, senão o fixo, como `getClientePhone`), `email` e `endereco` (uma linha, mesmo formato de `getClienteEndereco`) | O cabeçalho do cliente na proposta. Buscar o cliente à parte exigiria a permissão de clientes, que o vendedor pode não ter |
| `vendedor` no detalhe passa a trazer `telefone` (celular do funcionário, senão o fixo, se houver) | Contato do vendedor na proposta ("Seu consultor: Alan · (85) 9…") |
| Evento `ORCAMENTO_ENVIADO` grava em `dados` o **total, o sinal, a validade e o número de móveis** no momento do envio, e a frase "Enviado com total de R$ 9.238,89, válido até 21/10/2026." | Registro do que o cliente recebeu, mesmo depois de "voltar a editar" (§8) |

Os campos novos **não** são custo: saem também para quem não tem `view_custos`.

---

## 6. Especificação técnica

### 6.1. `DadosProposta` — `utils/dadosProposta.ts`

```ts
/** Tudo o que a proposta e a visão do cliente mostram. Nada de custo (D3). */
export interface DadosProposta {
  codigo: string;                       // "ORC-2026-000084"
  versao: number;                       // 2
  status: StatusOrcamento;              // decide a faixa (D6)
  emitidaEm: string;                    // data de hoje, "06/10/2026"
  validadeTexto: string;                // "até 21/10/2026" ou "15 dias a partir do envio"
  faixa: string | null;                 // "PRÉVIA — proposta ainda não enviada" ou null (D6)
  cliente: { nome: string; documento: string; telefone: string; email: string; endereco: string };
  projeto: { nome: string; enderecoObra: string };
  vendedor: { nome: string; telefone: string } | null;
  ambientes: Array<{
    nome: string;
    totalCentavos: number;              // subtotal bruto do ambiente (D10)
    moveis: Array<{ nome: string; descricao: string; medidas: string; quantidade: number }>;
  }>;
  instalacaoCentavos: number | null;    // preço da instalação (C3), ou null
  subtotalCentavos: number;             // bruto
  desconto: { centavos: number; percentualTexto: string | null } | null;  // null sem desconto
  totalCentavos: number;
  sinal: { centavos: number; percentualTexto: string | null } | null;     // null com sinal zero (D11)
  saldoCentavos: number;
  prazoEntregaDias: number;
  observacoes: string;                  // observações da proposta, com quebras de linha (D15)
}

/** Copia do detalhe só o que pode chegar ao cliente. Função pura (sem rede, sem store). */
export function montarDadosProposta(detalhe: OrcamentoDetalhe, hoje: Date): DadosProposta {
  return {
    codigo: detalhe.codigo,
    versao: detalhe.versao,
    status: detalhe.status,
    emitidaEm: formatarData(hoje),                                    // data local
    validadeTexto: detalhe.datas.validade
      ? `até ${formatarData(detalhe.datas.validade)}`                 // já enviado: data gravada
      : `${detalhe.parametros.validade_dias} dias a partir do envio`, // prévia: ainda não conta
    faixa: faixaDoStatus(detalhe),                                    // D6
    // ...cliente, projeto e vendedor copiados campo a campo (nunca com spread do detalhe)
    ambientes: detalhe.ambientes
      .filter((amb) => amb.moveis.length > 0)                         // D9: ambiente vazio não sai
      .map((amb) => ({
        nome: amb.nome,
        totalCentavos: amb.subtotal_centavos,                         // bruto, como a 06A devolve
        moveis: amb.moveis.map((m) => ({
          nome: m.nome,
          descricao: m.descricao ?? '',
          medidas: formatarMedidasProposta(m.largura_mm, m.altura_mm, m.profundidade_mm), // D14
          quantidade: m.quantidade,                                   // preço do móvel NÃO entra (T5)
        })),
      })),
    // ...valores a partir de detalhe.calculo (D10, D11)
  };
}
```

- **Nunca** usar `...detalhe` nem `...movel`: cada campo é copiado pelo nome. É isso que o caso 01 garante.
- `percentualTexto` só existe quando o modo é `PERCENTUAL` ("5%", "12,5%"); no modo `VALOR` o documento mostra só o R$.

### 6.2. Template — `PropostaPrintTemplate.vue`

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [logo] Marcenaria Exemplo · CNPJ · endereço · contato  PROPOSTA COMERCIAL │  PrintCompanyHeader
│                                              ORC-2026-000084 · versão 2 │  documentLabel/Number
│                                              Emitida em 06/10/2026      │  dateLabel/Value
│ [PRÉVIA — proposta ainda não enviada]                     (só se houver) │  D6
├──────────────────────────────────────────────────────────────────────────┤
│ CLIENTE  Studio Arquitetura & Interiores Ltda · CNPJ 00.360.305/0001-04  │
│          (85) 3333-4444 · contato@studio.com · Av. …, Fortaleza - CE     │
│ PROJETO  Residencial Alpha Ville - Apto 802 · Av. das Américas, 4200     │
│ CONSULTOR Alan Alves de Amorim · (85) 98888-7777                         │
├──────────────────────────────────────────────────────────────────────────┤
│ COZINHA GOURMET                                           R$ 8.300,15    │
│  Torre Quente c/ Nicho p/ Forno e Micro-ondas                            │
│    MDF Branco TX e Freijó, corrediças com amortecedor                    │
│    L 700 × A 2200 × P 600 mm                                             │
│  Balcão                                                          2 un.   │
│    …                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                   Instalação e montagem     R$ 1.425,00  │
│                                   Subtotal                  R$ 9.725,15  │
│                                   Desconto (5%)            − R$ 486,26   │
│                                   TOTAL                     R$ 9.238,89  │
│ CONDIÇÕES                                                                │
│  Sinal na aprovação: R$ 3.695,56 (40%) · Saldo: R$ 5.543,33              │
│  Prazo de entrega: 30 dias corridos após a aprovação                     │
│  Validade: até 21/10/2026                                                │
│ OBSERVAÇÕES                                                              │
│  Saldo em 3x no cartão. Projeto 3D aprovado em 01/10.                    │
│                                                                          │
│ Declaro estar de acordo com esta proposta e autorizo a execução.         │
│  ____________________________      ____________________________          │  PrintSignatures
│  Cliente: Studio Arquitetura…       Marcenaria Exemplo (Alan)             │
│  Data: ___/___/______                                                    │
│                                                         PrintFooter     │
└──────────────────────────────────────────────────────────────────────────┘
```

```vue
<script setup lang="ts">
// Documento do cliente: recebe só DadosProposta (D3), nunca o detalhe com custos.
const props = defineProps<{ dados: DadosProposta }>();
const { companyInfo } = useCompanyPrintInfo();               // logo, CNPJ e contato da empresa
</script>

<template>
  <!-- Teleport: o print-a4.css esconde tudo o que não for filho direto do body. -->
  <Teleport to="body">
    <div class="print-container proposta hidden print:block bg-white text-black font-sans">
      <PrintCompanyHeader
        :company="companyInfo"
        document-label="PROPOSTA COMERCIAL"
        :document-number="`${dados.codigo} · versão ${dados.versao}`"
        date-label="Emitida em"
        :date-value="dados.emitidaEm"
      />
      <!-- Faixa de status: texto e borda, sem cor (check:print-bw). -->
      <p v-if="dados.faixa" class="proposta-faixa">{{ dados.faixa }}</p>
      <!-- ...blocos da §6.2, na ordem do desenho... -->
    </div>
  </Teleport>
</template>

<style>
/* Quebras de página (D13). Global como o print-a4.css, mas restrito a .proposta. */
@media print {
  .proposta .movel { break-inside: avoid; }                  /* móvel nunca dividido */
  .proposta .ambiente-titulo { break-after: avoid; }         /* título não fica sozinho */
  .proposta .fechamento { break-inside: avoid; }             /* valores + condições + aceite juntos */
}
</style>
```

- Cores: só a escala neutra (o `check:print-bw` reprova qualquer outra).
- A linha repetida no topo das páginas seguintes (D13) usa `position: running()`/margem de página **se** o motor de impressão do WebView2 suportar; senão, fica de fora (não é critério de aceite). Conferir no app instalado.

### 6.3. Fluxo — `useImprimirProposta.ts`

```ts
export function useImprimirProposta(fila: FilaOrcamento, detalhe: Ref<OrcamentoDetalhe | undefined>) {
  const dadosParaImprimir = ref<DadosProposta | null>(null);   // o template só existe enquanto imprime
  const toast = useToast();

  async function imprimir() {
    try {
      await fila.esvaziar();                                    // D4: grava o que está pendente
    } catch {
      toast.error('A proposta não foi gerada', 'Há alterações que não foram salvas.');
      return;                                                    // nunca imprime o que não está gravado
    }
    dadosParaImprimir.value = montarDadosProposta(detalhe.value!, new Date());
    const tituloOriginal = document.title;
    document.title = nomeArquivoProposta(dadosParaImprimir.value); // D5: nome sugerido do PDF
    await nextTick();                                            // o template entra no DOM
    await aguardarImagensDaImpressao();                          // a logo da empresa precisa ter carregado
    const restaurar = () => {                                    // depois do diálogo, tudo volta
      document.title = tituloOriginal;
      dadosParaImprimir.value = null;
      window.removeEventListener('afterprint', restaurar);
    };
    window.addEventListener('afterprint', restaurar);
    imprimirComPagina('A4', { folha: 'A4' });                    // D2: sempre folha inteira
  }

  return { imprimir, dadosParaImprimir };
}
```

O editor monta `<PropostaPrintTemplate v-if="dadosParaImprimir" :dados="dadosParaImprimir" />`.

### 6.4. Nome do arquivo — `utils/nomeArquivoProposta.ts`

```ts
/** "Proposta ORC-2026-000084 v2 - Studio Arquitetura" (D5). */
export function nomeArquivoProposta(dados: DadosProposta): string {
  const cliente = dados.cliente.nome
    .replace(/[\\/:*?"<>|]/g, ' ')   // caracteres proibidos em nome de arquivo no Windows
    .replace(/\s+/g, ' ')            // espaços repetidos viram um só
    .trim()
    .slice(0, 40);                   // nome de empresa longo não estoura o caminho
  const base = `Proposta ${dados.codigo} v${dados.versao}`;
  return cliente ? `${base} - ${cliente}` : base;   // prévia sem cliente: só o código
}
```

### 6.5. Modal de envio (06B §7.9)

No `<slot name="proposta">` do `EnviarModal`:

- Dica do D8 (uma vez por computador).
- Botão principal **"Enviar e gerar proposta"**: `acoes.enviar()` pela fila → com o detalhe novo (status `ENVIADO`, validade gravada) → `imprimir()`.
- Botão secundário **"Só marcar como enviado"**: só o envio.
- Se o envio falhar (`422`, faltou algo), nada é impresso e o modal mostra a pendência (06B D36).

---

## 7. Prova de não regressão (PR1)

Nenhum arquivo compartilhado muda. Conferir só:
1. `npm run check:print-bw` passa com o template novo.
2. Imprimir uma OS e uma venda em A4 e em cupom depois de imprimir uma proposta: mesmas vias de antes (a proposta não deixa estilo nem título para trás).

## 8. Limitações conhecidas

- **PDF pelo diálogo** (D1): o arquivo nasce onde o usuário escolher no "Salvar como PDF"; o sistema não guarda uma cópia. O registro do que foi enviado fica no **evento de envio** (total, sinal, validade; 06A Revisão 2), não no PDF.
- **"Voltar a editar" muda o que a reimpressão mostra:** a proposta é sempre do estado atual. Para preservar a proposta antiga como documento, o caminho é **nova versão** (a anterior fica somente leitura e reimprime igual, com a faixa "VERSÃO SUBSTITUÍDA").
- **Sem envio direto** por e-mail ou WhatsApp, e **sem QR do PIX** para o sinal: o sinal pago antes de a OS existir não teria onde ser registrado (a OS nasce na aprovação, Spec 08). Candidatos para depois da Spec 08.
- **Cabeçalho repetido nas páginas seguintes** depende do motor de impressão (§6.2).

---

## 9. Decisão registrada (T5a, Revisão 8 da SPEC-00)

**D1 — PDF pelo diálogo de impressão ou gerado pelo sistema?**

| | Diálogo de impressão (proposta) | Gerado pelo sistema |
|---|---|---|
| Como o vendedor faz | "Enviar e gerar proposta" → diálogo → Destino "Salvar como PDF" → escolhe a pasta | "Enviar e gerar proposta" → o PDF abre no visualizador, salvo numa pasta do app |
| Layout | O mesmo motor e cabeçalho das vias de OS e venda | Layout novo em Python (`fpdf2`, já no `requirements.txt` e sem uso) ou biblioteca nova no frontend |
| Onde o arquivo fica | Onde o vendedor escolher (Downloads, Área de Trabalho) | Pasta interna do app; para anexar no WhatsApp, o vendedor precisa achá-la (ou a spec acrescenta um "Salvar como…") |
| Cópia guardada | Não (o evento guarda os valores) | Pode guardar a cópia exata do que foi enviado |
| Esforço | Uma tela e um template | Gerador, fontes, quebras de página, teste do PyArmor (PR7) |

Decidido em 06/10/2026 (T5a): **diálogo de impressão**. A cópia exata guardada é o único ganho real do outro caminho, e o evento de envio com os valores cobre a necessidade da fase 1.

---

## 10. Critérios de aceite

- [ ] Botão "Proposta" no editor em qualquer status; o diálogo de impressão abre com o nome sugerido "Proposta ORC-… v… - Cliente".
- [ ] A proposta mostra cliente (com telefone, e-mail e endereço), projeto, consultor, ambientes com móveis (descrição e medidas), total por ambiente, instalação, subtotal, desconto, total, sinal, saldo, prazo, validade, observações e aceite.
- [ ] Nenhum custo, margem, insumo, parâmetro ou preço por móvel, nem para o master.
- [ ] A soma dos ambientes com a instalação bate com o subtotal (cenário B da Spec 05).
- [ ] Faixas de prévia, vencida, recusada e substituída conforme o status; enviada e aprovada sem faixa.
- [ ] Alteração ainda não salva é gravada antes; com conflito, nada é impresso.
- [ ] "Enviar e gerar proposta" envia e imprime com a validade gravada; cancelar o diálogo não desfaz o envio.
- [ ] Projeto de 3 ambientes em 2 páginas sem móvel cortado e com o fechamento junto.
- [ ] `check:print-bw` passa; vias de OS e venda iguais às de antes.
- [ ] Código novo comentado (PR6).

## 11. Casos de teste

### Unidade

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `montarDadosProposta` com detalhe **com** custos | Nenhuma chave de custo, margem, insumo, parâmetro (`markup`, `perda`, `custo_hora`) ou `preco_*` de móvel em lugar nenhum da saída (varredura recursiva das chaves) |
| 02 | Detalhe `RASCUNHO` | `faixa` "PRÉVIA…"; `validadeTexto` "15 dias a partir do envio" |
| 03 | Detalhe `ENVIADO` com validade 21/10/2026 | Sem faixa; "até 21/10/2026" |
| 04 | `VENCIDO` / `RECUSADO` / `SUBSTITUIDO` (com v3 existente) | Faixas do D6 |
| 05 | Ambiente sem móveis | Fora da saída |
| 06 | Desconto `PERCENTUAL` 500 bp | `percentualTexto` "5%" |
| 07 | Desconto `VALOR` | `percentualTexto` null |
| 08 | Sinal zero | `sinal` null |
| 09 | Cenário B da Spec 05 | Soma de `totalCentavos` dos ambientes + instalação = `subtotalCentavos` |
| 10 | `nomeArquivoProposta` com cliente `A/B: "Móveis" <SP>` | "Proposta ORC-… v1 - A B Móveis SP" |
| 11 | `nomeArquivoProposta` sem cliente | "Proposta ORC-… v1" |

### Componentes

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 12 | Template com o cenário B | Textos da §6.2; nenhum "R$" ao lado de móvel |
| 13 | Observações com 3 linhas | 3 linhas no documento |
| 14 | `useImprimirProposta` com a fila rejeitando | `imprimirComPagina` não é chamado; toast de erro |
| 15 | `useImprimirProposta` | Título trocado durante a impressão e restaurado no `afterprint` |
| 16 | `EnviarModal`: "Enviar e gerar proposta" | `enviar` antes de `imprimir`; com `422`, nenhum dos dois termina |

### Roteiro manual (app instalado ou `tauri dev`)

1. Orçamento do cenário B em rascunho → "Proposta" → conferir a faixa de prévia → **Salvar como PDF** → abrir o arquivo.
2. Conferir os valores com a Spec 05 §11.1 e a soma na calculadora.
3. Enviar com "Enviar e gerar proposta"; conferir a validade no PDF e o evento no histórico ("Enviado com total de R$ …").
4. Criar 3 ambientes com 6 móveis cada e descrições longas: 2 páginas, sem móvel cortado.
5. Logar como vendedor sem custos e como master: PDFs idênticos.
6. Nova versão → reimprimir a v1: faixa "VERSÃO SUBSTITUÍDA pela v2".
7. Imprimir uma OS em cupom e em A4 em seguida: iguais às de antes.
