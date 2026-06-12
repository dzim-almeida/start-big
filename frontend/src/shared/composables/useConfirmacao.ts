import { ref } from 'vue'

export interface OpcoesConfirmacao {
  titulo: string
  descricao: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'warning' | 'info'
}

export function useConfirmacao() {
  const isOpen = ref(false)
  const opcoes = ref<OpcoesConfirmacao>({ titulo: '', descricao: '' })

  let _resolve: ((ok: boolean) => void) | null = null

  function pedirConfirmacao(opts: OpcoesConfirmacao): Promise<boolean> {
    opcoes.value = { confirmLabel: 'Confirmar', cancelLabel: 'Cancelar', variant: 'warning', ...opts }
    isOpen.value = true
    return new Promise((resolve) => {
      _resolve = resolve
    })
  }

  function confirmar() {
    isOpen.value = false
    _resolve?.(true)
    _resolve = null
  }

  function cancelar() {
    isOpen.value = false
    _resolve?.(false)
    _resolve = null
  }

  return { isOpen, opcoes, pedirConfirmacao, confirmar, cancelar }
}
