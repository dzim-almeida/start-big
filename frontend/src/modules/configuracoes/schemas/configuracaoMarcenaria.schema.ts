/**
 * Contrato de GET/PUT /configuracoes/marcenaria (Spec 04A §5, Spec 04B §5).
 *
 * A resposta tem DOIS formatos, decididos por `inclui_custos`: quem não tem a
 * permissão `view_custos_marcenaria` recebe só a parte sem custo, e as chaves
 * de custo nem vêm (não chegam como null). O zod confere isso na chegada.
 *
 * Percentuais em basis points (9000 = 90,00%) e dinheiro em centavos (PR4).
 */
import { z } from 'zod';

/** Como o RT do arquiteto entra no orçamento (SPEC-00, C5c). */
export const rtModoSchema = z.enum(['MARGEM', 'PRECO']);

/** O que qualquer usuário logado recebe. */
const base = z.object({
  validade_dias: z.number().int(),
  prazo_entrega_dias: z.number().int(),
  etapas_producao: z.array(z.string()),
  checklist_vistoria: z.array(z.string()),
});

/** Resposta do GET: sem custo (`inclui_custos: false`) ou completa (`true`). */
export const configuracaoMarcenariaSchema = z.discriminatedUnion('inclui_custos', [
  base.extend({ inclui_custos: z.literal(false) }),
  base.extend({
    inclui_custos: z.literal(true),
    markup_padrao_bp: z.number().int(),
    perda_padrao_bp: z.number().int(),
    custo_hora_centavos: z.number().int(),
    rt_padrao_bp: z.number().int(),
    rt_modo: rtModoSchema,
    /** Dias depois de finalizar a OS para a conta do RT vencer (Spec 09A §5 / 09B D11). */
    rt_vencimento_dias: z.number().int(),
  }),
]);

export type ConfiguracaoMarcenaria = z.infer<typeof configuracaoMarcenariaSchema>;
export type RtModo = z.infer<typeof rtModoSchema>;

/** Corpo do PUT: parcial, só os campos enviados mudam. */
export interface ConfiguracaoMarcenariaUpdate {
  markup_padrao_bp?: number;
  perda_padrao_bp?: number;
  custo_hora_centavos?: number;
  rt_padrao_bp?: number;
  rt_modo?: RtModo;
  rt_vencimento_dias?: number;
  validade_dias?: number;
  prazo_entrega_dias?: number;
  etapas_producao?: string[];
  checklist_vistoria?: string[];
}
