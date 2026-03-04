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

export type OsStatusEnumDataType = z.infer<typeof OsStatusEnum>

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
