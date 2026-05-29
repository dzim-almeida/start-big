import z from 'zod';

import { PaginationBaseSchema } from '@/shared/schemas/pagination/pagination.schema';

// ── Re-exports dos schemas Read (fonte de verdade em shared/) ──────────────

export {
  CustomerPFReadSchema,
  CustomerPJReadSchema,
  CustomerUnionReadSchema,
  isCustomerPF,
} from '@/shared/schemas/customer/customer.schema';

export type {
  CustomerPFReadSchemaDataType,
  CustomerPJReadSchemaDataType,
  CustomerUnionReadSchemaDataType,
} from '@/shared/schemas/customer/customer.schema';

// ── Params (filtros de busca) ──────────────────────────────────────────────

const CustomerParamsSchema = z.object({
  search: z.string().max(255, 'A busca pode ter no máximo 255 caracteres').optional().nullable(),
  only_active: z.boolean().optional(),
  page: z.number().int().min(1).optional(),
  limit: z.number().int().min(1).max(100).optional(),
});

export type CustomerParamsDataType = z.infer<typeof CustomerParamsSchema>;

// ── Pagination ─────────────────────────────────────────────────────────────

import { CustomerUnionReadSchema } from '@/shared/schemas/customer/customer.schema';

const CustomerFilterSchema = z.object({
  search: z.string().max(255).optional().nullable(),
  only_active: z.boolean().optional(),
});

export const CustomerPaginationSchema = z.object({
  ...PaginationBaseSchema.shape,
  filters: CustomerFilterSchema,
  items: z.array(CustomerUnionReadSchema),
});

export type CustomerPaginationDataType = z.infer<typeof CustomerPaginationSchema>;

// ── Stats (calculadas localmente) ──────────────────────────────────────────

export const CustomerStatsSchema = z.object({
  total: z.number().int(),
  ativos: z.number().int(),
  pf: z.number().int(),
  pj: z.number().int(),
});

export type CustomerStatsDataType = z.infer<typeof CustomerStatsSchema>;
