/**
 * @fileoverview Ponte de configuração com o Tauri
 * @description Invoca os commands Rust de configuração server/client.
 * Fora do runtime Tauri (navegador), tauriDisponivel() retorna false.
 */

import { invoke, isTauri } from '@tauri-apps/api/core'

export interface AppConfig {
  is_server: boolean
  server_ip: string
  server_port: number
  configured: boolean
}

export function tauriDisponivel(): boolean {
  return isTauri()
}

export async function getConfig(): Promise<AppConfig> {
  return invoke<AppConfig>('get_config')
}

export async function getApiUrl(): Promise<string> {
  return invoke<string>('get_api_url')
}

export async function setRoleServer(customPort?: number): Promise<AppConfig> {
  return invoke<AppConfig>('set_role_server', { customPort: customPort ?? null })
}

export async function setRoleClient(serverIp: string, serverPort: number): Promise<AppConfig> {
  return invoke<AppConfig>('set_role_client', { serverIp, serverPort })
}

export async function obterIpLocal(): Promise<string> {
  return invoke<string>('obter_ip_local')
}

export async function isDevMode(): Promise<boolean> {
  return invoke<boolean>('is_dev_mode')
}

export async function iniciarDescobertaServidores(): Promise<void> {
  return invoke<void>('iniciar_descoberta_servidores')
}
