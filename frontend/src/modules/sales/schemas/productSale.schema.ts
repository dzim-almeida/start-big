import z from 'zod';

import { SaleFinanceSummarySchema } from './sale.schema';

export const ProductSaleBaseSchema = z.object({
  tipo_produto: z.enum(['CADASTRADO', 'AVULSO']),
  produto_id: z.number().optional(),
  descricao_avulsa: z.string().max(100).optional(),
  quantidade: z.number({ required_error: 'Quantidade é obrigatória' }).min(1),
  valor_unitario: z.number().min(0).optional(),
  desconto: z.number(),
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
    if (!data.valor_unitario) {
      ctx.addIssue({
        code: 'custom',
        path: ['valor_unitario'],
        message: 'Valor unitário é obrigatório para produtos avulsos',
      });
    }
  }
});

export type ProductSaleCreate = z.infer<typeof ProductSaleCreateSchema>;

export const ProductSaleUpdateSchema = ProductSaleBaseSchema.omit({
  tipo_produto: true,
  produto_id: true,
}).partial();

export type ProductSaleUpdate = z.infer<typeof ProductSaleUpdateSchema>;

export const ProductSaleReadSchema = ProductSaleBaseSchema.extend({
  id: z.number(),
  sku: z.string().optional(),
  nome: z.string(),
  subtotal: z.number().min(0),
  total: z.number().min(0),
}).omit({ descricao_avulsa: true });

export const ProductAlterationSchema = z.object({
  produto_adicionado: ProductSaleReadSchema,
  financeiro_atualizado: SaleFinanceSummarySchema,
});

export type ProductAlteration = z.infer<typeof ProductAlterationSchema>;

export const ProductSaleListItemSchema = z.object({
  id: z.number(),
  nome: z.string(),
  sku: z.string().optional(),
  preco: z.number(),
  quantidade: z.number(),
  imagem_url: z.string().optional(),
}).array();

export type ProductSaleListItem = z.infer<typeof ProductSaleListItemSchema>;
