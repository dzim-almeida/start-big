import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';

export const ServiceReadSchema = z.object({
  id: z.number().int().positive(),
  descricao: z.string().min(1, 'Descrição é obrigatória'),
  valor: z.number().int().nonnegative(),
  ativo: z.boolean(),
});

export const ServiceCreateSchema = z.object({
  descricao: z.string().min(1, 'Descrição é obrigatória').max(255),
  valor: z.number().int().nonnegative(),
});

export const ServiceUpdateSchema = z.object({
  descricao: z.string().min(1).max(255).optional(),
  valor: z.number().int().nonnegative().optional(),
});

export const ServiceFormSchema = z.object({
  descricao: z
    .string({ required_error: 'Descrição é obrigatória' })
    .min(3, 'Descrição deve ter no mínimo 3 caracteres')
    .max(255, 'Descrição deve ter no máximo 255 caracteres'),
  valor: z
    .number({ required_error: 'Valor é obrigatório' })
    .nonnegative('Valor não pode ser negativo'),
});

export const PaginatedServicesSchema = z.object({
  items: z.array(ServiceReadSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  limit: z.number().int().positive(),
  pages: z.number().int().nonnegative(),
});

export type ServiceReadZod = z.infer<typeof ServiceReadSchema>;
export type ServiceCreateZod = z.infer<typeof ServiceCreateSchema>;
export type ServiceUpdateZod = z.infer<typeof ServiceUpdateSchema>;
export type ServiceFormZod = z.infer<typeof ServiceFormSchema>;
export type PaginatedServicesZod = z.infer<typeof PaginatedServicesSchema>;

export const servicoFormValidationSchema = toTypedSchema(ServiceFormSchema);
