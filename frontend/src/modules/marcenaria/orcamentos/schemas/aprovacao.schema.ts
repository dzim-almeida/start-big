/**
 * @fileoverview Zod da aprovação do orçamento (Spec 08A §6, Revisão 1; 08B).
 *
 * - simulação: os números do que SERIA aprovado (custos só com permissão);
 * - resumo por OS: o que foi vendido, para quem trabalha na OS (nunca custo).
 */
import { z } from 'zod';

const centavos = z.number().int();

/** POST /{id}/aprovacao/simular (08A §6.2). */
export const simulacaoAprovacaoSchema = z.object({
  moveis_aprovados: z.number().int(),
  moveis_recusados: z.number().int(),
  bruto_centavos: centavos,
  desconto_centavos: centavos,
  total_centavos: centavos,
  sinal_centavos: centavos,
  saldo_centavos: centavos,
  desconto_bp_efetivo: z.number().int(),
  sinal_bp_efetivo: z.number().int(),
  credito_cliente_centavos: centavos,             // para oferecer "Usar crédito do cliente" (08A D16)
  previsao_entrega: z.string(),                   // data pura "2026-11-08"
  avisos: z.array(z.string()),
  // Só com view_custos_marcenaria (06A D23):
  custo_total_centavos: centavos.optional(),
  margem_bruta_centavos: centavos.optional(),
  rt_total_centavos: centavos.optional(),
  margem_liquida_centavos: centavos.optional(),
  margem_liquida_bp: z.number().int().optional(),
});
export type SimulacaoAprovacao = z.infer<typeof simulacaoAprovacaoSchema>;

/** GET /por-os/{numero_os} (08A Revisão 1): a aba "Orçamento" da OS. */
export const resumoPorOsSchema = z.object({
  orcamento_id: z.number(),
  codigo: z.string(),
  versao: z.number(),
  status: z.string(),
  data_aprovacao: z.string().nullable(),
  aprovado_por: z.string().nullable(),
  projeto: z.string().nullable(),
  moveis: z.array(z.object({
    nome: z.string(),
    ambiente: z.string(),
    quantidade: z.number().int(),
    medidas: z.object({
      largura_mm: z.number().nullable(),
      altura_mm: z.number().nullable(),
      profundidade_mm: z.number().nullable(),
    }),
    os_item_id: z.number().nullable(),
  })),
  moveis_nao_aprovados: z.number().int(),
  instalacao_aprovada: z.boolean().nullable(),
  total_aprovado_centavos: centavos.nullable(),
  sinal_combinado_centavos: centavos.nullable(),
  sinal_recebido_centavos: centavos,              // lido da OS: o adiantamento lançado depois aparece aqui
  pode_desfazer: z.boolean(),
  motivos_desfazer: z.array(z.string()),
  // Remodelação item 20: os aditivos desta OS (móveis a mais), o total aprovado
  // SOMADO (principal + aditivos aprovados) e se dá para criar outro agora.
  // `default`: um backend antigo não manda os campos; a tela fica como antes.
  aditivos: z.array(z.object({
    orcamento_id: z.number(),
    codigo: z.string(),
    versao: z.number(),
    status: z.string(),
    data_aprovacao: z.string().nullable(),
    total_aprovado_centavos: centavos.nullable(),   // o que somou na OS (só aprovado)
    total_centavos: centavos,                       // o total atual da proposta
    motivos_desfazer: z.array(z.string()).default([]),   // as regras do aditivo (a OS segue)
    moveis: z.array(z.object({
      nome: z.string(),
      ambiente: z.string(),
      quantidade: z.number().int(),
      medidas: z.object({
        largura_mm: z.number().nullable(),
        altura_mm: z.number().nullable(),
        profundidade_mm: z.number().nullable(),
      }),
      os_item_id: z.number().nullable(),
    })),
  })).default([]),
  total_geral_aprovado_centavos: centavos.nullable().default(null),
  pode_criar_aditivo: z.boolean().default(false),
});
export type ResumoPorOs = z.infer<typeof resumoPorOsSchema>;
export type AditivoDaOS = ResumoPorOs['aditivos'][number];

/** Corpo de simular e aprovar (08A `AprovacaoEntrada`). */
export interface AprovacaoEntrada {
  movel_ids: number[];
  incluir_instalacao: boolean;
  desconto?: { modo: 'PERCENTUAL' | 'VALOR'; valor: number };
  /** Só no /aprovar (08A D15): o que entra na OS é o que foi RECEBIDO. */
  sinal?: {
    recebido: boolean;
    valor_centavos?: number;
    forma_pagamento_id?: number | null;
    usar_credito_cliente?: boolean;
  };
}

/** Corpo do desfazer (08A `DesfazerEntrada`). */
export interface DesfazerEntrada {
  motivo: string;
  destino_sinal: 'CREDITO' | 'DEVOLVIDO';
  codigo_gerente?: string;
}

/**
 * Formulário do AprovarModal (08B §7.4). `sinal_recebido` começa SEM resposta
 * (null): uma opção pré-marcada seria aceita sem ler (D8).
 */
export const aprovarFormSchema = z
  .object({
    movel_ids: z.array(z.number()).min(1, 'Escolha pelo menos um móvel.'),
    incluir_instalacao: z.boolean(),
    desconto: z.object({ modo: z.enum(['PERCENTUAL', 'VALOR']), valor: z.number().int().min(0) }),
    sinal_recebido: z.boolean({ required_error: 'Diga se o sinal já foi pago.', invalid_type_error: 'Diga se o sinal já foi pago.' }),
    sinal_valor_centavos: z.number().int().min(0, 'O valor recebido não pode ser negativo.'),
    forma_pagamento_id: z.number().nullable(),
    usar_credito_cliente: z.boolean(),
  })
  .superRefine((f, ctx) => {
    // D9: recebido exige a forma, a não ser que use o crédito do cliente.
    if (f.sinal_recebido && !f.usar_credito_cliente && !f.forma_pagamento_id) {
      ctx.addIssue({ code: 'custom', path: ['forma_pagamento_id'], message: 'Informe a forma de pagamento do sinal.' });
    }
  });
export type AprovarForm = Omit<z.infer<typeof aprovarFormSchema>, 'sinal_recebido'> & { sinal_recebido: boolean | null };
