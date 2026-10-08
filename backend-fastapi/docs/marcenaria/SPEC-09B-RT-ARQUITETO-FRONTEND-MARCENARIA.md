# Spec 09B — RT do Arquiteto (Frontend)

| Campo        | Valor                                                                                      |
|--------------|--------------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                            |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado (cadastro de fornecedor)             |
| Dependências | Specs 04B (Configurações › Marcenaria), 06B (editor), 06A Revisão 3, 09A Revisão 1         |
| Bloqueia     | —                                                                                          |
| Referência   | SPEC-00: C5a, C5b, C5c, C5d, C5e, P4 · PR1, PR3, PR6                                       |

> **Revisão 1 (08/10/2026) — dependências escritas.** A versão anterior citava a "06A Revisão 3" e a "09A Revisão 1", que não existiam. As duas foram escritas em 08/10: a **06A Revisão 3** traz o `rt_padrao_bp` no orçamento, o `PUT /rt` sem percentual (mantém o gravado ou usa o padrão; só `manage` para trocar o arquiteto, `view_custos` para mandar `rt_bp`) e o `valor_previsto_centavos`; a **09A Revisão 1** traz a `conta` de cada arquiteto no detalhe. Também: a ordem das decisões (D11 e D12 estavam trocadas) e dos casos de teste foi acertada; nada mudou no conteúdo.

---

## 1. Objetivo

1. No orçamento, dizer **qual arquiteto indicou** o cliente e com que percentual de RT.
2. Ver quanto o arquiteto vai receber e, depois da OS finalizada, a **conta a pagar** dele.
3. Cadastrar o arquiteto sem sair do orçamento, como um tipo próprio de fornecedor.
4. Ajustar em Configurações o **prazo** para pagar o RT.

## 2. Escopo

**Dentro do escopo**
- Bloco "Arquiteto" no editor de orçamento (um arquiteto por orçamento na tela, C5a).
- RT no painel de custos e na faixa do orçamento aprovado.
- Tipo de fornecedor "Arquiteto / Designer" (só com a capacidade `orcamento_tecnico`).
- Campo "Prazo para pagar o RT" em Configurações › Marcenaria.

**Fora do escopo**
- Vários arquitetos no mesmo orçamento (o modelo aceita; a tela é de um, SPEC-00 §7).
- Tela própria de RT a pagar: a conta aparece em **Contas a Pagar**, como qualquer outra.

---

## 3. Arquivos afetados

