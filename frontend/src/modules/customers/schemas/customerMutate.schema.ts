import z from 'zod';

import { GenderTypeEnum } from '@/shared/schemas/customer/enums/genderEnum.schema';

// ── Endereço (Create / Update) ─────────────────────────────────────────────

const StateEnum = z.enum([
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES',
  'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR',
  'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
  'SP', 'SE', 'TO',
]);

const EnderecoCreateSchema = z.object({
  logradouro: z.string().max(255),
  numero: z.string().max(20),
  bairro: z.string().max(100),
  cidade: z.string().max(100),
  estado: StateEnum,
  cep: z.string().max(9),
  complemento: z.string().max(100).optional(),
});

const EnderecoUpdateSchema = z.object({
  id: z.number().int().positive().optional(),
  logradouro: z.string().max(255).optional(),
  numero: z.string().max(20).optional(),
  bairro: z.string().max(100).optional(),
  cidade: z.string().max(100).optional(),
  estado: StateEnum.optional(),
  cep: z.string().max(9).optional(),
  complemento: z.string().max(100).optional(),
});

export type EnderecoCreateDataType = z.infer<typeof EnderecoCreateSchema>;
export type EnderecoUpdateDataType = z.infer<typeof EnderecoUpdateSchema>;

// ── PF Create ──────────────────────────────────────────────────────────────

export const CustomerPFCreateSchema = z.object({
  nome: z.string().min(1).max(255),
  cpf: z.string().regex(/^\d{11}$/).optional(),
  rg: z.string().regex(/^\d{5,20}$/).optional(),
  genero: GenderTypeEnum.optional(),
  data_nascimento: z.string().optional(),
  email: z.string().email().max(255).optional(),
  celular: z.string().max(255).optional(),
  telefone: z.string().max(255).optional(),
  observacoes: z.string().max(500).optional(),
  endereco: z.array(EnderecoCreateSchema).optional(),
});

export type CustomerPFCreateDataType = z.infer<typeof CustomerPFCreateSchema>;

// ── PJ Create ──────────────────────────────────────────────────────────────

export const CustomerPJCreateSchema = z.object({
  razao_social: z.string().min(1).max(255),
  cnpj: z.string().regex(/^\d{14}$/).optional(),
  nome_fantasia: z.string().max(255).optional(),
  ie: z.string().regex(/^\d{9,14}$/).optional(),
  im: z.string().regex(/^\d{9,14}$/).optional(),
  regime_tributario: z.string().optional(),
  responsavel: z.string().max(255).optional(),
  email: z.string().email().max(255).optional(),
  celular: z.string().max(255).optional(),
  telefone: z.string().max(255).optional(),
  observacoes: z.string().max(500).optional(),
  endereco: z.array(EnderecoCreateSchema).optional(),
});

export type CustomerPJCreateDataType = z.infer<typeof CustomerPJCreateSchema>;

// ── PF Update ──────────────────────────────────────────────────────────────

export const CustomerPFUpdateSchema = z.object({
  tipo: z.literal('PF'),
  nome: z.string().max(255).optional(),
  cpf: z.string().regex(/^\d{11}$/).optional(),
  rg: z.string().regex(/^\d{5,20}$/).optional(),
  genero: GenderTypeEnum.optional(),
  data_nascimento: z.string().optional(),
  email: z.string().email().max(255).optional(),
  celular: z.string().max(255).optional(),
  telefone: z.string().max(255).optional(),
  observacoes: z.string().max(500).optional(),
  endereco: z.array(EnderecoUpdateSchema).optional(),
});

export type CustomerPFUpdateDataType = z.infer<typeof CustomerPFUpdateSchema>;

// ── PJ Update ──────────────────────────────────────────────────────────────

export const CustomerPJUpdateSchema = z.object({
  tipo: z.literal('PJ'),
  razao_social: z.string().max(255).optional(),
  cnpj: z.string().regex(/^\d{14}$/).optional(),
  nome_fantasia: z.string().max(255).optional(),
  ie: z.string().regex(/^\d{9,14}$/).optional(),
  im: z.string().regex(/^\d{9,14}$/).optional(),
  regime_tributario: z.string().optional(),
  responsavel: z.string().max(255).optional(),
  email: z.string().email().max(255).optional(),
  celular: z.string().max(255).optional(),
  telefone: z.string().max(255).optional(),
  observacoes: z.string().max(500).optional(),
  endereco: z.array(EnderecoUpdateSchema).optional(),
});

export type CustomerPJUpdateDataType = z.infer<typeof CustomerPJUpdateSchema>;

// ── Union Update (discriminated) ───────────────────────────────────────────

export const CustomerUpdateSchema = z.discriminatedUnion('tipo', [
  CustomerPFUpdateSchema,
  CustomerPJUpdateSchema,
]);

export type CustomerUpdateDataType = z.infer<typeof CustomerUpdateSchema>;
