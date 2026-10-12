/**
 * @fileoverview O que a API da entrega e da agenda devolve (Spec 13A §6),
 * conferido pelo zod. Nenhum preço: a aba é de quem monta e entrega (P4).
 */
import { z } from 'zod';

/** As situações da entrega de um ambiente (13A D4). */
export const SITUACOES_ENTREGA = ['PENDENTE', 'CONFORME', 'COM_RESSALVAS'] as const;
export type SituacaoEntrega = (typeof SITUACOES_ENTREGA)[number];

/** Um montador: o funcionário e o nome COPIADO na hora (13A, I4). */
export const montadorSchema = z.object({ funcionario_id: z.number(), nome: z.string() });
export type Montador = z.infer<typeof montadorSchema>;

/** A marcação de um item do checklist, passada a limpo do papel (13A D4). */
export const MARCACOES = ['ok', 'nao_ok'] as const;
export type Marcacao = (typeof MARCACOES)[number] | null;

const medidasSchema = z.object({
  largura_mm: z.number().nullable(), altura_mm: z.number().nullable(), profundidade_mm: z.number().nullable(),
});

export const pendenciaSchema = z.object({
  id: z.number(),
  descricao: z.string(),
  situacao: z.enum(['ABERTA', 'RESOLVIDA']),
  criada_em: z.string(),                                 // instante em UTC, sem fuso
  criada_por: z.string().nullable(),
  resolucao: z.string().nullable(),
  resolvida_em: z.string().nullable(),                   // data pura
  resolvida_por: z.string().nullable(),
});
export type Pendencia = z.infer<typeof pendenciaSchema>;

export const fotoEntregaSchema = z.object({
  id: z.number(),                                        // o VÍNCULO (é o que se exclui)
  os_foto_id: z.number(),                                // a foto na galeria da OS
  tipo: z.enum(['TERMO', 'MONTAGEM']),
  url: z.string(),
  nome_arquivo: z.string(),
});
export type FotoEntrega = z.infer<typeof fotoEntregaSchema>;

export const entregaSchema = z.object({
  id: z.number(),
  ambiente_id: z.number(),
  ambiente: z.string(),
  situacao: z.enum(SITUACOES_ENTREGA),
  moveis: z.array(z.object({ nome: z.string(), quantidade: z.number(), medidas: medidasSchema })),
  checklist: z.array(z.object({ texto: z.string(), marcacao: z.enum(MARCACOES).nullable() })),
  data_entrega: z.string().nullable(),
  montadores: z.array(montadorSchema),
  recebido_por: z.string().nullable(),
  observacoes: z.string().nullable(),
  registrado_por: z.string().nullable(),
  registrado_em: z.string().nullable(),
  pendencias: z.array(pendenciaSchema),
  fotos: z.array(fotoEntregaSchema),
  // O agendamento mais recente que inclui o ambiente (13A §6.1).
  agendamento: z.object({
    id: z.number(), data: z.string(), hora_inicio: z.string().nullable(), montadores: z.array(montadorSchema),
  }).nullable(),
});
export type EntregaAmbiente = z.infer<typeof entregaSchema>;

export const agendamentoSchema = z.object({
  id: z.number(),
  data: z.string(),                                      // data pura "2026-11-03"
  hora_inicio: z.string().nullable(),                    // "08:00"
  ambiente_ids: z.array(z.number()),
  ambientes: z.array(z.string()),
  montadores: z.array(montadorSchema),
  observacao: z.string().nullable(),
  criado_por: z.string().nullable(),
  atrasado: z.boolean(),                                 // 13A D12
  editavel: z.boolean(),                                 // 13A D10 e OS aberta
});
export type Agendamento = z.infer<typeof agendamentoSchema>;

/** O resumo da aba e do aviso da finalização (13A D15, D16). */
export const resumoSchema = z.object({
  entregues: z.number(),
  total: z.number(),
  todos_entregues: z.boolean(),
  ambientes_pendentes: z.array(z.string()),
  pendencias_abertas: z.array(z.object({
    id: z.number(), entrega_id: z.number(), ambiente: z.string(), descricao: z.string(),
  })),
});
export type ResumoEntrega = z.infer<typeof resumoSchema>;

/** Um aviso que não trava: "SEM_FOTO_TERMO", "MONTADOR_OCUPADO" (13A D8, D11). */
export const avisoSchema = z.object({ codigo: z.string(), mensagem: z.string() }).passthrough();
export type AvisoEntrega = z.infer<typeof avisoSchema>;

export const entregaDaOSSchema = z.object({
  os: z.object({ numero_os: z.string(), status: z.string(), editavel: z.boolean() }),
  projeto: z.object({ codigo: z.string().nullable(), nome: z.string().nullable(), endereco_obra: z.string().nullable() }),
  cliente: z.object({ nome: z.string().nullable(), telefone: z.string().nullable() }),
  entregas: z.array(entregaSchema),
  agendamentos: z.array(agendamentoSchema),
  resumo: resumoSchema,
  avisos: z.array(avisoSchema),
});
export type EntregaDaOS = z.infer<typeof entregaDaOSSchema>;

/** GET /instalacoes: quem instala onde (13A D13). */
export const instalacoesSchema = z.object({
  itens: z.array(z.object({
    id: z.number(),
    data: z.string(),
    hora_inicio: z.string().nullable(),
    numero_os: z.string(),
    status_os: z.string(),
    cliente: z.string().nullable(),
    telefone: z.string().nullable(),
    projeto: z.string().nullable(),
    endereco_obra: z.string().nullable(),
    ambientes: z.array(z.object({
      ambiente_id: z.number(), nome: z.string(), situacao: z.enum(SITUACOES_ENTREGA).nullable(),
    })),
    montadores: z.array(montadorSchema),
    observacao: z.string().nullable(),
    atrasado: z.boolean(),
  })),
});
export type Instalacao = z.infer<typeof instalacoesSchema>['itens'][number];
