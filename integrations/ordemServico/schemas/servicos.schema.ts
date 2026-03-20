import { z } from 'zod';

export const ServicoReadSchema = z.object({
  id: z.number().int().positive(),
  descricao: z.string().min(1, 'Descrição é obrigatória'),
  valor: z.number().int().nonnegative(),
  ativo: z.boolean(),
});

export const ServicoCreateSchema = z.object({
  descricao: z.string().min(1, 'Descrição é obrigatória').max(255),
  valor: z.number().int().nonnegative(),
});

export const ServicoUpdateSchema = z.object({
  descricao: z.string().min(1).max(255).optional(),
  valor: z.number().int().nonnegative().optional(),
});

export const PaginatedServicosSchema = z.object({
  items: z.array(ServicoReadSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  limit: z.number().int().positive(),
  pages: z.number().int().nonnegative(),
});

export type ServicoReadZod = z.infer<typeof ServicoReadSchema>;
export type ServicoCreateZod = z.infer<typeof ServicoCreateSchema>;
export type ServicoUpdateZod = z.infer<typeof ServicoUpdateSchema>;
export type PaginatedServicosZod = z.infer<typeof PaginatedServicosSchema>;
