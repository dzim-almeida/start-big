import { z } from 'zod';

export const AtualizarContaSchema = z.object({
  nome: z.string().min(2, 'Nome deve ter pelo menos 2 caracteres').max(255),
  email: z.string().email('E-mail inválido').max(255),
});

export const AlterarSenhaSchema = z
  .object({
    senha_atual: z.string().min(8, 'Senha deve ter pelo menos 8 caracteres'),
    nova_senha: z.string().min(8, 'Nova senha deve ter pelo menos 8 caracteres').max(72),
    confirmar_nova_senha: z.string(),
  })
  .refine((data) => data.nova_senha === data.confirmar_nova_senha, {
    message: 'As senhas não coincidem',
    path: ['confirmar_nova_senha'],
  });

export type AtualizarContaForm = z.infer<typeof AtualizarContaSchema>;
export type AlterarSenhaForm = z.infer<typeof AlterarSenhaSchema>;
