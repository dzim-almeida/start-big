import { z } from 'zod';

export const ReceitaGrupoItemSchema = z.object({
  icms_st: z.boolean(),
  monofasico: z.boolean(),
  valor: z.number(),
});

export const ProdutoSemClassificacaoItemSchema = z.object({
  produto_id: z.number().nullable(),
  nome: z.string(),
  valor: z.number(),
  motivo: z.string(),
});

export const RelatorioContadorSchema = z.object({
  inicio: z.string(),
  fim: z.string(),
  crt: z.number().nullable(),
  receita_total: z.number(),
  mercadoria: z.array(ReceitaGrupoItemSchema),
  mercadoria_sem_classificacao: z.number(),
  servicos: z.number(),
  frete_e_juros: z.number(),
  faturamento_vendas: z.number(),
  faturamento_os: z.number(),
  produtos_sem_classificacao: z.array(ProdutoSemClassificacaoItemSchema),
});

export type RelatorioContador = z.infer<typeof RelatorioContadorSchema>;
export type ReceitaGrupoItem = z.infer<typeof ReceitaGrupoItemSchema>;
