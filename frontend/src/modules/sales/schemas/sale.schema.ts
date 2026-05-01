import z from 'zod';

import { ProductSaleReadSchema } from './productSale.schema';
import { PaymentSaleReadSchema } from './paymentSale.schema';

export const SaleCreateSchema = z.object({
  cliente_id: z.number().optional(),
  funcionario_id: z.number({required_error: 'Funcionário é obrigatório'}),
});

export type SaleCreate = z.infer<typeof SaleCreateSchema>

export const SaleUpdateSchema = SaleCreateSchema.extend({
  entrega: z.number().min(0).optional(),
  desconto: z.number().min(0).optional(),
  observacao: z.string().max(255).optional(),
}).partial();

export type SaleUpdate = z.infer<typeof SaleUpdateSchema>

export const SaleSimpleReadSchema = z.object({
  id: z.number(),

  cliente_id: z.number().optional(),
  funcionario_id: z.number(),

  entrega: z.number(),
  descontos: z.number(),
  subtotal: z.number(),
  total: z.number(),
  troco: z.number(),

  status: z.enum(['RASCUNHO', 'CONCLUIDA', 'CANCELADA']),
  observacao: z.string().optional(),
  criado_em: z.string().datetime(),
  atualizado_em: z.string().datetime(),
});

export type SaleSimpleRead = z.infer<typeof SaleSimpleReadSchema>

export const SaleReadSchema = SaleSimpleReadSchema.extend({
  produtos: z.array(ProductSaleReadSchema),
  pagamentos: z.array(PaymentSaleReadSchema),
});

export type SaleRead = z.infer<typeof SaleReadSchema>

export const SaleSearchSchema = z.object({
  search: z.string().max(255).optional(),
  status: z.enum(['RASCUNHO', 'CONCLUIDA', 'CANCELADA']).optional(),
});

export type SaleSearch = z.infer<typeof SaleSearchSchema>

export const SaleListSchema = z.object({
  filters: SaleSearchSchema,
  vendas: SaleSimpleReadSchema.array(),
  total: z.number(),
  page: z.number(),
  limit: z.number(),
  total_pages: z.number(),
  links: z.object({
    next: z.string().optional(),
    prev: z.string().optional(),
  }),
});

export type SaleList = z.infer<typeof SaleListSchema>

export const SaleFinanceSummarySchema = z.object({
  subtotal: z.number(),
  descontos: z.number(),
  entrega: z.number(),
  total: z.number(),
});

export const SaleStatusSummarySchema = z.object({
  vendas_em_aberto: z.number(),
  vendas_finalizadas: z.number(),
  vendas_canceladas: z.number(),
  ticket_medio: z.number(),
});
