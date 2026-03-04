import z from 'zod';
import { cpf, cnpj } from 'cpf-cnpj-validator';

import { CustomerTypeEnum } from './enums/customerEnum.type';
import { GenderTypeEnum } from './enums/genderEnum.type';
import { AddressReadSchema } from './relationship/address.schema';

const CustomerBaseSchema = z.object({
  id: z.number().int().positive(),
  tipo: CustomerTypeEnum,
  email: z.string().email().max(255, 'O email é obrigatório').optional(),
  telefone: z
    .string()
    .min(10, 'Digite um número de telefone válido')
    .max(10, 'Digite um número de telefone válido')
    .optional(),
  celular: z
    .string()
    .min(11, 'Digite um número de telefone válido')
    .max(11, 'Digite um número de telefone válido')
    .optional(),
  observacoes: z.string().max(500, 'A observação tem uma máximo de 500 caracteres').optional(),
  endereco: AddressReadSchema.optional(),
  ativo: z.boolean()
});

export const CustomerPFReadSchema = z
  .object({
    ...CustomerBaseSchema.shape,
    nome: z.string().max(255, 'O nome deve ter no máximo 255 caracteres'),
    cpf: z.string(),
    rg: z
      .string()
      .min(5, 'Um RG deve ter no mínimo 5 números')
      .max(20, 'RG tem no máximo 20 números')
      .optional(),
    genero: GenderTypeEnum.optional(),
    data_nascimento: z.date().optional()
  })
  .refine((data) => cpf.isValid(data.cpf), {
    message: 'O CPF deve ser um documento válido',
    path: ['cpf'],
  });

  export const CustomerPJReadSchema = z
  .object({
    ...CustomerBaseSchema.shape,
    razao_social: z.string().max(255, 'O nome deve ter no máximo 255 caracteres'),
    cnpj: z.string(),
    nome_fantasia: z.string().max(255, 'O nome fantasia deve ter no máximo 255 caracteres').optional(),
    ie: z
      .string()
      .min(9, 'Uma inscrição estadual deve ter no mínimo 9 números')
      .max(14, 'Inscrição estadual tem no máximo 14 números')
      .optional(),
    im: z
      .string()
      .min(9, 'Uma inscrição municipal deve ter no mínimo 9 números')
      .max(14, 'Uma inscrição municipal tem no máximo 14 números')
      .optional(),
    regime_tributario: z.string().optional(),
    responsavel: z.string().max(255, 'O nome do responsável deve ter no máximo 255 caracteres').optional()
  })
  .refine((data) => cnpj.isValid(data.cnpj), {
    message: 'O CNPJ deve ser um documento válido',
    path: ['cnpj'],
  });

  export const CustomerUnionReadSchema = z.union([CustomerPFReadSchema, CustomerPJReadSchema])
  export type CustomerUnionReadSchemaDataType = z.infer<typeof CustomerUnionReadSchema>
