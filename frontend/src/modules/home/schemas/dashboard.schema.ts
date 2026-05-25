import { z } from 'zod';

// ===========================================================================
// Stats Cards
// ===========================================================================

export const DashboardStatsSchema = z.object({
  vendas_total: z.number(),
  vendas_total_variacao: z.number(),
  os_count: z.number(),
  os_count_variacao: z.number(),
  novos_clientes: z.number(),
  novos_clientes_variacao: z.number(),
  ticket_medio: z.number(),
  ticket_medio_variacao: z.number(),
});

export type DashboardStatsData = z.infer<typeof DashboardStatsSchema>;

// ===========================================================================
// OS Vencendo
// ===========================================================================

export const OSVencendoItemSchema = z.object({
  numero_os: z.string(),
  cliente_nome: z.string(),
  defeito_relatado: z.string(),
  data_previsao: z.string(),
  urgencia: z.enum(['vermelho', 'amarelo', 'verde']),
});

export type OSVencendoItemData = z.infer<typeof OSVencendoItemSchema>;

export const OSVencendoResponseSchema = z.object({
  items: z.array(OSVencendoItemSchema),
});

export type OSVencendoResponseData = z.infer<typeof OSVencendoResponseSchema>;

// ===========================================================================
// Estoque Baixo
// ===========================================================================

export const EstoqueBaixoItemSchema = z.object({
  produto_id: z.number(),
  nome: z.string(),
  quantidade: z.number(),
  quantidade_minima: z.number().nullable(),
  status: z.enum(['zerado', 'baixo']),
});

export type EstoqueBaixoItemData = z.infer<typeof EstoqueBaixoItemSchema>;

export const EstoqueBaixoResponseSchema = z.object({
  items: z.array(EstoqueBaixoItemSchema),
});

export type EstoqueBaixoResponseData = z.infer<typeof EstoqueBaixoResponseSchema>;

// ===========================================================================
// Ultimas Vendas
// ===========================================================================

export const UltimaVendaItemSchema = z.object({
  id: z.number(),
  numero_venda: z.number().nullable(),
  cliente_nome: z.string().nullable(),
  total: z.number(),
  status: z.string(),
  criado_em: z.string(),
});

export type UltimaVendaItemData = z.infer<typeof UltimaVendaItemSchema>;

export const UltimasVendasResponseSchema = z.object({
  items: z.array(UltimaVendaItemSchema),
});

export type UltimasVendasResponseData = z.infer<typeof UltimasVendasResponseSchema>;
