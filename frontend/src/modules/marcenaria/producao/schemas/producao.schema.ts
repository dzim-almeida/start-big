/**
 * @fileoverview O que a API da produção devolve (Spec 12A §6), conferido pelo
 * zod. Nenhum preço: a tela é do computador da fábrica (P4).
 */
import { z } from 'zod';

import { SITUACOES, sugestaoStatusSchema } from '@/modules/marcenaria/terceirizados/schemas/terceirizado.schema';

/** As três situações de uma etapa (12A D2). */
export const STATUS_ETAPA = ['PENDENTE', 'EM_EXECUCAO', 'CONCLUIDA'] as const;
export type StatusEtapa = (typeof STATUS_ETAPA)[number];

export const etapaSchema = z.object({
  id: z.number(),
  nome: z.string(),
  ordem: z.number(),
  status: z.enum(STATUS_ETAPA),
  responsavel: z.string().nullable(),                       // quem está fazendo / fez
  responsavel_funcionario_id: z.number().nullable(),
  iniciada_em: z.string().nullable(),                       // instante em UTC, sem fuso ("2026-10-09T18:28:07")
  concluida_em: z.string().nullable(),
  concluida_por: z.string().nullable(),                     // quem clicou (pode ser outro usuário)
});
export type Etapa = z.infer<typeof etapaSchema>;

export const movelProducaoSchema = z.object({
  movel_id: z.number(),
  nome: z.string(),
  ambiente: z.string(),
  quantidade: z.number(),
  medidas: z.object({
    largura_mm: z.number().nullable(), altura_mm: z.number().nullable(), profundidade_mm: z.number().nullable(),
  }),
  tipo_producao: z.string(),                                // INTERNA ou TERCEIRIZADA
  pronto: z.boolean(),
  // Só nos móveis feitos na fábrica:
  sem_etapas: z.boolean().optional(),                       // 12A D6: sem caminho para ficar pronto
  proxima_etapa: z.string().nullable().optional(),          // a primeira ainda não concluída
  etapas: z.array(etapaSchema).optional(),
  // Só nos terceirizados (12A D5): a situação da 11A.
  terceirizado: z.object({
    situacao: z.enum(SITUACOES), previsao: z.string().nullable(), atrasado: z.boolean(),
  }).optional(),
});
export type MovelProducao = z.infer<typeof movelProducaoSchema>;

export const producaoSchema = z.object({
  os: z.object({
    numero_os: z.string(),
    status: z.string(),
    editavel: z.boolean(),
    previsao: z.string().nullable(),                        // data pura da entrega prevista
  }),
  progresso: z.object({
    etapas_concluidas: z.number(), etapas_total: z.number(), moveis_prontos: z.number(), moveis_total: z.number(),
  }),
  producao_concluida: z.boolean(),
  moveis: z.array(movelProducaoSchema),
  // 12A D16: a escrita sugere o próximo status da OS (a leitura manda null).
  sugestao_status: sugestaoStatusSchema,
});
export type ProducaoDaOS = z.infer<typeof producaoSchema>;

/** GET /producao: o quadro da fábrica (12A D18). */
export const quadroSchema = z.object({
  itens: z.array(z.object({
    numero_os: z.string(),
    cliente: z.string().nullable(),
    projeto: z.string().nullable(),
    status: z.string(),
    rotulo_status: z.string(),                              // o texto do segmento ("Em Produção")
    previsao: z.string().nullable(),
    progresso: producaoSchema.shape.progresso,
    producao_concluida: z.boolean(),
    moveis_atrasados: z.number(),
    proxima_etapa: z.object({ nome: z.string(), moveis: z.number() }).nullable(),
  })),
});
export type ItemQuadro = z.infer<typeof quadroSchema>['itens'][number];
