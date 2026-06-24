import { invoke, isTauri } from '@tauri-apps/api/core';

/**
 * Obtém o identificador único da máquina (HWID) via Tauri.
 * Requer runtime Tauri (desktop). Lança erro se chamado fora do Tauri.
 */
export async function getHwid(): Promise<string> {
  if (!isTauri()) {
    throw new Error('HWID só pode ser obtido no runtime Tauri (desktop)');
  }
  return invoke<string>('get_hwid');
}
