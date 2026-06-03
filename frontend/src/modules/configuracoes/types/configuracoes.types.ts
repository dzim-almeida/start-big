import type { Component } from 'vue'

export type SecaoId =
  | 'regras-de-vendas'
  | 'produtos-estoque'
  | 'ordens-de-servico'
  | 'clientes-cadastro'
  | 'financeiro-taxas'
  | 'integracoes-apis'
  | 'impressao'
  | 'formatos-exibicao'
  | 'backup-dados'
  | 'suporte'

export interface SecaoConfiguracao {
  id: SecaoId
  label: string
  icone: Component
}
