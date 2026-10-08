import { z } from 'zod';

/** R1 = preço de embalagem nas avulsas · R2 = a partir de N · R3 = leve X, pague Y. */
export const RegraPrecoCodigoSchema = z.enum(['R1', 'R2', 'R3']);

export const RegraPrecoResumoSchema = z.object({
  regra: RegraPrecoCodigoSchema,
  qtd_vendas: z.number(),
  unidades: z.number(),
  faturamento: z.number(),
  abatimento: z.number(),
});

export const RegraPrecoProdutoItemSchema = z.object({
  regra: RegraPrecoCodigoSchema,
  produto_id: z.number(),
  nome: z.string(),
  sku: z.string().nullable(),
  qtd_vendas: z.number(),
  unidades: z.number(),
  faturamento: z.number(),
  abatimento: z.number(),
});

export const RelatorioRegrasPrecoSchema = z.object({
  inicio: z.string(),
  fim: z.string(),
  qtd_vendas: z.number(),
  faturamento: z.number(),
  abatimento: z.number(),
  por_regra: z.array(RegraPrecoResumoSchema),
  por_produto: z.array(RegraPrecoProdutoItemSchema),
});

export type RegraPrecoCodigo = z.infer<typeof RegraPrecoCodigoSchema>;
export type RelatorioRegrasPreco = z.infer<typeof RelatorioRegrasPrecoSchema>;
export type RegraPrecoResumo = z.infer<typeof RegraPrecoResumoSchema>;
export type RegraPrecoProdutoItem = z.infer<typeof RegraPrecoProdutoItemSchema>;
