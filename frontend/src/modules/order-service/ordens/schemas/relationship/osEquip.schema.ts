import z from 'zod';

import { OsEquipTypeEnum } from '../enums/osEnums.schema';

export const OsEquipCreateSchema = z.object({
  tipo_equipamento: OsEquipTypeEnum,
  marca: z
    .string({ required_error: 'A marca é obrigatória' })
    .max(100, 'A marca deve ter no máximo 100 caracteres'),
  modelo: z
    .string({ required_error: 'O modelo é obrigatório' })
    .max(100, 'O modelo deve ter no máximo 100 caracteres'),
  numero_serie: z
    .string({ required_error: 'O número de série é obrigatório' })
    .max(100, 'O número de série deve ter no máximo 100 caracteres'),
  imei: z
    .string({ required_error: 'O IMEI é obrigatório' })
    .max(20, 'O IMEI deve ter no máximo 20 caracteres'),
  cor: z.string().max(50, 'A cor deve ter no máximo 50 caracteres').optional(),
});

export const OsEquipReadSchema = z.object({
  ...OsEquipCreateSchema.shape,
  id: z.number().int().positive(),
  cliente_id: z.number().int().positive(),
  ativo: z.boolean(),
  data_criacao: z.string(),
  data_atualizacao: z.string(),
});

export const OsEquipUpdateSchema = z.object({
  tipo_equipamento: OsEquipTypeEnum.optional(),
  marca: z.string().max(255, 'A marca deve ter no máximo 255 caracteres').optional(),
  modelo: z.string().max(255, 'O modelo deve ter no máximo 255 caracteres').optional(),
  numero_serie: z
    .string()
    .max(255, 'O número de série deve ter no máximo 255 caracteres')
    .optional(),
  imei: z.string().max(255, 'O IMEI deve ter no máximo 255 caracteres').optional(),
  cor: z.string().max(255, 'A cor deve ter no máximo 255 caracteres').optional(),
  cliente_id: z.number().int().positive().optional(),
});

export type OsEquipCreateSchemaDataType = z.infer<typeof OsEquipCreateSchema>
export type OsEquipReadSchemaDataType = z.infer<typeof OsEquipReadSchema>
export type OsEquipUpdateSchemaDataType = z.infer<typeof OsEquipUpdateSchema>
