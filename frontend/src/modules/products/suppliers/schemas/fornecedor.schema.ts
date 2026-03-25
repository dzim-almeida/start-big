// ============================================================================
// MÓDULO: FornecedorSchemas (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Definição de esquemas de validação e tipagem de dados.
// TECNOLOGIAS: Zod (Validation), Vee-Validate (Schema Bridge), TypeScript.
// FUNCIONALIDADES: Validação condicional entre PF/PJ, sanitização de strings,
//                  verificação de integridade de documentos (CPF/CNPJ/Telefone).
// ============================================================================
import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';
import { unmaskPhone } from '@/shared/utils/document.utils';

const unmask = (v: string) => v.replace(/\D/g, '');

const telefoneValidation = z
  .string()
  .optional()
  .or(z.literal(''))
  .refine(
    (v) => !v || unmaskPhone(v).length === 10,
    'Telefone deve ter 10 dígitos',
  );

const celularValidation = z
  .string()
  .optional()
  .or(z.literal(''))
  .refine(
    (v) => !v || unmaskPhone(v).length === 11,
    'Celular deve ter 11 dígitos',
  );

const EnderecoReadSchema = z.object({
  id: z.number().int().positive(),
  logradouro: z.string(),
  numero: z.string(),
  complemento: z.string().nullable().optional(),
  bairro: z.string(),
  cidade: z.string(),
  estado: z.string(),
  cep: z.string(),
  id_entidade: z.number(),
  tipo_entidade: z.string(),
});

export const FornecedorReadSchema = z.object({
  id: z.number().int().positive(),
  tipo: z.string().nullable().optional(),
  nome: z.string(),
  cnpj: z.string().nullable().optional(),
  cpf: z.string().nullable().optional(),
  nome_fantasia: z.string().nullable().optional(),
  ie: z.string().nullable().optional(),
  telefone: z.string().nullable().optional(),
  celular: z.string().nullable().optional(),
  email: z.string().nullable().optional(),
  representante: z.string().nullable().optional(),
  veiculo: z.string().nullable().optional(),
  placa: z.string().nullable().optional(),
  observacao: z.string().nullable().optional(),
  banco: z.string().nullable().optional(),
  agencia: z.string().nullable().optional(),
  conta: z.string().nullable().optional(),
  tipo_conta: z.string().nullable().optional(),
  pix: z.string().nullable().optional(),
  endereco: z.array(EnderecoReadSchema).nullable().optional(),
  ativo: z.boolean(),
});

export const FornecedorFormSchema = z
  .object({
    tipo: z.enum(['produto', 'transportadora', 'entregador'], {
      required_error: 'Tipo é obrigatório',
    }),
    nome: z
      .string({ required_error: 'Nome é obrigatório' })
      .min(2, 'Nome deve ter no mínimo 2 caracteres')
      .max(255),
    cnpj: z.string().optional().or(z.literal('')),
    cpf: z.string().optional().or(z.literal('')),
    nome_fantasia: z.string().max(255).optional().or(z.literal('')),
    ie: z.string().max(14).optional().or(z.literal('')),
    telefone: telefoneValidation,
    celular: celularValidation,
    email: z
      .string()
      .optional()
      .refine(
        (v) => !v || v === '' || z.string().email().safeParse(v).success,
        'Email inválido',
      ),
    representante: z.string().max(255).optional().or(z.literal('')),
    veiculo: z.string().max(100).optional().or(z.literal('')),
    placa: z.string().max(10).optional().or(z.literal('')),
    observacao: z.string().optional().or(z.literal('')),
    banco: z.string().max(100).optional().or(z.literal('')),
    agencia: z.string().max(20).optional().or(z.literal('')),
    conta: z.string().max(20).optional().or(z.literal('')),
    tipo_conta: z.string().optional().or(z.literal('')),
    pix: z.string().max(150).optional().or(z.literal('')),
    // Endereço (campos opcionais)
    endereco_id: z.number().nullable().optional(),
    logradouro: z.string().max(255).optional().or(z.literal('')),
    numero: z.string().max(20).optional().or(z.literal('')),
    complemento: z.string().max(100).optional().or(z.literal('')),
    bairro: z.string().max(100).optional().or(z.literal('')),
    cidade: z.string().max(100).optional().or(z.literal('')),
    estado: z.string().optional().or(z.literal('')),
    cep: z.string().max(10).optional().or(z.literal('')),
  })
  .superRefine((data, ctx) => {
    if (data.tipo === 'entregador') {
      if (!data.cpf || unmask(data.cpf).length !== 11) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['cpf'],
          message: 'CPF deve ter 11 dígitos',
        });
      }
    } else {
      if (!data.cnpj || unmask(data.cnpj).length !== 14) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['cnpj'],
          message: 'CNPJ deve ter 14 dígitos',
        });
      }
    }
  });

export type FornecedorReadType = z.infer<typeof FornecedorReadSchema>;
export type FornecedorFormType = z.infer<typeof FornecedorFormSchema>;

export const fornecedorFormValidationSchema = toTypedSchema(FornecedorFormSchema);
