/**
 * @fileoverview Schema de validação Zod para formulário de login
 * @description Define as regras de validação para os campos de email e senha
 * utilizando Zod com integração ao Vee-Validate.
 */

import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';

/**
 * Schema Zod para validação do formulário de login
 */
export const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .toLowerCase()
    .email('Digite um email válido'),

  senha: z
    .string()
    .trim()
});

/**
 * Schema tipado para uso com Vee-Validate
 */
export const loginValidationSchema = toTypedSchema(loginSchema);

/**
 * Tipo inferido do schema de login
 */
export type LoginFormData = z.infer<typeof loginSchema>;
