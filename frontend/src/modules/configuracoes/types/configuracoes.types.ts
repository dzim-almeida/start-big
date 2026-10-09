import type { Component } from 'vue'

export type SecaoId =
  | 'seguranca'
  | 'regras-de-vendas'
  | 'gestao-financeira'
  | 'produtos-estoque'
  | 'ordens-de-servico'
  | 'marcenaria'
  | 'clientes-cadastro'
  | 'integracoes-apis'
  | 'terminais'
  | 'impressao'
  | 'formatos-exibicao'
  | 'backup-dados'
  | 'rede'
  | 'suporte'

export interface SecaoConfiguracao {
  id: SecaoId
  label: string
  icone: Component
}

export interface SecaoExposta {
  form?: Record<string, unknown>
  isDirty?: boolean
  resetar?: () => void
  /** Marcenaria (Spec 04B): o usuário pode alterar? Sem isso, sem "Salvar". */
  podeGerir?: boolean
  /** Marcenaria: erros do formulário, com as mesmas mensagens do backend. */
  erros?: Record<string, string>
  /** Marcenaria: converte o formulário (% e R$) no corpo do PUT. */
  paraApi?: (form: never) => unknown
}
