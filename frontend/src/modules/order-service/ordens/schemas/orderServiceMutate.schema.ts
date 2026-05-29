import z from "zod";
import { toTypedSchema } from "@vee-validate/zod";

import { OrderServiceBaseSchema } from "./orderService.schema";

import { OsPriorityEnum, OsStatusEnum } from "./enums/osEnums.schema";

import { OsEquipCreateSchema } from "./relationship/osEquip.schema";
import { OsItemCreateSchema } from "./relationship/osItem.schema";
import { OsPaymentCreateSchema } from "./relationship/osPayment.schema";



export const OrderServiceCreateSchema = z.object({
  ...OrderServiceBaseSchema.shape,

  // Vínculos
  cliente_id: z.number().int().positive(),
  funcionario_id: z.number().int().positive(),

  // Aninhamento
  equipamento: OsEquipCreateSchema,
  itens: z.array(OsItemCreateSchema).default([]),
});

export const orderServiceCreateValidationSchema = toTypedSchema(OrderServiceCreateSchema)
export type OrderServiceCreateSchemaDataType = z.infer<typeof OrderServiceCreateSchema>

export const OrderServiceUpdateSchema = z.object({
  // Status e Prioridade
  prioridade: OsPriorityEnum.optional(),
  status: OsStatusEnum.optional(),

  // Descrição técnica
  defeito_relatado: z
    .string({ required_error: 'A descrição de defeito é obrigatória' })
    .max(500, 'A descrição de defeito deve ter máximo 500 caracteres')
    .optional(),
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

  // Relações
  funcionario_id: z.number().int().positive().optional(),

  // Prazos e garantia
  garantia: z.string().max(20, 'A garantia deve ter máximo 20 caracteres').optional(),
  data_previsao: z.string().optional(),
});

export const orderServiceUpdateValidationSchema = toTypedSchema(OrderServiceUpdateSchema)
export type OrderServiceUpdateDataType = z.infer<typeof OrderServiceUpdateSchema>

export const OrderServiceReadySchema = z.object({
  solucao: z.string().max(500, 'Uma descrição deve ter no máximo 500 caracteres').optional(),
  observacoes: z.string().max(500, 'Uma observação deve ter no máximo 500 caracteres'),
  desconto: z.number().int().min(0, 'Desconto não pode ser negativo').default(0),
  taxa_entrega: z.number().int().min(0, 'Taxa de entrega inválida').default(0),
  acrescimo: z.number().int().min(0, 'Acréscimo inválido').default(0),
  valor_entrada: z.number().int().min(0, 'Adiantamento não pode ser negativo').optional(),
  pagamentos: z
    .array(OsPaymentCreateSchema)
    .min(1, 'Para finalizar precisa de ao menos um pagamento válido'),
});

export const orderServiceReadyValidationSchema = toTypedSchema(OrderServiceReadySchema)
export type OrderServiceReadyDataType = z.infer<typeof OrderServiceReadySchema>

export const OrderServiceCancelSchema = z.object({
  motivo: z.string().max(500, 'Um motivo deve ter no máximo 500 caracteres'),
});

export const orderServiceCancelValidationSchema = toTypedSchema(OrderServiceCancelSchema)
export type OrderServiceCancelDataType = z.infer<typeof OrderServiceCancelSchema>