```
frontend/src/modules/
├── products/suppliers/
│   ├── types/fornecedor.types.ts                     # ALTERAR ⚠️ — 'arquiteto' em SupplierTipo
│   ├── schemas/fornecedor.schema.ts                  # ALTERAR ⚠️ — 'arquiteto' no enum
│   ├── components/SupplierTypeSelector.vue           # ALTERAR ⚠️ — opção só com a capacidade
│   ├── components/FornecedorFormModal.vue            # ALTERAR ⚠️ — seção do arquiteto
│   ├── components/FornecedorTable.vue                # ALTERAR ⚠️ — selo do tipo
│   ├── components/form/DadosArquitetoSection.vue     # CRIAR
│   └── composables/useFornecedorModal.ts             # ALTERAR ⚠️ — abrir com tipo e callback
├── configuracoes/components/sections/marcenaria/components/Marcenaria.vue   # ALTERAR — prazo do RT
├── configuracoes/schemas/configuracaoMarcenaria.schema.ts                    # ALTERAR — campo novo
└── marcenaria/orcamentos/
    ├── components/editor/BlocoArquiteto.vue          # CRIAR
    ├── components/editor/PainelCustos.vue            # ALTERAR — linha do RT com o arquiteto
    ├── components/editor/EditorFaixaStatus.vue       # ALTERAR — situação da conta de RT
    └── services/orcamento.service.ts                 # ALTERAR — putRt
```

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Bloco **"Arquiteto"** no editor, entre "Cliente e projeto" e "Ambientes": um select "Quem indicou" (com "Nenhum") e, **só com `view_custos`**, o campo "RT (%)". Quem não vê custos escolhe o arquiteto; o percentual vem do padrão da configuração (06A Revisão 3) | O vendedor é quem sabe quem indicou; o percentual é decisão de quem vê a margem (P4) |
| D2 | Arquiteto é um **fornecedor** (C5a) de tipo novo **`arquiteto`**, "Arquiteto / Designer". O seletor de tipo do cadastro de fornecedor mostra a opção **só** com `temOrcamentoTecnico`; nos outros segmentos o seletor é o de hoje | Separar o arquiteto do fornecedor de chapa deixa a lista do select curta e o cadastro com os campos certos. Sem a capacidade, ninguém vê o tipo novo |
| D3 | `DadosArquitetoSection`: Nome*, "Pessoa física ou jurídica" (CPF ou CNPJ, com a consulta de CNPJ da Spec 02 quando PJ), Escritório (`nome_fantasia`), Celular, Telefone, E-mail. Endereço, **dados bancários e PIX** e observações são as seções que todo fornecedor já tem | O PIX é por onde o RT é pago. Nada de campo novo no banco: tudo existe na tabela de fornecedores |
| D4 | O select lista os fornecedores ativos de tipo `arquiteto`, ordenados pelo nome; a busca acha por nome ou escritório. No fim da lista: **"Cadastrar arquiteto"**, que abre o cadastro de fornecedor já no tipo arquiteto e, ao salvar, seleciona o novo | Cadastrar sem sair do orçamento (mesmo princípio do cadastro rápido de insumo, 06B D31) |
| D5 | O cadastro de fornecedor ganha `openCreateModalWithCallback(tipo, callback)` e é montado no editor de orçamento (o modal hoje vive só na tela de Produtos) | Mesmo padrão do modal de cliente (`openCreateModalWithCallback`) |
| D6 | Com `view_custos`, embaixo do campo: o **valor previsto** ("Studio Renascer recebe R$ 739,11") e o efeito do modo do RT: "Modo: sai da margem — o preço do orçamento não muda." ou "Modo: embutido no preço — os preços sobem para cobrir o RT." | C5c. O dono vê na hora o que a escolha faz com o preço e com a margem |
| D7 | Escolher ou trocar o arquiteto salva na hora (`PUT /rt`, pela fila de escrita, 06B D7); o percentual salva pelo salvamento automático (800 ms) | Mesmo comportamento do resto do editor |
| D8 | Fora de `RASCUNHO`, o bloco é somente leitura. Sem `view_custos`, o vendedor vê só o nome do arquiteto | 06A D11, P4 |
| D9 | No **painel de custos**, a linha "RT arquiteto" passa a mostrar o nome e o percentual: "RT — Studio Renascer (8%)  R$ 739,11" | O número já aparecia (06B); faltava de quem é |
| D10 | Orçamento **aprovado**, com `view_custos`: a faixa (08B D12) ganha a linha da conta de RT: "RT de Studio Renascer: previsto R$ 739,11 · conta criada na finalização da OS" ou, depois de finalizada, "Conta a pagar de R$ 739,11, vence 05/12/2026 (Pendente)", com link **"Ver em Contas a Pagar"** quando a loja tem o módulo Financeiro | C5e: o dono sabe se o arquiteto já foi pago sem procurar |
| D11 | **Configurações › Marcenaria**, bloco "Preço e custos" (só com custos, 04B D8): "Prazo para pagar o RT (dias após finalizar a OS)", padrão 30, de 0 a 180, com a ajuda "A conta a pagar do arquiteto nasce quando a OS é finalizada e vence depois deste prazo." | C5e |
| D12 | **Arquiteto com 0%** (o RT padrão da configuração nasce em 0%, 04A): com `view_custos`, aviso âmbar no bloco: "Studio Renascer está sem percentual de RT. Informe o % ou defina um padrão em Configurações › Marcenaria." Também aparece no modal de envio entre os avisos (06B D36) | Sem o aviso, o vendedor escolhe o arquiteto, o % fica 0 e o RT é esquecido até o arquiteto cobrar |

---

## 5. Contratos consumidos

- `PUT /marcenaria/orcamentos/{id}/rt` (06A, Revisão 3).
- `arquitetos` no detalhe, com `valor_previsto_centavos` e `conta` (09A, Revisão 1).
- `GET/PUT /configuracoes/marcenaria` com `rt_vencimento_dias` (09A §5).
- Fornecedores: `GET /fornecedores` e `POST /fornecedores` existentes, com `tipo = "arquiteto"` (texto livre no backend).

---

## 6. Especificação técnica

### 6.1. Tipo de fornecedor ⚠️

```ts
// fornecedor.types.ts
export type SupplierTipo = 'produto' | 'transportadora' | 'entregador' | 'arquiteto';

// fornecedor.schema.ts — o enum aceita o valor novo; as regras dos outros tipos não mudam.
tipo: z.enum(['produto', 'transportadora', 'entregador', 'arquiteto'], { required_error: 'Tipo é obrigatório' }),
```

```ts
// SupplierTypeSelector.vue — a opção só existe onde o segmento faz orçamento técnico (D2).
const { temOrcamentoTecnico } = useCapacidades();
const opcoes = computed(() => [
  ...OPCOES_DE_HOJE,                                         // produto, transportadora, entregador
  ...(temOrcamentoTecnico.value
    ? [{ tipo: 'arquiteto' as SupplierTipo, label: 'Arquiteto / Designer',
         description: 'Profissionais que indicam clientes e recebem RT', icon: Ruler }]
    : []),
]);
```

- Validação da seção do arquiteto (no `superRefine` do schema, como os outros tipos): CPF **ou** CNPJ válido, conforme a escolha; nome obrigatório.
- `FornecedorTable`: selo "Arquiteto" (mesma paleta neutra dos outros tipos).

### 6.2. `BlocoArquiteto.vue`

