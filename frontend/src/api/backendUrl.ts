/**
 * @fileoverview Gerenciamento centralizado da URL do backend.
 * A porta é obtida dinamicamente do Tauri em modo desktop,
 * com fallback para porta 8000 em modo desenvolvimento (browser).
 */

let _backendBaseUrl = '';
let _apiBaseUrl = '';
let _initialized = false;

function isTauri(): boolean {
  return !!(window as any).__TAURI_INTERNALS__;
}

/**
 * Inicializa as URLs do backend. Deve ser chamado UMA VEZ
 * antes de montar o app Vue.
 */
export async function initBackendUrl(): Promise<void> {
  if (_initialized) return;

  let port = 8000;

  if (isTauri()) {
    const { invoke } = await import('@tauri-apps/api/core');
    port = await invoke<number>('get_backend_port');
  }

  _backendBaseUrl = `http://127.0.0.1:${port}`;
  _apiBaseUrl = `${_backendBaseUrl}/api/v1`;
  _initialized = true;
}

/**
 * Retorna a URL base do backend (ex: http://127.0.0.1:54321)
 */
export function getBackendBaseUrl(): string {
  if (!_initialized) {
    console.warn('[backendUrl] acessado antes da inicialização, usando fallback');
    return 'http://127.0.0.1:8000';
  }
  return _backendBaseUrl;
}

/**
 * Retorna a URL base da API (ex: http://127.0.0.1:54321/api/v1)
 */
export function getApiBaseUrl(): string {
  if (!_initialized) {
    console.warn('[backendUrl] acessado antes da inicialização, usando fallback');
    return 'http://127.0.0.1:8000/api/v1';
  }
  return _apiBaseUrl;
}
