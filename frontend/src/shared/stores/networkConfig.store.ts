import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNetworkConfigStore = defineStore('network-config', () => {
  const necessitaConfiguracao = ref(false)
  const tentandoConexao = ref(false)
  const erroConexao = ref<string | null>(null)

  function setNecessitaConfiguracao(valor: boolean) {
    necessitaConfiguracao.value = valor
  }

  function setTentandoConexao(valor: boolean) {
    tentandoConexao.value = valor
  }

  function setErroConexao(erro: string | null) {
    erroConexao.value = erro
  }

  function reset() {
    necessitaConfiguracao.value = false
    tentandoConexao.value = false
    erroConexao.value = null
  }

  return {
    necessitaConfiguracao,
    tentandoConexao,
    erroConexao,
    setNecessitaConfiguracao,
    setTentandoConexao,
    setErroConexao,
    reset,
  }
})
