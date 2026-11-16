/**
 * Contrato dos portes da loja e do preço por porte (Spec 02A/02B do lava-rápido).
 * Espelha app/schemas/lava_rapido/porte.py. Dinheiro em centavos (PR3).
 */
import { z } from 'zod';

export const porteSchema = z.object({
  id: z.number(),
  /** Id do tipo de trabalho do registry ("carro", "moto", "pesado"...). */
  tipo_veiculo: z.string(),
  nome: z.string(),
  ordem: z.number(),
  ativo: z.boolean(),
});
export type Porte = z.infer<typeof porteSchema>;

export const precoPorteSchema = z.object({
  porte_id: z.number(),
  valor: z.number(),
  duracao_minutos: z.number().nullable(),
});
export type PrecoPorte = z.infer<typeof precoPorteSchema>;

/** Serviço ativo com o preço que vale para um porte (botões da comanda). */
export const servicoDoPorteSchema = z.object({
  servico_id: z.number(),
  descricao: z.string(),
  valor: z.number(),
  duracao_minutos: z.number().nullable(),
  /** false = sem preço cadastrado para o porte; vale o padrão do serviço. */
  preco_do_porte: z.boolean(),
});
export type ServicoDoPorte = z.infer<typeof servicoDoPorteSchema>;

export interface PorteCreate {
  tipo_veiculo: string;
  nome: string;
}

export interface PorteUpdate {
  nome?: string;
  ordem?: number;
  ativo?: boolean;
}
