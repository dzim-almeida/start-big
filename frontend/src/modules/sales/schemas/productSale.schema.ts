import z from 'zod';

export const ProductSaleBaseSchema = z.object({
  tipo_produto: z.enum(['CADASTRADO', 'AVULSO']),
  produto_id: z.number().nullable().optional(),
  descricao_avulsa: z.string().max(100).optional(),
  // Quanto a loja PAGOU por unidade. Só para item AVULSO — o cadastrado tem o
  // custo no livro de estoque. Campo INTERNO: nenhum template de impressão o
  // exibe, por decisão explícita.
  custo_unitario: z.number().min(0).nullable().optional(),
  // > 0 e não ≥ 1: produto a granel vende 0,5 kg (venda fracionada). Quem
  // aceita ou recusa a fração pela unidade é o servidor.
  quantidade: z.number({ required_error: 'Quantidade é obrigatória' }).positive('A quantidade deve ser maior que zero'),
  valor_unitario: z
    .number()
    .min(0)
    .optional()
    .transform((val) => (!!val ? 0 : val)),
  desconto: z.number().nullable().optional(),
  // Venda por embalagem (fardo/caixa): a quantidade é de embalagens e o preço é
  // o dela; o estoque baixa quantidade × fator. Só com `usarEmbalagens` ligado.
  embalagem_id: z.number().nullable().optional(),
});

export const ProductSaleCreateSchema = ProductSaleBaseSchema.superRefine((data, ctx) => {
  if (data.tipo_produto === 'AVULSO') {
    if (!data.descricao_avulsa) {
      ctx.addIssue({
        code: 'custom',
        path: ['descricao_avulsa'],
        message: 'Descrição avulsa é obrigatória para produtos avulsos',
      });
    }
    if (!data.valor_unitario || data.valor_unitario <= 0) {
      ctx.addIssue({
        code: 'custom',
        path: ['valor_unitario'],
        message: 'Valor unitário é obrigatório para produtos avulsos',
      });
    }
  }

  if (data.desconto) {
    if (data.desconto > (data.valor_unitario || 0) * data.quantidade) {
      ctx.addIssue({
        code: 'custom',
        path: ['desconto'],
        message: 'Desconto não pode ser maior que o subtotal do item',
      });
    }
  }
});

export type ProductSaleCreate = z.infer<typeof ProductSaleCreateSchema>;

export const ProductSaleUpdateSchema = ProductSaleBaseSchema
  .omit({
    tipo_produto: true,
    produto_id: true,
  })
  .partial()
  .refine(
    (data) => {
      return (data.desconto || 0) <= (data.valor_unitario || 0) * (data.quantidade || 0);
    },
    {
      message: 'O desconto não pode ser maior que o subtotal',
      path: ['desconto'],
    },
  );

export type ProductSaleUpdate = z.infer<typeof ProductSaleUpdateSchema> & { codigo_gerente?: string };

export const ProductSaleReadSchema = ProductSaleBaseSchema.extend({
  id: z.number(),
  sku: z.string().nullable().optional(),
  nome: z.string(),
  subtotal: z.number().min(0),
  total: z.number().min(0),
  imagem_url: z.string().nullable().optional(),
  unidade_medida: z.string().nullable().optional(),
  estoque_disponivel: z.number().nullable().optional(),
  // Congelados na linha (backend mais antigo não manda: vale 1 / nulo).
  fator_embalagem: z.number().optional().default(1),
  sigla_embalagem: z.string().nullable().optional(),
  // Regra de preço por quantidade aplicada (§6.1). `desconto` continua sendo
  // só o do operador; `total` já desconta os dois. Backend antigo não manda.
  desconto_regra: z.number().optional().default(0),
  regra_preco: z.string().nullable().optional(),
  regra_descricao: z.string().nullable().optional(),
  valor_unitario_tabela: z.number().nullable().optional(),
  valor_unitario: z.number().transform((val) => (!val ? 0 : val)),
  desconto: z.number().transform((val) => (!val ? 0 : val)),
}).omit({ descricao_avulsa: true });

export type ProductSaleRead = z.infer<typeof ProductSaleReadSchema>;

export const SaleFinanceSummarySchema = z.object({
  subtotal: z.number(),
  descontos: z.number(),
  descontos_regra: z.number().optional().default(0),
  entrega: z.number(),
  total: z.number(),
});

export const ProductAlterationSchema = z.object({
  produto_adicionado: ProductSaleReadSchema,
  financeiro_atualizado: SaleFinanceSummarySchema,
  // As OUTRAS linhas que a regra de preço mudou (17 latas em duas linhas: as
  // duas ganham a regra). Vazio sem regra; backend antigo não manda.
  itens_alterados: z.array(ProductSaleReadSchema).optional().default([]),
});

export type ProductAlteration = z.infer<typeof ProductAlterationSchema>;

export const ProductSaleListItemSchema = z
  .object({
    id: z.number(),
    nome: z.string(),
    sku: z.string().nullable().optional(),
    // Usado só pelo leitor de código de barras: é o que permite exigir
    // correspondência exata antes de somar um item ao carrinho sozinho.
    // Opcional porque backend mais antigo que o frontend não devolve o campo.
    codigo_barras: z.string().nullable().optional(),
    preco: z.number(),
    estoque: z.number(),
    quantidade_minima: z.number().nullable().optional(),
    imagem_url: z.string().nullable().optional(),
    // Só vêm com `usar_embalagens` ligado; o preço já vem resolvido pelo backend.
    embalagens: z
      .array(
        z.object({
          id: z.number(),
          sigla: z.string(),
          descricao: z.string().nullable().optional(),
          fator: z.number(),
          codigo_barras: z.string().nullable().optional(),
          preco: z.number(),
        }),
      )
      .optional()
      .default([]),
    so_embalagem_fechada: z.boolean().optional().default(false),
  })
  .array();

export type ProductSaleListItem = z.infer<typeof ProductSaleListItemSchema>;
export type EmbalagemPdv = ProductSaleListItem[number]['embalagens'][number];

export const ItemSaleFormSchema = z.object({
  descricao: z.string().min(1, 'Informe a descrição do produto'),
  valor_unitario: z.number().min(0.01, 'Informe um valor unitário válido'),
  quantidade: z.number().min(1, 'A quantidade deve ser pelo menos 1'),
  desconto: z.number().min(0).default(0),
  // Custo interno do avulso (em reais no form, centavos no envio). Opcional:
  // deixar zerado só significa "não sei/não quero declarar", e aí o item entra
  // no relatório sem custo.
  custo: z.number().min(0).default(0),
}).refine((data) => {
  return data.desconto <= data.valor_unitario * data.quantidade;
}, {
  path: ['desconto'],
  message: 'O desconto não pode ser maior que o subtotal',
})

export type ItemSaleForm = z.infer<typeof ItemSaleFormSchema>;