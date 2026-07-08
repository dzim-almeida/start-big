import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ConfigAtual {
  ip: string
  port: number
}

export const useNetworkConfigStore = defineStore('network-config', () => {
  const necessitaConfiguracao = ref(false)
  const tentandoConexao = ref(false)
  const erroConexao = ref<string | null>(null)
  const erroConexaoTerminal = ref(false)
  const configAtual = ref<ConfigAtual | null>(null)

  function setNecessitaConfiguracao(valor: boolean) {
    necessitaConfiguracao.value = valor
  }

  function setTentandoConexao(valor: boolean) {
    tentandoConexao.value = valor
  }

  function setErroConexao(erro: string | null) {
    erroConexao.value = erro
  }

  function setErroConexaoTerminal(valor: boolean) {
    erroConexaoTerminal.value = valor
  }

  function setConfigAtual(ip: string, port: number) {
    configAtual.value = { ip, port }
  }

  function reset() {
    necessitaConfiguracao.value = false
    tentandoConexao.value = false
    erroConexao.value = null
    erroConexaoTerminal.value = false
    configAtual.value = null
  }

  return {
    necessitaConfiguracao,
    tentandoConexao,
    erroConexao,
    erroConexaoTerminal,
    configAtual,
    setNecessitaConfiguracao,
    setTentandoConexao,
    setErroConexao,
    setErroConexaoTerminal,
    setConfigAtual,
    reset,
  }
})
