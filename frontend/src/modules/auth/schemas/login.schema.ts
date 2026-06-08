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
    .string({ required_error: 'E-mail é obrigatório' })
    .trim()
    .toLowerCase()
    .email('Digite um e-mail válido'),

  senha: z
    .string({ required_error: 'Senha é obrigatória' })
    .trim()
    .min(1, 'Senha é obrigatória')
});

/**
 * Schema tipado para uso com Vee-Validate
 */
export const loginValidationSchema = toTypedSchema(loginSchema);

/**
 * Tipo inferido do schema de login
 */
export type LoginFormData = z.infer<typeof loginSchema>;
