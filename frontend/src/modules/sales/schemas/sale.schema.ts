import z from 'zod';

import { ProductSaleReadSchema } from './productSale.schema';
import { PaymentSaleReadSchema } from './paymentSale.schema';
import { CustomerDiscriminatedSchema } from './customers.schema';

export const SaleCreateSchema = z.object({
  cliente_id: z.number().optional(),
  funcionario_id: z.number({ required_error: 'Funcionário é obrigatório' }),
});

export type SaleCreate = z.infer<typeof SaleCreateSchema>;

export const SaleUpdateSchema = SaleCreateSchema.extend({
  entrega: z.number().min(0).optional(),
  desconto: z.number().min(0).optional(),
  observacao: z.string().max(255).optional(),
}).partial();

export type SaleUpdate = z.infer<typeof SaleUpdateSchema>;

export const SaleSimpleReadSchema = z.object({
  id: z.number(),

  cliente_id: z.number().nullable().optional(),
  funcionario_id: z.number(),

  total: z.number(),

  status: z.enum(['RASCUNHO', 'FINALIZADA', 'CANCELADA']),

  cliente: CustomerDiscriminatedSchema.nullable().optional(),
});

export type SaleSimpleRead = z.infer<typeof SaleSimpleReadSchema>;

export const SaleReadSchema = SaleSimpleReadSchema.extend({
  entrega: z.number(),
  descontos: z.number(),
  subtotal: z.number(),
  troco: z.number(),

  observacao: z.string().optional(),

  produtos: z.array(ProductSaleReadSchema),
  pagamentos: z.array(PaymentSaleReadSchema),
});

export type SaleRead = z.infer<typeof SaleReadSchema>;

export const SaleSearchSchema = z.object({
  search: z.string().max(255).nullable().optional(),
  status: z.enum(['RASCUNHO', 'FINALIZADA', 'CANCELADA']).nullable().optional(),
});

export type SaleSearch = z.infer<typeof SaleSearchSchema>;

export const SaleListSchema = z.object({
  filters: SaleSearchSchema,
  vendas: SaleSimpleReadSchema.array(),
  total: z.number(),
  page: z.number(),
  limit: z.number(),
  total_pages: z.number(),
  links: z.object({
    next: z.string().nullable().optional(),
    prev: z.string().nullable().optional(),
  }),
});

export type SaleList = z.infer<typeof SaleListSchema>;

export const SalesStatusSchema = z.object({
  vendas_em_aberto: z.number(),
  vendas_finalizadas: z.number(),
  vendas_canceladas: z.number(),
  ticket_medio: z.number(),
});

export type SalesStatus = z.infer<typeof SalesStatusSchema>;
