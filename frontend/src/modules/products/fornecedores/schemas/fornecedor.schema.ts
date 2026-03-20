import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';

const unmask = (v: string) => v.replace(/\D/g, '');

export const FornecedorReadSchema = z.object({
  id: z.number().int().positive(),
  nome: z.string(),
  cnpj: z.string(),
  nome_fantasia: z.string().nullable().optional(),
  ie: z.string().nullable().optional(),
  telefone: z.string().nullable().optional(),
  celular: z.string().nullable().optional(),
  email: z.string().nullable().optional(),
  representante: z.string().nullable().optional(),
  ativo: z.boolean(),
});

export const FornecedorFormSchema = z.object({
  nome: z
    .string({ required_error: 'Nome é obrigatório' })
    .min(2, 'Nome deve ter no mínimo 2 caracteres')
    .max(255),
  cnpj: z
    .string({ required_error: 'CNPJ é obrigatório' })
    .min(1, 'CNPJ é obrigatório')
    .refine((v) => unmask(v).length === 14, 'CNPJ deve ter 14 dígitos'),
  nome_fantasia: z.string().max(255).optional().or(z.literal('')),
  ie: z.string().max(14).optional().or(z.literal('')),
  telefone: z.string().optional().or(z.literal('')),
  celular: z.string().optional().or(z.literal('')),
  email: z
    .string()
    .optional()
    .refine((v) => !v || v === '' || z.string().email().safeParse(v).success, 'Email inválido'),
  representante: z.string().max(255).optional().or(z.literal('')),
});

export type FornecedorReadType = z.infer<typeof FornecedorReadSchema>;
export type FornecedorFormType = z.infer<typeof FornecedorFormSchema>;

export const fornecedorFormValidationSchema = toTypedSchema(FornecedorFormSchema);
