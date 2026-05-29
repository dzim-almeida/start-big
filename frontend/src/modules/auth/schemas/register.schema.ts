/**
 * @fileoverview Schema de validação Zod para formulário de registro de usuario
 * @description Define as regras de validação para os campos de nome, email, senha e confirmar senha
 * utilizando Zod com integração ao Vee-Validate.
 */

import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';

/**
 * Schema Zod para validação do formulário de login
 */
export const registerSchema = z
  .object({
    nome: z
      .string({ required_error: 'O nome é obrigatório' })
      .trim()
      .min(3, 'O nome deve ter no mínimo 3 caracteres')
      .max(100, 'O nome deve ter no máximo 100 caracteres'),

    email: z
      .string({ required_error: 'O e-mail é obrigatório' })
      .trim()
      .toLowerCase()
      .email('Digite um email válido')
      .max(255, 'O e-mail deve ter no máximo 255 caracteres'),

    senha: z
      .string({ required_error: 'A senha é obrigatória' })
      .min(8, 'A senha deve ter no mínimo 8 caracteres')
      .max(72, 'A senha deve ter no mínimo 72 caracteres')
      .regex(/[A-Z]/, 'A senha deve conter ao menos uma letra maiúscula')
      .regex(/[0-9]/, 'A senha deve conter ao menos um número'),

    confirmarSenha: z.string({ required_error: 'A confirmação de senha é obrigatória' }),
  })
  .refine((data) => data.senha === data.confirmarSenha, {
    message: 'As senhas não coincidem',
    path: ['confirmarSenha'],
  });

/**
 * Schema tipado para uso com Vee-Validate
 */
export const registerValidationSchema = toTypedSchema(registerSchema);

/**
 * Tipo inferido do schema de login
 */
export type RegisterFormData = z.infer<typeof registerSchema>;

