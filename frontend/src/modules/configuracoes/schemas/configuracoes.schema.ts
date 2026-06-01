import { z } from 'zod'

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
