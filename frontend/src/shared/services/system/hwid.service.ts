/**
 * @fileoverview Serviço de obtenção do HWID do terminal.
 * @description Invoca o command Rust para ler o identificador único da máquina.
 * Fora do runtime Tauri (navegador), retorna um HWID fixo de desenvolvimento.
 */

import { invoke, isTauri } from '@tauri-apps/api/core'

let _cachedHwid: string | null = null

/**
 * Retorna o Hardware ID da máquina atual.
 * Resultado é cacheado em memória (imutável durante a sessão).
 *
 * - Tauri: lê MachineGuid (Windows) ou /etc/machine-id (Linux) via Rust.
 * - Browser (dev): retorna string fixa "dev-browser-hwid".
 */
export async function obterHwid(): Promise<string> {
  if (_cachedHwid) return _cachedHwid

  if (isTauri()) {
    _cachedHwid = await invoke<string>('obter_hwid')
  } else {
    _cachedHwid = 'dev-browser-hwid'
  }

  return _cachedHwid
}
