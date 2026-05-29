import z from 'zod';

export const OsStatusEnum = z.enum([
  'ABERTA',
  'EM_ANDAMENTO',
  'AGUARDANDO_PECAS',
  'AGUARDANDO_APROVACAO',
  'AGUARDANDO_RETIRADA',
  'FINALIZADA',
  'CANCELADA',
]);

export const OsPriorityEnum = z.enum(['BAIXA', 'NORMAL', 'ALTA', 'URGENTE']);

export const OsItemTypeEnum = z.enum(['PRODUTO', 'SERVICO']);

export const OsEquipTypeEnum = z.enum([
  'COMPUTADOR',
  'CELULAR',
  'TABLET',
  'IMPRESSORA',
  'MONITOR',
  'PRINTER',
  'SCANNER',
  'OUTROS',
]);

export const OsItemMeasureEnum = z.enum([
  'UN',
  'KG',
  'G',
  'L',
  'ML',
  'M',
  'CM',
  'M2',
  'M3',
  'H',
  'D',
  'MES',
  'OUTROS',
]);

export const OsCardsFlagEnum = z.enum([
  'MASTERCARD',
  'VISA',
  'ELO',
  'OUTROS',
])

export type OsStatusEnumDataType = z.infer<typeof OsStatusEnum>
export type OsPriorityEnumDataType = z.infer<typeof OsPriorityEnum>
export type OsItemTypeEnumDataType = z.infer<typeof OsItemTypeEnum>
export type OsEquipTypeEnumDataType = z.infer<typeof OsEquipTypeEnum>
export type OsItemMeasureEnumDataType = z.infer<typeof OsItemMeasureEnum>
export type OsCardsFlagEnumDataType = z.infer<typeof OsCardsFlagEnum>