```ts
const props = defineProps<{ orcamento: OrcamentoDetalhe; podeEditar: boolean }>();
const { data: fornecedores } = useFornecedoresQuery();                  // query que já existe
const arquitetos = computed(() =>
  (fornecedores.value ?? []).filter((f) => f.ativo && f.tipo === 'arquiteto'),   // só arquitetos ativos (D4)
);
const atual = computed(() => props.orcamento.arquitetos[0] ?? null);    // fase 1: um por orçamento

/** Troca o arquiteto: só o fornecedor; o % fica com o backend (padrão ou o já gravado). */
function escolher(fornecedorId: number | null) {
  fila.enfileirar((revisao) =>
    putRt(props.orcamento.id, revisao, fornecedorId ? [{ fornecedor_id: fornecedorId }] : []),
  );
}
```

- O percentual (com `view_custos`) usa o mesmo campo de % do editor (2 casas, convertido para bp com `Math.round`, 06B §7.7) e entra no salvamento automático como `rt` (o `useSalvamentoAutomatico` manda `PUT /rt` para esta chave, e `PATCH` para as outras).
- "Nenhum" envia a lista vazia.

### 6.3. Painel e faixa

- `PainelCustos`: "RT — {nome} ({%})" quando houver arquiteto; "RT — sem arquiteto" e R$ 0,00 quando não.
- `EditorFaixaStatus` (aprovado, com custos): texto do D10. O link "Ver em Contas a Pagar" leva a `finance-payable` com o filtro de busca pela descrição (`?busca=ORC-2026-000084`), só quando `useModulosStore().temModulo(MODULOS.FINANCEIRO)`; sem o módulo, só o texto.

---

## 7. Prova de não regressão (⚠️ PR1)

1. `npm run test` e `npx vue-tsc --noEmit`.
2. Informática, oficina, serigrafia e PDV: o seletor de tipo de fornecedor tem as mesmas 3 opções; cadastrar e editar fornecedor de cada tipo funciona igual; a tabela mostra os mesmos selos.
3. Tela de Produtos › Fornecedores: abrir "Novo fornecedor" continua começando pelo seletor de tipo (o `openCreateModal` de hoje não muda; o tipo pré-escolhido só vem do novo `openCreateModalWithCallback`).

## 8. Limitações conhecidas

- Um arquiteto por orçamento na tela (C5a; o modelo aceita vários).
- O RT é sempre sobre o total aprovado (09A D3); ajustes ficam na conta a pagar.

---

## 9. Critérios de aceite

- [ ] Vendedor sem custos escolhe o arquiteto; o % entra pelo padrão; ele não vê nem o % nem o valor.
- [ ] Dono escolhe o arquiteto, muda o %, vê o valor previsto e a frase do modo do RT; a margem e (no modo embutido) os preços se atualizam.
- [ ] "Cadastrar arquiteto" abre o cadastro no tipo arquiteto e, ao salvar, já seleciona o novo.
- [ ] Tipo "Arquiteto / Designer" só aparece na marcenaria.
- [ ] Orçamento aprovado mostra o RT previsto e, depois da finalização, a conta com status e vencimento.
- [ ] Prazo do RT editável em Configurações › Marcenaria.
- [ ] Prova de não regressão (§7); código comentado (PR6).

## 10. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `SupplierTypeSelector`, informática | 3 opções (snapshot) |
| 02 | `SupplierTypeSelector`, marcenaria | 4 opções; a 4ª é "Arquiteto / Designer" |
| 03 | Schema do fornecedor, tipo arquiteto, PJ sem CNPJ | Erro no CNPJ |
| 04 | `BlocoArquiteto` sem `view_custos` | Só o select; `putRt` sem `rt_bp` |
| 05 | `BlocoArquiteto` com custos, mudar o % | Um `PUT /rt` com `rt_bp` depois de 800 ms |
| 06 | Escolher "Nenhum" | `PUT /rt` com lista vazia |
| 07 | `openCreateModalWithCallback('arquiteto', cb)` | Modal no formulário do arquiteto (sem o seletor); `cb` chamado com o fornecedor criado |
| 08 | Faixa do aprovado com `conta: null` / com conta pendente | Textos do D10 |
| 09 | Faixa sem o módulo Financeiro | Sem o link |
| 10 | Configurações: prazo 200 | Erro "O prazo do RT deve ficar entre 0 e 180 dias." |
| 11 | Arquiteto com `rt_bp = 0`, com custos | Aviso do D12 no bloco e no modal de envio |

### Roteiro manual (dev)

1. Marcenaria, como vendedor sem custos: num rascunho, "Cadastrar arquiteto" (PJ, consulta de CNPJ, PIX), selecionar.
2. Como master: com o RT padrão ainda em 0%, ver o aviso do D12; definir 8% em Configurações; num orçamento novo, ver os 8%, mudar para 6%, alternar o modo do RT em Configurações e ver o efeito num orçamento novo.
3. Aprovar, finalizar a OS, ver a conta em Contas a Pagar e a linha na faixa do orçamento.
4. Informática: §7.
