import z from 'zod';
import { toTypedSchema } from '@vee-validate/zod';

import { OrderServiceBaseSchema } from './orderService.schema';

import { OsStatusEnum } from './enums/osEnums.schema';

import {
  CustomerPFReadSchema,
  CustomerPJReadSchema,
} from './relationship/customer/customer.schema';
import { EmployeeReadSchema } from './relationship/employee/employee.schema';
import { OsEquipReadSchema } from './relationship/osEquip.schema';
import { OsItemReadSchema } from './relationship/osItem.schema';
import { OsPaymentReadSchema } from './relationship/osPayment.schema';
import { OsImageReadSchema } from './relationship/osPhoto.schema';
import { PaginationBaseSchema } from '@/shared/schemas/pagination/pagination.schema';

const OrderServiceParamsSchema = z.object({
  search: z.string().max(255, 'A busca pode ter no máximo 255 caracteres').nullish(),
  status: OsStatusEnum.nullish(),
  priority_sort: z.boolean().nullish(),
});

export const orderServiceParamsValidationSchema = toTypedSchema(OrderServiceParamsSchema);
export type OrderServiceParamsDataType = z.infer<typeof OrderServiceParamsSchema>;

export const OrderServiceReadSchema = z.object({
  ...OrderServiceBaseSchema.shape,

  // Identificação
  id: z.number().int().positive(),
  numero_os: z.string().max(20, 'O número da OS deve ter máximo 20 caracteres'),

  // Estados
  status: OsStatusEnum,

  // Financeiro
  valor_bruto: z.number().int().positive(),
  valor_total: z.number().int().positive(),

  // Datas
  data_finalizacao: z.string().datetime().optional(),
  data_criacao: z.string().datetime(),
  data_atualizacao: z.string().datetime(),

  // Status Lógico
  ativo: z.boolean(),

  // Relacionamentos
  cliente: z.union([CustomerPFReadSchema, CustomerPJReadSchema]),
  funcionario: EmployeeReadSchema,
  equipamento: OsEquipReadSchema,
  itens: z.array(OsItemReadSchema),
  pagamentos: z.array(OsPaymentReadSchema),
  fotos: z.array(OsImageReadSchema),
});

export const orderServiceReadValidationSchema = toTypedSchema(OrderServiceReadSchema);
export type OrderServiceReadDataType = z.infer<typeof OrderServiceReadSchema>;

export const OrderServicePaginationSchema = z.object({
  total_items: z.number().int().nonnegative(),
  page: z.number().int().min(1),
  limit: z.number().int().min(1),
  total_pages: z.number().int().nonnegative(),
  links: z
    .object({
      next: z.string().nullable().optional(),
      prev: z.string().nullable().optional(),
    })
    .nullable()
    .optional(),
  filters: OrderServiceParamsSchema,
  items: z.array(OrderServiceReadSchema),
});

export type OrderServicePaginationDataType = z.infer<typeof OrderServicePaginationSchema>;

export const OrderServiceStatsSchema = z.object({
  total: z.number().int(),
  abertas: z.number().int(),
  finalizadas: z.number().int(),
  ticket_medio: z.number().int(),
});

export type OrderServiceStatsDataType = z.infer<typeof OrderServiceStatsSchema>;
