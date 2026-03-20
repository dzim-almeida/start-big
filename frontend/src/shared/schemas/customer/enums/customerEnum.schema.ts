import z from 'zod';

export const CustomerTypeEnum = z.enum(['PF', 'PJ']);
export type CustomerTypeEnumDataType = z.infer<typeof CustomerTypeEnum>;
