import z from 'zod';

const LinksBaseSchema = z.object({
  next: z.string().url().nullable(),
  prev: z.string().url().nullable(),
});

export const PaginationBaseSchema = z.object({
  total_items: z.number().int().nonnegative(),
  page: z.number().int().min(1, 'A página não pode ser menor que 1'),
  limit: z.number().int().min(20, 'O limite mínimo é 20 itens'),
  total_pages: z.number().int().nonnegative(),
  links: LinksBaseSchema.optional(),
});