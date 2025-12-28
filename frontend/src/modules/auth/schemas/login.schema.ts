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
    .string({ required_error: 'O e-mail é obrigatório' })
    .trim()
    .toLowerCase()
    .email('Digite um email válido')
    .max(255, 'O e-mail deve ter no máximo 255 caracteres'),

  senha: z
    .string({ required_error: 'A senha é obrigatória' })
    .trim()
    .min(8, 'A senha deve ter no mínimo 8 caracteres')
    .max(72, 'A senha deve ter no mínimo 72 caracteres'),
});

/**
 * Schema tipado para uso com Vee-Validate
 */
export const loginValidationSchema = toTypedSchema(loginSchema);

/**
 * Tipo inferido do schema de login
 */
export type LoginFormData = z.infer<typeof loginSchema>;
