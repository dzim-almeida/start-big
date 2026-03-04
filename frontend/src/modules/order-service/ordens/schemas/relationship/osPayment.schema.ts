import z, { string } from 'zod';

import { PaymentFormReadSchema } from '@/shared/schemas/payments/payment.schema';

import { OsCardsFlagEnum } from '../enums/osEnums.schema';

export const OsPaymentCreateSchema = z.object({
  forma_pagamento_id: z.number().int().positive(),
  valor: z.number().int().min(1, 'O valor deve ser maior que 0'),
  parcelas: z.number().int().min(1, 'O número de parcelas deve ser maior que 0'),
  bandeira_cartao: OsCardsFlagEnum.optional(),
  detalhes: string().max(500, 'Detalhes deve ter no máximo 500 caracteres').optional(),
});

export type OsPaymentCreateSchemaDataType = z.infer<typeof OsPaymentCreateSchema>;

export const OsPaymentReadSchema = z.object({
  id: z.number().int().positive(),
  ordem_servico_id: z.number().int().positive(),
  forma_pagamento: PaymentFormReadSchema,
  valor: z.number().int(),
  parcelas: z.number().int(),
  bandeira_cartao: OsCardsFlagEnum.optional(),
  detalhes: z.string().max(500, 'Detalhes deve ter no máximo 500 caracteres').optional()
});
