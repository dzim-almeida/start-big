import { z } from 'zod'

export const ConfiguracaoProdutosSchema = z.object({
  id: z.number(),
  empresa_id: z.number(),

  exigir_codigo_barras: z.boolean(),
  exigir_categoria: z.boolean(),
  exigir_preco_custo: z.boolean(),

  margem_lucro_padrao: z.number(),
  utilizar_preco_atacado: z.boolean(),

  permitir_venda_estoque_zerado: z.boolean(),
  quantidade_minima_padrao: z.number(),
  unidade_medida_padrao: z.string(),

  data_atualizacao: z.string(),
})

export const ConfiguracaoProdutosUpdateSchema = ConfiguracaoProdutosSchema
  .omit({ id: true, empresa_id: true, data_atualizacao: true })
  .partial()

export type ConfiguracaoProdutosRead = z.infer<typeof ConfiguracaoProdutosSchema>
export type ConfiguracaoProdutosUpdate = z.infer<typeof ConfiguracaoProdutosUpdateSchema>

export const ConfiguracaoClientesSchema = z.object({
  id: z.number(),
  empresa_id: z.number(),

  exigir_cpf_pf: z.boolean(),
  exigir_cnpj_pj: z.boolean(),
  exigir_celular: z.boolean(),
  exigir_rg_pf: z.boolean(),
  exigir_ie_pj: z.boolean(),
  exigir_email: z.boolean(),
  exigir_endereco: z.boolean(),

  tipo_pessoa_padrao: z.enum(['PF', 'PJ']),
  exibir_genero: z.boolean(),
  exibir_data_nascimento: z.boolean(),

  bloquear_faturamento_inativo: z.boolean(),
  oferecer_reativacao_rapida: z.boolean(),

  ativar_limite_credito: z.boolean(),
  bloquear_venda_limite: z.boolean(),

  data_atualizacao: z.string(),
})

export const ConfiguracaoClientesUpdateSchema = ConfiguracaoClientesSchema
  .omit({ id: true, empresa_id: true, data_atualizacao: true })
  .partial()

export type ConfiguracaoClientesRead = z.infer<typeof ConfiguracaoClientesSchema>
export type ConfiguracaoClientesUpdate = z.infer<typeof ConfiguracaoClientesUpdateSchema>

export const GARANTIA_OPTIONS = [
  'Sem garantia',
  '30 dias',
  '60 dias',
  '90 dias',
  '6 meses',
  '1 ano',
] as const

export const ConfiguracaoOSSchema = z.object({
  id: z.number(),
  empresa_id: z.number(),

  prazo_entrega_padrao: z.number().int().min(1),
  garantia_padrao: z.enum(GARANTIA_OPTIONS),
  prazo_abandono_dias: z.number().int().min(1),
  taxa_diagnostico_padrao: z.number().int().min(0),

  data_atualizacao: z.string(),
})

export const ConfiguracaoOSUpdateSchema = ConfiguracaoOSSchema
  .omit({ id: true, empresa_id: true, data_atualizacao: true })
  .partial()

export type ConfiguracaoOSRead = z.infer<typeof ConfiguracaoOSSchema>
export type ConfiguracaoOSUpdate = z.infer<typeof ConfiguracaoOSUpdateSchema>
