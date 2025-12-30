/**
 * @fileoverview Schemas de validação do onboarding
 * @description Schemas Zod para validação dos formulários de configuração
 * inicial da empresa.
 */

import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';

/**
 * Segmentos válidos
 */
const businessSegments = [
  'assistencia_tecnica',
  'oficina_mecanica',
  'mercado',
  'marcenaria',
  'eletricista',
  'outros',
] as const;

/**
 * Schema para seleção de segmento (Step 1)
 */
export const segmentSchema = z.object({
  segmento: z.enum(businessSegments, {
    required_error: 'Selecione um segmento',
    invalid_type_error: 'Segmento inválido',
  }),
});

export const segmentValidationSchema = toTypedSchema(segmentSchema);
export type SegmentFormData = z.infer<typeof segmentSchema>;

/**
 * Schema para dados da empresa (Step 2)
 */
export const companySchema = z.object({
  razaoSocial: z
    .string({ required_error: 'Razão social é obrigatória' })
    .min(3, 'Razão social deve ter no mínimo 3 caracteres')
    .max(150, 'Razão social deve ter no máximo 150 caracteres'),
  nomeFantasia: z
    .string({ required_error: 'Nome fantasia é obrigatório' })
    .min(2, 'Nome fantasia deve ter no mínimo 2 caracteres')
    .max(100, 'Nome fantasia deve ter no máximo 100 caracteres'),
  tipoDocumento: z.enum(['CNPJ', 'CPF'], {
    required_error: 'Selecione o tipo de documento',
  }),
  documento: z
    .string({ required_error: 'Documento é obrigatório' })
    .min(11, 'Documento inválido')
    .max(18, 'Documento inválido'),
  celular: z
    .string({ required_error: 'Celular é obrigatório' })
    .min(14, 'Celular inválido')
    .max(15, 'Celular inválido'),
  email: z
    .string({ required_error: 'E-mail é obrigatório' })
    .email('E-mail inválido')
    .max(255, 'E-mail deve ter no máximo 255 caracteres'),
  telefone: z
    .string()
    .max(14, 'Telefone inválido')
    .optional()
    .or(z.literal('')),
});

export const companyValidationSchema = toTypedSchema(companySchema);
export type CompanyFormData = z.infer<typeof companySchema>;

/**
 * Schema para endereço (Step 3)
 */
export const addressSchema = z.object({
  cep: z
    .string({ required_error: 'CEP é obrigatório' })
    .length(9, 'CEP deve ter 8 dígitos'),
  logradouro: z
    .string({ required_error: 'Logradouro é obrigatório' })
    .min(3, 'Logradouro deve ter no mínimo 3 caracteres')
    .max(200, 'Logradouro deve ter no máximo 200 caracteres'),
  numero: z
    .string({ required_error: 'Número é obrigatório' })
    .min(1, 'Número é obrigatório')
    .max(10, 'Número deve ter no máximo 10 caracteres'),
  complemento: z
    .string()
    .max(100, 'Complemento deve ter no máximo 100 caracteres')
    .optional()
    .or(z.literal('')),
  bairro: z
    .string({ required_error: 'Bairro é obrigatório' })
    .min(2, 'Bairro deve ter no mínimo 2 caracteres')
    .max(100, 'Bairro deve ter no máximo 100 caracteres'),
  cidade: z
    .string({ required_error: 'Cidade é obrigatória' })
    .min(2, 'Cidade deve ter no mínimo 2 caracteres')
    .max(100, 'Cidade deve ter no máximo 100 caracteres'),
  estado: z
    .string({ required_error: 'Estado é obrigatório' })
    .length(2, 'Estado deve ter 2 caracteres'),
});

export const addressValidationSchema = toTypedSchema(addressSchema);
export type AddressFormData = z.infer<typeof addressSchema>;
