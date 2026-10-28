/**
 * @fileoverview Contrato de GET /marcenaria/os/{numero_os}/faturamento e da
 * prévia da nota (docs/marcenaria-faturamento-plano.md, F3).
 *
 * Cada móvel aprovado da OS: se está pronto, se está no estoque como produto
 * acabado (dá para faturar) ou em que nota já saiu.
 */
import { z } from 'zod';

const documentoSchema = z.object({
  id: z.number(),
  numero: z.number().nullable(),
  serie: z.number().nullable(),
  status: z.string(),
  chave_acesso: z.string().nullable(),
  valor_total: z.number().nullable(),
  data_emissao: z.string().nullable(),
  mensagem: z.string().nullable(),
  /** Entrega futura (F4): SIMPLES_FATURAMENTO ou REMESSA_ENTREGA_FUTURA. */
  papel: z.string().nullable().optional(),
});
export type DocumentoDoMovel = z.infer<typeof documentoSchema>;

export const movelFaturamentoSchema = z.object({
  movel_id: z.number(),
  nome: z.string(),
  ambiente: z.string(),
  quantidade: z.number(),
  pronto: z.boolean(),
  situacao: z.enum(['NO_ESTOQUE', 'FATURADO']).nullable(),
  pode_faturar: z.boolean(),
  documento: documentoSchema.nullable(),
  /** Entrega futura (F4): a nota de simples faturamento que cobre o móvel. */
  simples_faturamento: documentoSchema.nullable().optional(),
});
export type MovelFaturamento = z.infer<typeof movelFaturamentoSchema>;

export const faturamentoDaOSSchema = z.object({
  numero_os: z.string(),
  faturamento_modo: z.enum(['DESLIGADO', 'NOTA_NA_ENTREGA', 'ENTREGA_FUTURA']),
  instalacao_modo: z.enum(['EMBUTIDA', 'FORA', 'NFSE']),
  moveis: z.array(movelFaturamentoSchema),
  notas: z.array(documentoSchema),
  /** Entrega futura (F4): algum móvel ainda sem simples faturamento (o aditivo ganha o seu). */
  falta_simples_faturamento: z.boolean().default(false),
  /** Instalação em NFS-e (G5): null fora desse modo (e num backend anterior). */
  nfse_instalacao: z.object({
    valor: z.number(),
    documento: z.object({
      id: z.number(),
      status: z.string(),
      numero: z.number().nullable(),
      codigo_verificacao: z.string().nullable(),
      url_consulta: z.string().nullable(),
      mensagem: z.string().nullable(),
    }).nullable(),
  }).nullable().default(null),
});
export type FaturamentoDaOS = z.infer<typeof faturamentoDaOSSchema>;

/** A prévia da nota: o que vai para a SEFAZ (sem reservar número). */
export const previaNotaSchema = z.object({
  natureza_operacao: z.string().nullable().optional(),
  itens: z.array(z.object({
    descricao: z.string(),
    quantidade_comercial: z.number(),
    valor_bruto: z.number(),
    cfop: z.string().nullable().optional(),
    ncm: z.string().nullable().optional(),
  }).passthrough()),
  totais: z.object({ valor_total: z.number() }).passthrough(),
  formas_pagamento: z.array(z.object({ forma_pagamento: z.string(), valor_pagamento: z.number() }).passthrough()),
  avisos: z.array(z.string()).default([]),
});
export type PreviaNota = z.infer<typeof previaNotaSchema>;

/** Resposta da emissão (a mesma do Centro Fiscal). */
export const emissaoSchema = z.object({
  documento_id: z.number(),
  status: z.string(),
  mensagem: z.string(),
});
export type ResultadoEmissao = z.infer<typeof emissaoSchema>;
