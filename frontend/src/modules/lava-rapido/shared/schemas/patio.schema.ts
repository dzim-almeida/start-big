/**
 * Contrato do pátio e dos lavadores (Spec 04A/10A do lava-rápido).
 * Espelha app/schemas/lava_rapido/patio.py e lavador.py. Dinheiro em centavos.
 */
import { z } from 'zod';

export const lavadorSchema = z.object({
  funcionario_id: z.number(),
  nome: z.string(),
});
export type Lavador = z.infer<typeof lavadorSchema>;

export const cartaoPatioSchema = z.object({
  numero_os: z.string(),
  /** Código do enum (ABERTA, EM_ANDAMENTO, AGUARDANDO_RETIRADA, FINALIZADA). */
  status: z.string(),
  tipo_veiculo: z.string().nullable(),
  placa: z.string().nullable(),
  modelo: z.string().nullable(),
  marca: z.string().nullable(),
  cor: z.string().nullable(),
  porte: z.string().nullable(),
  cliente_nome: z.string().nullable(),
  /** Celular (ou telefone) para o WhatsApp do "Pronto". */
  cliente_contato: z.string().nullable(),
  servicos: z.array(z.string()),
  valor_total: z.number(),
  lavadores: z.array(lavadorSchema),
  responsavel: z.string().nullable(),
  avarias: z.array(z.string()),
  /** UTC, como vem do backend. */
  entrada: z.string(),
  previsao: z.string().nullable(),
  finalizada_em: z.string().nullable(),
});
export type CartaoPatio = z.infer<typeof cartaoPatioSchema>;

export const patioSchema = z.object({
  aguardando: z.array(cartaoPatioSchema),
  lavando: z.array(cartaoPatioSchema),
  pronto: z.array(cartaoPatioSchema),
  entregues_hoje: z.array(cartaoPatioSchema),
});
export type Patio = z.infer<typeof patioSchema>;
