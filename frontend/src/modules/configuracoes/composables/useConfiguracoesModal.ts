import { ref } from 'vue'
import type { SecaoId } from '../types/configuracoes.types'

export function useConfiguracoesModal() {
  const secaoAtiva = ref<SecaoId>('regras-de-vendas')

  function irPara(secao: SecaoId) {
    secaoAtiva.value = secao
  }

  return { secaoAtiva, irPara }
}
