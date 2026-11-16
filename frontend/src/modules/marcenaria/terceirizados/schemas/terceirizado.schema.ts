/**
 * @fileoverview O que a API dos terceirizados devolve (Spec 11A §6), conferido
 * pelo zod. O valor orçado só vem para quem vê custos (11A D13).
 */
import { z } from 'zod';

/** As quatro situações (11A D1). */
export const SITUACOES = ['A_PEDIR', 'ENVIADO', 'RECEBIDO', 'CONFERIDO'] as const;
export type SituacaoTerceirizado = (typeof SITUACOES)[number];

export const movelTerceirizadoSchema = z.object({
  movel_id: z.number(),
  nome: z.string(),
  ambiente: z.string(),
  quantidade: z.number(),
  medidas: z.object({
    largura_mm: z.number().nullable(), altura_mm: z.number().nullable(), profundidade_mm: z.number().nullable(),
  }),
  central: z.object({ id: z.number(), nome: z.string(), telefone: z.string().nullable() }).nullable(),
  situacao: z.enum(SITUACOES),
  atrasado: z.boolean(),
  previsao: z.string().nullable(),                         // data pura "2026-10-20"
  // Com o Compras: o pedido de serviço; sem: o número anotado à mão; ou nada.
  pedido: z.union([
    z.object({ origem: z.literal('COMPRAS'), id: z.number(), codigo: z.string(), situacao: z.string() }),
    z.object({ origem: z.literal('MANUAL'), numero: z.string().nullable() }),
  ]).nullable(),
  enviado_em: z.string().nullable(),
  recebido_em: z.string().nullable(),
  conferido_em: z.string().nullable(),
  problema: z.string().nullable(),
  valor_orcado_centavos: z.number().int().optional(),     // só com view_custos_marcenaria
});
export type MovelTerceirizado = z.infer<typeof movelTerceirizadoSchema>;

/** A sugestão de status da OS (12A D16): vem no conferir e no voltar. */
export const sugestaoStatusSchema = z.object({ de: z.string(), para: z.string(), rotulo: z.string() }).nullable();
export type SugestaoStatus = z.infer<typeof sugestaoStatusSchema>;

export const terceirizadosSchema = z.object({
  os: z.object({ numero_os: z.string(), status: z.string(), editavel: z.boolean() }),
  modo_compras: z.boolean(),                               // o módulo Compras está contratado
  moveis: z.array(movelTerceirizadoSchema),
  sugestao_status: sugestaoStatusSchema.optional(),
});
export type TerceirizadosDaOS = z.infer<typeof terceirizadosSchema>;

/** POST /pedir: o pedido criado no Compras e a seção atualizada. */
export const pedirRespostaSchema = z.object({
  pedido: z.object({
    id: z.number(), codigo: z.string(), situacao: z.string(), fornecedor_nome: z.string(),
    valor_total_centavos: z.number().int().optional(),     // só para quem vê custo de compra
  }),
  terceirizados: terceirizadosSchema,
});
export type PedirResposta = z.infer<typeof pedirRespostaSchema>;

/** GET /terceirizados: a lista geral das OS abertas (11A D17). */
export const listaTerceirizadosSchema = z.object({
  itens: z.array(movelTerceirizadoSchema.extend({
    numero_os: z.string(),
    cliente: z.string().nullable(),
    orcamento_codigo: z.string(),
  })),
});
export type ItemListaTerceirizados = z.infer<typeof listaTerceirizadosSchema>['itens'][number];
