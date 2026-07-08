import { z } from 'zod'
import { toTypedSchema } from '@vee-validate/zod'

export const terminalConfigSchema = z.object({
  serverIp: z
    .string()
    .min(1, 'IP do servidor obrigatório')
    .regex(/^(\d{1,3}\.){3}\d{1,3}$/, 'Formato de IP inválido'),
  serverPort: z.coerce
    .number({ invalid_type_error: 'Porta deve ser um número' })
    .min(1, 'Porta mínima: 1')
    .max(65535, 'Porta máxima: 65535'),
})

export const terminalConfigTypedSchema = toTypedSchema(terminalConfigSchema)
export type TerminalConfigType = z.infer<typeof terminalConfigSchema>

export const servidorConfigSchema = z.object({
  customPort: z.coerce
    .number({ invalid_type_error: 'Porta deve ser um número' })
    .min(1, 'Porta mínima: 1')
    .max(65535, 'Porta máxima: 65535')
    .optional(),
})

export const servidorConfigTypedSchema = toTypedSchema(servidorConfigSchema)
export type ServidorConfigType = z.infer<typeof servidorConfigSchema>
