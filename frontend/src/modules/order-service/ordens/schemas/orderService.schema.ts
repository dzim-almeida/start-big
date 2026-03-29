import z from 'zod';

import { OsPriorityEnum } from './enums/osEnums.schema';

export const OrderServiceBaseSchema = z.object({
  // Status e Prioridade
  prioridade: OsPriorityEnum,

  // Descrição técnica
  defeito_relatado: z
    .string({ required_error: 'A descrição de defeito é obrigatória' })
    .max(500, 'A descrição de defeito deve ter máximo 500 caracteres'),
  diagnostico: z.string().max(500, 'O diagnóstico deve ter máximo 500 caracteres').optional(),
  solucao: z.string().max(500, 'A solução deve ter máximo 500 caracteres').optional(),

  // Observacoes Operacionais
  senha_aparelho: z.string().max(100, 'A senha deve ter máximo 100 caracteres').optional(),
  acessorios: z
    .string()
    .max(500, 'A observação de acessórios deve ter máximo 500 caracteres')
    .optional(),
  condicoes_aparelho: z
    .string()
    .max(500, 'A observação de condições do aparelho deve ter máximo 500 caracteres')
    .optional(),
  observacoes: z.string().max(500, 'A observação deve ter máximo 500 caracteres').optional(),

  // Financeiro
  desconto: z.number().int().optional(),
  valor_entrada: z.number().int().optional(),

  // Prazos e garantia
  garantia: z.string().max(20, 'A garantia deve ter máximo 20 caracteres').optional(),
  data_previsao: z.string().datetime().optional(),
});

