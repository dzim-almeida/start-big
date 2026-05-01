import z from 'zod';

export const PaymentSaleBaseSchema = z.object({
  forma_pagamento_id: z.number({required_error: 'Forma de pagamento é obrigatória'}),
  parcelado: z.boolean(),
  qtd_parcelas: z.number(),
  valor: z.number({required_error: 'Valor é obrigatório'}).min(0),
});

export const PaymentSaleCreateSchema = PaymentSaleBaseSchema.superRefine((data, ctx) => {
  if (data.parcelado && !data.qtd_parcelas) {
    ctx.addIssue({
      code: 'custom',
      path: ['qtd_parcelas'],
      message: 'Quantidade de parcelas é obrigatória para pagamentos parcelados',
    });
  }
});

export const PaymentSaleReadSchema = PaymentSaleBaseSchema.extend({
  id: z.number(),
  data_pagamento: z.string().datetime(),
}).merge(PaymentSaleBaseSchema);

export const FinishPaymentSaleSchema = z.object({
  pagamentos: PaymentSaleCreateSchema.array(),
});

export type PaymentSaleCreate = z.infer<typeof FinishPaymentSaleSchema>
