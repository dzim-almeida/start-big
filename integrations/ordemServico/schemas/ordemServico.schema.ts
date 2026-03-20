import { z } from 'zod';

export const OrdemServicoStatusSchema = z.enum([
  'ABERTA',
  'EM_ANDAMENTO',
  'AGUARDANDO_PECAS',
  'AGUARDANDO_APROVACAO',
  'AGUARDANDO_RETIRADA',
  'FINALIZADA',
  'CANCELADA',
]);

export const OrdemServicoPrioridadeSchema = z.enum([
  'BAIXA',
  'NORMAL',
  'ALTA',
  'URGENTE',
]);

export const ClienteResumoSchema = z.object({
  id: z.number().int().positive(),
  tipo: z.enum(['PF', 'PJ']),
  nome: z.string().optional().nullable(),
  cpf: z.string().optional().nullable(),
  razao_social: z.string().optional().nullable(),
  cnpj: z.string().optional().nullable(),
  nome_fantasia: z.string().optional().nullable(),
  celular: z.string().optional().nullable(),
  telefone: z.string().optional().nullable(),
});

export const FuncionarioResumoSchema = z.object({
  id: z.number().int().positive(),
  nome: z.string(),
});

export const OrdemServicoItemReadSchema = z.object({
  id: z.number().int().positive(),
  ordem_servico_id: z.number().int().positive(),
  servico_id: z.number().int().positive().optional().nullable(),
  descricao: z.string(),
  quantidade: z.number().positive(),
  valor_unitario: z.number().int().nonnegative(),
  valor_total: z.number().int().nonnegative(),
});

export const OrdemServicoFotoReadSchema = z.object({
  id: z.number().int().positive(),
  ordem_servico_id: z.number().int().positive(),
  nome_arquivo: z.string(),
  url: z.string(),
  data_criacao: z.string(),
});

export const FormaPagamentoReadSchema = z.object({
  id: z.number().int().positive(),
  nome: z.string(),
  tipo: z.enum(['DINHEIRO', 'PIX', 'CARTAO_CREDITO', 'CARTAO_DEBITO', 'BOLETO', 'OUTRO']),
  ativo: z.boolean(),
  permite_parcelamento: z.boolean(),
});

export const OSPagamentoReadSchema = z.object({
  id: z.number().int().positive(),
  forma_pagamento_id: z.number().int().positive(),
  valor: z.number().int().nonnegative(),
  parcelas: z.number().int().positive(),
  bandeira_cartao: z.string().optional().nullable(),
  detalhes: z.record(z.any()).optional().nullable(),
  forma_pagamento: FormaPagamentoReadSchema.optional().nullable(),
});

export const OrdemServicoReadSchema = z.object({
  id: z.number().int().positive(),
  numero: z.string(),
  cliente_id: z.number().int().positive(),
  funcionario_id: z.number().int().positive().optional().nullable(),
  status: OrdemServicoStatusSchema,
  prioridade: OrdemServicoPrioridadeSchema,
  equipamento: z.string(),
  marca: z.string().optional().nullable(),
  modelo: z.string().optional().nullable(),
  numero_serie: z.string().optional().nullable(),
  imei: z.string().optional().nullable(),
  cor: z.string().optional().nullable(),
  senha_aparelho: z.string().optional().nullable(),
  acessorios: z.string().optional().nullable(),
  condicoes_aparelho: z.string().optional().nullable(),
  defeito_relatado: z.string(),
  diagnostico: z.string().optional().nullable(),
  solucao: z.string().optional().nullable(),
  observacoes: z.string().optional().nullable(),
  valor_total: z.number().int().nonnegative(),
  desconto: z.number().int().nonnegative(),
  valor_entrada: z.number().int().nonnegative(),
  forma_pagamento: z.string().optional().nullable(),
  garantia: z.string().optional().nullable(),
  data_previsao: z.string().optional().nullable(),
  data_finalizacao: z.string().optional().nullable(),
  data_criacao: z.string(),
  data_atualizacao: z.string(),
  ativo: z.boolean(),
  cliente: ClienteResumoSchema.optional().nullable(),
  funcionario: FuncionarioResumoSchema.optional().nullable(),
  itens: z.array(OrdemServicoItemReadSchema),
  pagamentos: z.array(OSPagamentoReadSchema),
  fotos: z.array(OrdemServicoFotoReadSchema),
});

export const OrdemServicoListReadSchema = z.object({
  id: z.number().int().positive(),
  numero: z.string(),
  cliente_id: z.number().int().positive(),
  funcionario_id: z.number().int().positive().optional().nullable(),
  status: OrdemServicoStatusSchema,
  prioridade: OrdemServicoPrioridadeSchema,
  equipamento: z.string(),
  defeito_relatado: z.string(),
  valor_total: z.number().int().nonnegative(),
  data_previsao: z.string().optional().nullable(),
  data_criacao: z.string(),
  ativo: z.boolean(),
  cliente: ClienteResumoSchema.optional().nullable(),
  funcionario: FuncionarioResumoSchema.optional().nullable(),
});

