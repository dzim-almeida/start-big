import { z } from 'zod';

export const ExtratoServicoItemSchema = z.object({
  numero_os: z.string(),
  data_finalizacao: z.string(),
  objeto: z.string().nullable().optional(),
  cliente: z.string().nullable().optional(),
  servico: z.string(),
  quantidade: z.number(),
  valor_total: z.number(),
  /** Custo da peça embutida no preço do serviço. Interno: nunca sai na via do cliente. */
  custo: z.number().default(0),
  /** valor_total − custo. É a base da comissão de serviço. */
  mao_de_obra: z.number().default(0),
  /** Parte da comissão de serviço desta linha. */
  comissao: z.number().default(0),
});

export const ExtratoVendaItemSchema = z.object({
  venda_id: z.number(),
  numero: z.string(),
  data: z.string(),
  cliente: z.string().nullable().optional(),
  valor_total: z.number(),
  /** Margem: total − juros da operadora − custo das mercadorias. Pode ser negativa. */
  base: z.number(),
  comissao: z.number().default(0),
});

export const RelatorioExtratoFuncionarioSchema = z.object({
  inicio: z.string(),
  fim: z.string(),
  funcionario_id: z.number(),
  funcionario_nome: z.string(),
  /** OS DISTINTAS, não linhas: três serviços numa OS contam 1. */
  qtd_os: z.number(),
  qtd_servicos: z.number(),
  valor_total: z.number(),
  /** Soma da mão de obra — o que a comissão de serviço realmente paga. */
  total_mao_de_obra: z.number().default(0),
  itens: z.array(ExtratoServicoItemSchema),
  // Vendas e comissão. `.default` para backend mais antigo, que só mandava serviços.
  qtd_vendas: z.number().default(0),
  total_vendas: z.number().default(0),
  vendas: z.array(ExtratoVendaItemSchema).default([]),
  base_vendas: z.number().default(0),
  base_servicos: z.number().default(0),
  /** Basis points (500 = 5,00%). */
  percentual_venda: z.number().nullable().default(null),
  percentual_servico: z.number().nullable().default(null),
  comissao_vendas: z.number().default(0),
  comissao_servico: z.number().default(0),
  comissao_total: z.number().default(0),
  comissao_modo: z.string().default('direto'),
  meta_mensal: z.number().nullable().default(null),
  meta_atingida_percentual: z.number().nullable().default(null),
  comissao_liberada: z.boolean().default(true),
});

export type RelatorioExtratoFuncionario = z.infer<typeof RelatorioExtratoFuncionarioSchema>;
export type ExtratoServicoItem = z.infer<typeof ExtratoServicoItemSchema>;
export type ExtratoVendaItem = z.infer<typeof ExtratoVendaItemSchema>;
