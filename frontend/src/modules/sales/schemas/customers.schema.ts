import z from 'zod';

import { maskCpfCnpj } from '@/shared/utils/mask.utils';

const CustomerAddressSchema = z.object({
  logradouro: z.string(),
  numero: z.string(),
  bairro: z.string(),
  cidade: z.string(),
  estado: z.string(),
  cep: z.string(),
  complemento: z.string().nullable().optional(),
});

const CustomerPFSimpleReadSchema = z.object({
  id: z.number(),
  tipo: z.literal('PF'),
  nome: z.string(),
  cpf: z.string().transform((cpf) => maskCpfCnpj(cpf)).nullable(),
  telefone: z.string().nullable().optional(),
  celular: z.string().nullable().optional(),
  endereco: z.array(CustomerAddressSchema).optional(),
});

const CustomerPJSimpleReadSchema = z.object({
  id: z.number(),
  tipo: z.literal('PJ'),
  razao_social: z.string(),
  cnpj: z.string().transform((cnpj) => maskCpfCnpj(cnpj)).nullable(),
  telefone: z.string().nullable().optional(),
  celular: z.string().nullable().optional(),
  endereco: z.array(CustomerAddressSchema).optional(),
});

export const CustomerDiscriminatedSchema = z.discriminatedUnion('tipo', [
  CustomerPFSimpleReadSchema,
  CustomerPJSimpleReadSchema,
]);

export const CustomerDiscriminatedSimpleReadSchema = z.discriminatedUnion('tipo', [
  CustomerPFSimpleReadSchema,
  CustomerPJSimpleReadSchema,
]).array();

export type CustomerSimpleRead = z.infer<typeof CustomerDiscriminatedSimpleReadSchema>;
