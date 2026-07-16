import { ref, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useNetworkConfigStore } from '@/shared/stores/networkConfig.store'
import { verificarSaude } from '@/shared/services/system/health.service'
import { tauriDisponivel, getConfig } from '@/shared/services/system/tauriConfig.service'

const INTERVALO_PING_MS = 30_000 // 30 segundos
const MAX_FALHAS_CONSECUTIVAS = 3

/**
 * Monitoramento contínuo de saúde para terminais.
 * Executa ping periódico ao servidor e bloqueia o sistema após falhas consecutivas.
 * Só ativa em terminais Tauri (não em servidores nem em modo browser).
 *
 * @param appReady - Ref que indica se o app terminou o startup
 */
export function useHealthMonitor(appReady: Readonly<import('vue').Ref<boolean>>) {
  const router = useRouter()
  const networkStore = useNetworkConfigStore()

  const falhasConsecutivas = ref(0)
  let intervalId: ReturnType<typeof setInterval> | null = null
  let isTerminal = false

  async function verificarConexao() {
    if (networkStore.erroConexaoTerminal) return

    // Tenta até 2 vezes antes de contar como falha (tolera microcortes de rede)
    let ok = await verificarSaude(5000)
    if (!ok) {
      await new Promise((r) => setTimeout(r, 2000))
      ok = await verificarSaude(5000)
    }

    if (ok) {
      falhasConsecutivas.value = 0
    } else {
      falhasConsecutivas.value++
      if (falhasConsecutivas.value >= MAX_FALHAS_CONSECUTIVAS) {
        networkStore.setErroConexaoTerminal(true)
        try {
          const config = await getConfig()
          networkStore.setConfigAtual(config.server_ip, config.server_port)
        } catch {
          // config já pode estar no store via startup
        }
        router.replace({ name: 'erro-conexao' })
      }
    }
  }

  function iniciarMonitoramento() {
    if (intervalId) return
    falhasConsecutivas.value = 0
    intervalId = setInterval(verificarConexao, INTERVALO_PING_MS)
  }

  function pararMonitoramento() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  async function setup() {
    if (!tauriDisponivel()) return

    try {
      const config = await getConfig()
      isTerminal = config.configured && !config.is_server
    } catch {
      return
    }

    if (!isTerminal) return

    // Aguarda appReady para não conflitar com aguardarBackend do startup
    if (appReady.value) {
      iniciarMonitoramento()
    } else {
      const unwatch = watch(appReady, (ready) => {
        if (ready) {
          unwatch()
          // Só inicia se não entrou em erro no startup
          if (!networkStore.erroConexaoTerminal) {
            iniciarMonitoramento()
          }
        }
      })
    }
  }

  // Quando o erro é limpo (reconexão bem-sucedida), retoma o monitoramento
  watch(
    () => networkStore.erroConexaoTerminal,
    (emErro) => {
      if (!emErro && isTerminal) {
        falhasConsecutivas.value = 0
        iniciarMonitoramento()
      } else if (emErro) {
        pararMonitoramento()
      }
    },
  )

  setup()

  onBeforeUnmount(() => {
    pararMonitoramento()
  })
}
