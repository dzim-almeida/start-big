import { ref } from 'vue'

export function useGerenteAprovacao() {
  const isOpen = ref(false)
  const isLoading = ref(false)

  let _resolve: ((pin: string | null) => void) | null = null

  function pedirPin(): Promise<string | null> {
    isOpen.value = true
    return new Promise((resolve) => {
      _resolve = resolve
    })
  }

  function confirmar(pin: string) {
    isOpen.value = false
    _resolve?.(pin)
    _resolve = null
  }

  function cancelar() {
    isOpen.value = false
    _resolve?.(null)
    _resolve = null
  }

  return { isOpen, isLoading, pedirPin, confirmar, cancelar }
}
