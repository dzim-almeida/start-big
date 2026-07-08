/**
 * @fileoverview Health check do backend
 * @description Verifica conectividade com o backend via GET /api/health.
 * Usa axios puro (sem interceptors de auth).
 */

import axios from 'axios'
import { getBackendApiUrl } from '@/api/backendUrl'

export async function verificarSaude(timeoutMs = 5000): Promise<boolean> {
  try {
    const { data } = await axios.get(`${getBackendApiUrl()}/health`, { timeout: timeoutMs })
    return data.status === 'ok'
  } catch {
    return false
  }
}

/**
 * Aguarda o backend ficar disponível com retries e backoff.
 * - Servidor (sidecar local): até 10 tentativas (~15s) — precisa de tempo para bootar.
 * - Terminal (servidor remoto): até 3 tentativas (~5s) — se está offline, não vale esperar.
 */
export async function aguardarBackend(isServer: boolean): Promise<boolean> {
  const maxTentativas = isServer ? 10 : 3
  let intervaloMs = isServer ? 1000 : 1500

  for (let i = 0; i < maxTentativas; i++) {
    if (await verificarSaude(3000)) return true
    await new Promise((r) => setTimeout(r, intervaloMs))
    if (isServer) intervaloMs = Math.min(intervaloMs * 1.5, 5000)
  }
  return false
}
