import { z } from 'zod';

/** Um cargo da loja e se ele vê as comissões (e o extrato) de toda a equipe. */
export const AcessoComissoesCargoSchema = z.object({
  id: z.number(),
  nome: z.string(),
  liberado: z.boolean(),
  /** Sem acesso à tela de Relatórios, a liberação não aparece para ninguém do cargo. */
  abre_relatorios: z.boolean(),
});

export const AcessoComissoesSchema = z.object({
  cargos: z.array(AcessoComissoesCargoSchema).default([]),
});

export type AcessoComissoesCargo = z.infer<typeof AcessoComissoesCargoSchema>;
export type AcessoComissoes = z.infer<typeof AcessoComissoesSchema>;
