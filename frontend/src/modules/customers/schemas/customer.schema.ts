/**
 * @fileoverview Zod validation schemas for customer forms
 * @description Validates customer data for both PF (individual) and PJ (company) types
 * Uses CPF and CNPJ validation with nested address structures
 */

import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';
import { cpf, cnpj } from 'cpf-cnpj-validator';

// =============================================
// REUSABLE SCHEMAS
// =============================================

const genderSchema = z
  .enum(['MASCULINO', 'FEMININO', 'OUTRO'])
  .optional()
  .or(z.literal(''));

/**
 * Schema for address (single)
 */
export const addressSchema = z.object({
  id: z.number().optional(),
  cep: z.string().max(9).optional().or(z.literal('')),
  logradouro: z.string().max(255).optional().or(z.literal('')),
  numero: z.string().max(20).optional().or(z.literal('')),
  complemento: z.string().max(100).optional().or(z.literal('')),
  bairro: z.string().max(100).optional().or(z.literal('')),
  cidade: z.string().max(100).optional().or(z.literal('')),
  estado: z.string().max(2).optional().or(z.literal('')),
});

// =============================================
// COMMON FIELDS SCHEMA
// =============================================

const commonFieldsSchema = z.object({
  email: z.string().email('Email inválido').optional().or(z.literal('')),
  celular: z.string().max(16).optional().or(z.literal('')),
  telefone: z.string().max(15).optional().or(z.literal('')),
  observacoes: z.string().max(500).optional().or(z.literal('')),
});

// =============================================
// CUSTOMER PF (Individual) SCHEMA
// =============================================

export const customerPFSchema = z
  .object({
    // PF Specific Fields - Required
    nome: z
      .string({ required_error: 'Nome é obrigatório' })
      .min(3, 'Nome deve ter no mínimo 3 caracteres')
      .max(255),
    cpf: z
      .string()
      .min(14, 'CPF inválido')
      .max(14, 'CPF inválido')
      .optional()
      .or(z.literal('')),

    // PF Specific Fields - Optional
    rg: z.string().max(20).optional().or(z.literal('')),
    genero: genderSchema,
    data_nascimento: z.string().optional().or(z.literal('')),

    // Common fields
    ...commonFieldsSchema.shape,

    // Addresses (optional array)
    enderecos: z.array(addressSchema).optional().default([]),
  })
  .refine(
    (data) => {
      // CPF validation only if provided
      if (data.cpf && data.cpf.length === 14) {
        return cpf.isValid(data.cpf);
      }
      return true;
    },
    {
      message: 'CPF inválido',
      path: ['cpf'],
    }
  );

export const customerPFValidationSchema = toTypedSchema(customerPFSchema);
export type CustomerPFSchemaData = z.infer<typeof customerPFSchema>;

// =============================================
// CUSTOMER PJ (Company) SCHEMA
// =============================================

export const customerPJSchema = z
  .object({
    // PJ Specific Fields - Required
    razao_social: z
      .string({ required_error: 'Razão Social é obrigatória' })
      .min(3, 'Razão Social deve ter no mínimo 3 caracteres')
      .max(255),
    nome_fantasia: z.string().max(255).optional().or(z.literal('')),
    cnpj: z
      .string()
      .min(18, 'CNPJ inválido')
      .max(18, 'CNPJ inválido')
      .optional()
      .or(z.literal('')),

    // PJ Specific Fields - Optional
    ie: z.string().max(20).optional().or(z.literal('')),
    im: z.string().max(20).optional().or(z.literal('')),
    regime_tributario: z.string().max(100).optional().or(z.literal('')),
    responsavel: z.string().max(255).optional().or(z.literal('')),

    // Common fields
    ...commonFieldsSchema.shape,

    // Addresses (optional array)
    enderecos: z.array(addressSchema).optional().default([]),
  })
  .refine(
    (data) => {
      // CNPJ validation only if provided
      if (data.cnpj && data.cnpj.length === 18) {
        return cnpj.isValid(data.cnpj);
      }
      return true;
    },
    {
      message: 'CNPJ inválido',
      path: ['cnpj'],
    }
  );

export const customerPJValidationSchema = toTypedSchema(customerPJSchema);
export type CustomerPJSchemaData = z.infer<typeof customerPJSchema>;

// =============================================
// TYPE EXPORTS FOR FORM DATA
// =============================================

export type CustomerFormType = 'PF' | 'PJ';

export interface CustomerFormData {
  tipo: CustomerFormType;
  // PF fields
  nome: string;
  cpf: string;
  rg: string;
  genero: string;
  data_nascimento: string;
  // PJ fields
  razao_social: string;
  nome_fantasia: string;
  cnpj: string;
  ie: string;
  im: string;
  regime_tributario: string;
  responsavel: string;
  // Common fields
  email: string;
  celular: string;
  telefone: string;
  observacoes: string;
  // Addresses
  enderecos: AddressFormData[];
}

export interface AddressFormData {
  id?: number;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  estado: string;
}
