import z from 'zod';

import { CustomerTypeEnum } from './enums/customerEnum.type';
import { GenderTypeEnum } from './enums/genderEnum.type';
import { AddressReadSchema } from './relationship/address.schema';

const CustomerBaseSchema = z.object({
  id: z.number().int().positive(),
  tipo: CustomerTypeEnum,
  email: z.string().nullish(),
  telefone: z.string().nullish(),
  celular: z.string().nullish(),
  observacoes: z.string().nullish(),
  endereco: z.union([AddressReadSchema, z.array(AddressReadSchema)]).nullish(),
  ativo: z.boolean(),
});

export const CustomerPFReadSchema = z.object({
  ...CustomerBaseSchema.shape,
  nome: z.string(),
  cpf: z.string().nullish(),
  rg: z.string().nullish(),
  genero: GenderTypeEnum.nullish(),
  data_nascimento: z.string().nullish(),
});

export const CustomerPJReadSchema = z.object({
  ...CustomerBaseSchema.shape,
  razao_social: z.string().nullish(),
  cnpj: z.string().nullish(),
  nome_fantasia: z.string().nullish(),
  ie: z.string().nullish(),
  im: z.string().nullish(),
  regime_tributario: z.string().nullish(),
  responsavel: z.string().nullish(),
  nome: z.string().nullish(),
});

export const CustomerUnionReadSchema = z.union([CustomerPFReadSchema, CustomerPJReadSchema]);
export type CustomerUnionReadSchemaDataType = z.infer<typeof CustomerUnionReadSchema>;
