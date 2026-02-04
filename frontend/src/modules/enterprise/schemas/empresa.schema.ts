import { z } from 'zod';

// Schemas de validação

export const EnderecoSchema = z.object({
  id: z.number().int().positive().optional(),
  logradouro: z.string().min(1),
  numero: z.string().min(1),
  bairro: z.string().min(1),
  cidade: z.string().min(1),
  estado: z.string().length(2),
  cep: z.string().min(8).max(9),
  complemento: z.string().optional(),
  codigo_ibge: z.string().optional(),
});

export const FiscalSettingsSchema = z.object({
  id: z.number().int().positive().optional(),
  company_id: z.number().int().positive().optional(),
  ambiente_emissao: z.number().int().min(1).max(2).default(2),
  serie_nfe: z.number().int().nonnegative().default(1),
  ultimo_numero_nfe: z.number().int().nonnegative().default(0),
  serie_nfce: z.number().int().nonnegative().default(1),
  ultimo_numero_nfce: z.number().int().nonnegative().default(0),
  csc_token: z.string().optional(),
  csc_id: z.string().optional(),
  rps_serie: z.string().optional(),
  rps_ultimo_numero: z.number().int().nonnegative().optional(),
  prefeitura_login: z.string().optional(),
  prefeitura_senha: z.string().optional(),
  prefeitura_token_api: z.string().optional(),
  regime_tributacao_iss: z.number().int().min(1).max(6).optional(),
  tipo_certificado: z.enum(['ARQUIVO', 'WINDOWS']).default('ARQUIVO'),
  certificado_digital_path: z.string().optional(),
  certificado_validade: z.string().optional(),
  certificado_thumbprint: z.string().optional(),
});

export const EmpresaSchema = z.object({
  razao_social: z.string().min(1),
  nome_fantasia: z.string().optional(),
  is_cnpj: z.boolean().default(true),
  documento: z.string().min(11),
  inscricao_estadual: z.string().optional(),
  inscricao_municipal: z.string().optional(),
  regime_tributario: z.string().min(1).optional(),
  cnae_principal: z.string().optional(),
  email: z.string().email().or(z.literal('')).optional(),
  telefone: z.string().optional(),
  celular: z.string().optional(),
  url_logo: z.string().optional(),
  fiscal_settings: FiscalSettingsSchema.optional(),
  enderecos: z.array(EnderecoSchema).optional(),
}).passthrough();

export const WindowsCertificateSchema = z.object({
  thumbprint: z.string(),
  subject: z.string(),
  friendly_name: z.string(),
  issuer: z.string(),
  valid_until: z.string(),
  serial_number: z.string(),
});

export const ConnectionTestResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
});

// Tipos inferidos
export type EnderecoZod = z.infer<typeof EnderecoSchema>;
export type FiscalSettingsZod = z.infer<typeof FiscalSettingsSchema>;
export type EmpresaZod = z.infer<typeof EmpresaSchema>;
export type WindowsCertificateZod = z.infer<typeof WindowsCertificateSchema>;
export type ConnectionTestResponseZod = z.infer<typeof ConnectionTestResponseSchema>;

// Funções de validação
export function validateEmpresa(data: unknown): EmpresaZod | null {
  try {
    return EmpresaSchema.parse(data);
  } catch {
    return null;
  }
}

export function validateEndereco(data: unknown): EnderecoZod | null {
  try {
    return EnderecoSchema.parse(data);
  } catch {
    return null;
  }
}

export function validateFiscalSettings(data: unknown): FiscalSettingsZod | null {
  try {
    return FiscalSettingsSchema.parse(data);
  } catch {
    return null;
  }
}

// =============================================
// VeeValidate Integration
// =============================================

import { toTypedSchema } from '@vee-validate/zod';

/**
 * Schema de validação para VeeValidate
 * Converte Zod schema para formato compatível com VeeValidate
 */
export const empresaValidationSchema = toTypedSchema(EmpresaSchema);

/**
 * Type inference do schema
 */
export type EmpresaSchemaData = z.infer<typeof EmpresaSchema>;
