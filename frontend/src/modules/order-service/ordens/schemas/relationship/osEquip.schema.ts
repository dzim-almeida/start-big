import z from 'zod';

import { OsEquipTypeEnum } from '../enums/osEnums.schema';

/**
 * Regex de placa (Mercosul ABC1D23 ou antiga ABC1234), já normalizada
 * (maiúsculas, sem hífen). Espelha app/core/segmentos.PLACA_REGEX do backend.
 * Usada como validação leve de UX no segmento de oficina; o backend é a fonte da verdade.
 */
export const PLACA_REGEX = /^(?:[A-Z]{3}\d{4}|[A-Z]{3}\d[A-Z]\d{2})$/;

export const OsEquipCreateSchema = z.object({
  // Opcional: oficina não usa o enum de TI (moto seria outro segmento).
  tipo_equipamento: OsEquipTypeEnum.optional(),
  marca: z
    .string({ required_error: 'A marca é obrigatória' })
    .trim()
    .min(1, 'A marca é obrigatória')
    .max(100, 'A marca deve ter no máximo 100 caracteres'),
  modelo: z
    .string({ required_error: 'O modelo é obrigatório' })
    .trim()
    .min(1, 'O modelo é obrigatório')
    .max(100, 'O modelo deve ter no máximo 100 caracteres'),
  numero_serie: z
    .string({ required_error: 'O número de série é obrigatório' })
    .trim()
    .min(1, 'O número de série é obrigatório')
    .max(100, 'O número de série deve ter no máximo 100 caracteres'),
  imei: z
    .string()
    .max(20, 'O IMEI deve ter no máximo 20 caracteres')
    .optional()
    .default(''),
  cor: z.string().max(50, 'A cor deve ter no máximo 50 caracteres').optional(),
  // Lembrete de revisão (oficina) — colunas do objeto no backend.
  proxima_revisao_data: z.string().optional().nullable(),
  proxima_revisao_km: z.number().int().min(0).optional().nullable(),
  // Campos dinâmicos do objeto por segmento (ex: oficina → chassi, ano).
  dados_adicionais: z.record(z.any()).optional().default({}),
});

export const OsEquipReadSchema = z.object({
  ...OsEquipCreateSchema.shape,
  // Na resposta, tipo_equipamento é livre por segmento (ex: 'Veículo', 'COMPUTADOR').
  tipo_equipamento: z.string().optional().nullable(),
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
    .string({ required_error: 'O número de série é obrigatório' })
    .max(255, 'O número de série deve ter no máximo 255 caracteres')
    .optional(),
  imei: z.string({ required_error: 'O IMEI é obrigatório' }).max(255, 'O IMEI deve ter no máximo 255 caracteres').optional(),
  cor: z.string().max(255, 'A cor deve ter no máximo 255 caracteres').optional(),
  cliente_id: z.number().int().positive().optional(),
  proxima_revisao_data: z.string().optional().nullable(),
  proxima_revisao_km: z.number().int().min(0).optional().nullable(),
  dados_adicionais: z.record(z.any()).optional(),
});

export type OsEquipCreateSchemaDataType = z.infer<typeof OsEquipCreateSchema>
export type OsEquipReadSchemaDataType = z.infer<typeof OsEquipReadSchema>
export type OsEquipUpdateSchemaDataType = z.infer<typeof OsEquipUpdateSchema>
