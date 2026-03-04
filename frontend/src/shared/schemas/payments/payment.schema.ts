import z from "zod";

export const PaymentFormCreateSchema = z.object({
    nome: z.string().min(2, 'O nome deve ter no mínimo 2 caracteres').max(50, 'O nome deve ter no máximo 50 caracteres'),
    ativo: z.boolean(),
})

export const PaymentFormReadSchema = z.object({
    ...PaymentFormCreateSchema.shape,
    id: z.number().int().positive()
})

export const PaymentFormUpdateSchema = z.object({
    nome: z.string().min(2, 'O nome deve ter no mínimo 2 caracteres').max(50, 'O nome deve ter no máximo 50 caracteres').optional(),
    ativo: z.boolean().optional(),
})

