/**
 * @fileoverview Zod validation schemas for product forms
 * @description Validates product and stock data for create/edit
 */

import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';

export const productSchema = z.object({
  nome: z
    .string({ required_error: 'Nome e obrigatorio' })
    .min(3, 'Nome deve ter no minimo 3 caracteres')
    .max(255),
  codigo_produto: z
    .string({ required_error: 'Codigo do produto e obrigatorio' })
    .min(2, 'Codigo deve ter no minimo 2 caracteres')
    .max(100),
  codigo_barras: z.string().max(100).optional().or(z.literal('')),
  unidade_medida: z.string().max(25).optional().or(z.literal('')),
  categoria: z.string().max(100).optional().or(z.literal('')),
  marca: z.string().max(100).optional().or(z.literal('')),
  fornecedor_id: z
    .string()
    .optional()
    .or(z.literal(''))
    .refine((val) => (val ? /^\d+$/.test(val) : true), {
      message: 'Fornecedor deve ser um numero',
    }),
  localizacao_estoque: z.string().max(255).optional().or(z.literal('')),
  observacao: z.string().max(500).optional().or(z.literal('')),

  valor_entrada: z.number().optional().or(z.literal(0)),
  valor_varejo: z
    .number({ required_error: 'Valor de varejo e obrigatorio' })
    .min(0.01, 'Valor de varejo deve ser maior que zero'),
  valor_atacado: z.number().optional().or(z.literal(0)),

  quantidade: z
  .number({ required_error: 'Quantidade e obrigatoria' })
  .min(1, 'Quantidade deve ser maior que zero'),
  quantidade_minima: z
  .number()
  .optional(),
  quantidade_ideal: z
  .number()
  .optional(),
});

export const productValidationSchema = toTypedSchema(productSchema);
export type ProductSchemaData = z.infer<typeof productSchema>;
