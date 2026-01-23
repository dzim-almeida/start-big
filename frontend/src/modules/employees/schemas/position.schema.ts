/**
 * @fileoverview Zod validation schema for cargo (position) form
 */

import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';

export const positionSchema = z.object({
  nome: z
    .string({ required_error: 'Nome do cargo e obrigatorio' })
    .min(3, 'Nome deve ter no minimo 3 caracteres')
    .max(50, 'Nome deve ter no maximo 50 caracteres'),
  permissoes: z.record(z.boolean()).optional().default({}),
});

export const positionValidationSchema = toTypedSchema(positionSchema);
export type PositionSchemaData = z.infer<typeof positionSchema>;