export const PaginatedOrdensServicoSchema = z.object({
  items: z.array(OrdemServicoListReadSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  limit: z.number().int().positive(),
  pages: z.number().int().nonnegative(),
});

// ===========================================================================
// SCHEMAS DE FORMULARIO (VALIDACAO DE ENTRADA)
// ===========================================================================

/**
 * Schema para validacao de item do formulario
 */
export const OSItemFormSchema = z.object({
  servico_id: z.string().optional(),
  descricao: z.string().min(1, 'Descricao e obrigatoria'),
  quantidade: z.number().positive('Quantidade deve ser maior que zero'),
  valor_unitario: z.number().nonnegative('Valor unitario deve ser positivo'),
});

/**
 * Schema para validacao do formulario de OS
 * Usado antes de enviar para a API
 */
export const OSFormDataSchema = z.object({
  equipamento: z.string().min(1, 'Equipamento e obrigatorio'),
  marca: z.string().optional(),
  modelo: z.string().optional(),
  numero_serie: z.string().optional(),
  imei: z.string().optional(),
  cor: z.string().optional(),
  acessorios: z.string().optional(),
  senha_aparelho: z.string().optional(),
  condicoes_aparelho: z.string().optional(),
  defeito_relatado: z.string().min(1, 'Defeito relatado e obrigatorio'),
  diagnostico: z.string().optional(),
  solucao: z.string().optional(),
  observacoes: z.string().optional(),
  prioridade: OrdemServicoPrioridadeSchema,
  status: OrdemServicoStatusSchema,
  funcionario_id: z.string().optional(),
  data_previsao: z.string().optional(),
  valor_orcamento: z.string().optional(),
  forma_pagamento: z.string().optional(),
  garantia: z.string().optional(),
  desconto: z.string().optional(),
  valor_entrada: z.string().optional(),
  data_finalizacao: z.string().optional(),
});

/**
 * Schema para criacao de item de OS (payload para API)
 */
export const OrdemServicoItemCreateSchema = z.object({
  servico_id: z.number().int().positive().optional(),
  descricao: z.string().min(1, 'Descricao e obrigatoria'),
  quantidade: z.number().positive('Quantidade deve ser maior que zero'),
  valor_unitario: z.number().int().nonnegative('Valor unitario deve ser positivo'),
});

/**
 * Schema para criacao de OS (payload para API)
 */
export const OrdemServicoCreateSchema = z.object({
  cliente_id: z.number().int().positive('Cliente e obrigatorio'),
  funcionario_id: z.number().int().positive().optional(),
  prioridade: OrdemServicoPrioridadeSchema.optional(),
  equipamento: z.string().min(1, 'Equipamento e obrigatorio'),
  marca: z.string().optional(),
  modelo: z.string().optional(),
  numero_serie: z.string().optional(),
  imei: z.string().optional(),
  cor: z.string().optional(),
  senha_aparelho: z.string().optional(),
  acessorios: z.string().optional(),
  condicoes_aparelho: z.string().optional(),
  defeito_relatado: z.string().min(1, 'Defeito relatado e obrigatorio'),
  diagnostico: z.string().optional(),
  observacoes: z.string().optional(),
  data_previsao: z.string().optional(),
  desconto: z.number().int().nonnegative().optional(),
  valor_entrada: z.number().int().nonnegative().optional(),
  forma_pagamento: z.string().optional(),
  garantia: z.string().optional(),
  itens: z.array(OrdemServicoItemCreateSchema).optional(),
});

/**
 * Schema para atualizacao de OS (payload para API)
 */
export const OrdemServicoUpdateSchema = z.object({
  funcionario_id: z.number().int().positive().optional(),
  status: OrdemServicoStatusSchema.optional(),
  prioridade: OrdemServicoPrioridadeSchema.optional(),
  equipamento: z.string().min(1).optional(),
  marca: z.string().optional(),
  modelo: z.string().optional(),
  numero_serie: z.string().optional(),
  imei: z.string().optional(),
  cor: z.string().optional(),
  senha_aparelho: z.string().optional(),
  acessorios: z.string().optional(),
  condicoes_aparelho: z.string().optional(),
  defeito_relatado: z.string().min(1).optional(),
  diagnostico: z.string().optional(),
  solucao: z.string().optional(),
  observacoes: z.string().optional(),
  data_previsao: z.string().optional(),
  data_finalizacao: z.string().optional(),
  desconto: z.number().int().nonnegative().optional(),
  valor_entrada: z.number().int().nonnegative().optional(),
  forma_pagamento: z.string().optional(),
  garantia: z.string().optional(),
  itens: z.array(OrdemServicoItemCreateSchema).optional(),
});

// ===========================================================================
// TIPOS INFERIDOS
// ===========================================================================
export type OrdemServicoReadZod = z.infer<typeof OrdemServicoReadSchema>;
export type OrdemServicoListReadZod = z.infer<typeof OrdemServicoListReadSchema>;
export type PaginatedOrdensServicoZod = z.infer<typeof PaginatedOrdensServicoSchema>;
export type OSFormDataZod = z.infer<typeof OSFormDataSchema>;
export type OSItemFormZod = z.infer<typeof OSItemFormSchema>;
export type OrdemServicoCreateZod = z.infer<typeof OrdemServicoCreateSchema>;
export type OrdemServicoUpdateZod = z.infer<typeof OrdemServicoUpdateSchema>;
