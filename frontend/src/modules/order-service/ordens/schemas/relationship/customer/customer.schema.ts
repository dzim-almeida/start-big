import z from 'zod';

import { CustomerTypeEnum } from './enums/customerEnum.type';
import { GenderTypeEnum } from './enums/genderEnum.type';
import { AddressReadSchema } from './relationship/address.schema';

const CustomerBaseSchema = z.object({
  id: z.number().int().positive(),
  tipo: CustomerTypeEnum,
  email: z.string().email().max(255, 'O email é obrigatório').optional().nullable(),
  telefone: z
    .string()
    .min(10, 'Digite um número de telefone válido')
    .max(10, 'Digite um número de telefone válido')
    .optional().nullable(),
  celular: z
    .string()
    .min(11, 'Digite um número de telefone válido')
    .max(11, 'Digite um número de telefone válido')
    .optional().nullable(),
  observacoes: z.string().max(500, 'A observação tem uma máximo de 500 caracteres').optional().nullable(),
  endereco: z.preprocess(
    (val) => {
      if (!Array.isArray(val)) return val;
      return val.length === 0 ? null : val[0];
    },
    AddressReadSchema.optional().nullable()
  ),
  ativo: z.boolean()
});

export const CustomerPFReadSchema = z.object({
  ...CustomerBaseSchema.shape,
  nome: z.string().max(255, 'O nome deve ter no máximo 255 caracteres'),
  cpf: z.string(),
  rg: z
    .string()
    .min(5, 'Um RG deve ter no mínimo 5 números')
    .max(20, 'RG tem no máximo 20 números')
    .optional().nullable(),
  genero: GenderTypeEnum.optional(),
  data_nascimento: z.coerce.date().optional().nullable()
});

export const CustomerPJReadSchema = z.object({
  ...CustomerBaseSchema.shape,
  razao_social: z.string().max(255, 'O nome deve ter no máximo 255 caracteres'),
  cnpj: z.string(),
  nome_fantasia: z.string().max(255, 'O nome fantasia deve ter no máximo 255 caracteres').optional(),
  ie: z
    .string()
    .min(9, 'Uma inscrição estadual deve ter no mínimo 9 números')
    .max(14, 'Inscrição estadual tem no máximo 14 números')
    .optional().nullable(),
  im: z
    .string()
    .min(9, 'Uma inscrição municipal deve ter no mínimo 9 números')
    .max(14, 'Uma inscrição municipal tem no máximo 14 números')
    .optional().nullable(),
  regime_tributario: z.string().optional().nullable(),
  responsavel: z.string().max(255, 'O nome do responsável deve ter no máximo 255 caracteres').optional().nullable()
});

export const CustomerUnionReadSchema = z.union([CustomerPFReadSchema, CustomerPJReadSchema])
export type CustomerUnionReadSchemaDataType = z.infer<typeof CustomerUnionReadSchema>
