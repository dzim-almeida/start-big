/**
 * @fileoverview Gerenciamento centralizado da URL do backend.
 * A URL é obtida dinamicamente do Tauri via get_api_url(),
 * com fallback para localhost:8000 em modo desenvolvimento (browser).
 */

import { getApiUrl, tauriDisponivel } from '@/shared/services/system/tauriConfig.service'

let _backendBaseUrl = ''
let _backendApiUrl = ''
let _apiBaseUrl = ''
let _initialized = false

/**
 * Inicializa as URLs do backend. Deve ser chamado UMA VEZ
 * antes de montar o app Vue.
 */
export async function initBackendUrl(): Promise<void> {
  if (_initialized) return

  if (tauriDisponivel()) {
    _backendApiUrl = await getApiUrl() // ex: http://127.0.0.1:8080/api
  } else {
    _backendApiUrl = 'http://127.0.0.1:8000/api'
  }

  _backendBaseUrl = _backendApiUrl.replace(/\/api$/, '') // ex: http://127.0.0.1:8080
  _apiBaseUrl = `${_backendApiUrl}/v1` // ex: http://127.0.0.1:8080/api/v1
  _initialized = true
}

/**
 * Re-inicializa as URLs após troca de configuração (server/client).
 */
export async function reinitBackendUrl(): Promise<void> {
  _initialized = false
  await initBackendUrl()
}

/**
 * Retorna a URL base do backend (ex: http://127.0.0.1:8080)
 * Usada para acessar arquivos estáticos e imagens.
 */
export function getBackendBaseUrl(): string {
  if (!_initialized) {
    console.warn('[backendUrl] acessado antes da inicialização, usando fallback')
    return 'http://127.0.0.1:8000'
  }
  return _backendBaseUrl
}

/**
 * Retorna a URL base da API sem versionamento (ex: http://127.0.0.1:8080/api)
 * Usada para endpoints de infraestrutura como /health.
 */
export function getBackendApiUrl(): string {
  if (!_initialized) {
    console.warn('[backendUrl] acessado antes da inicialização, usando fallback')
    return 'http://127.0.0.1:8000/api'
  }
  return _backendApiUrl
}

/**
 * Retorna a URL base da API versionada (ex: http://127.0.0.1:8080/api/v1)
 * Usada pelo Axios para chamadas de negócio.
 */
export function getApiBaseUrl(): string {
  if (!_initialized) {
    console.warn('[backendUrl] acessado antes da inicialização, usando fallback')
    return 'http://127.0.0.1:8000/api/v1'
  }
  return _apiBaseUrl
}
