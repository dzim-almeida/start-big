/**
 * Contrato da agenda (Spec 08A/08B do lava-rápido). Espelha
 * app/schemas/lava_rapido/agendamento.py. Dinheiro em centavos.
 */
import { z } from 'zod';

export const SITUACOES_AGENDA = ['AGENDADO', 'CHEGOU', 'NAO_VEIO', 'CANCELADO'] as const;
export type SituacaoAgenda = (typeof SITUACOES_AGENDA)[number];

export const servicoAgendadoSchema = z.object({
  servico_id: z.number().nullable(),
  nome: z.string(),
  valor: z.number(),
});
export type ServicoAgendado = z.infer<typeof servicoAgendadoSchema>;

export const agendamentoSchema = z.object({
  id: z.number(),
  /** UTC, como vem do backend (sem "Z"). */
  inicio: z.string(),
  duracao_minutos: z.number().nullable(),
  cliente_id: z.number().nullable(),
  cliente_nome: z.string(),
  cliente_contato: z.string().nullable(),
  placa: z.string().nullable(),
  veiculo: z.string().nullable(),
  tipo_veiculo: z.string().nullable(),
  porte_id: z.number().nullable(),
  servicos: z.array(servicoAgendadoSchema),
  observacao: z.string().nullable(),
  situacao: z.enum(SITUACOES_AGENDA),
  numero_os: z.string().nullable(),
  criado_em: z.string(),
});
export type Agendamento = z.infer<typeof agendamentoSchema>;

/** O que a tela manda ao criar ou alterar. `inicio` com fuso (toISOString). */
export interface AgendamentoEntrada {
  inicio: string;
  duracao_minutos: number | null;
  cliente_id: number | null;
  cliente_nome: string;
  cliente_contato: string | null;
  placa: string | null;
  veiculo: string | null;
  tipo_veiculo: string | null;
  porte_id: number | null;
  servicos: ServicoAgendado[];
  observacao: string | null;
}
