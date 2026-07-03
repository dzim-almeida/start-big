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
