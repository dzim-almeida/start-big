import z from 'zod';

import { OsPriorityEnum } from './enums/osEnums.schema';

export const OrderServiceBaseSchema = z.object({
  // Status e Prioridade
  prioridade: OsPriorityEnum,

  // Descrição técnica
  defeito_relatado: z
    .string({ required_error: 'A descrição de defeito é obrigatória' })
    .max(500, 'A descrição de defeito deve ter máximo 500 caracteres'),
  diagnostico: z.string().max(500).nullish(),
  solucao: z.string().max(500).nullish(),

  // Observacoes Operacionais
  senha_aparelho: z.string().max(100).nullish(),
  acessorios: z.string().max(500).nullish(),
  condicoes_aparelho: z.string().max(500).nullish(),
  observacoes: z.string().max(500).nullish(),

  // Financeiro
  desconto: z.number().int().nullish(),

  // Prazos e garantia
  garantia: z.string().max(20).nullish(),
  data_previsao: z.string().nullish(),
});

