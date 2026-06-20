/**
 * @fileoverview Ponte de impressão com o Tauri
 * @description Invoca os commands Rust de impressão (spooler RAW e TCP 9100).
 * Fora do runtime Tauri (navegador), impressaoDisponivel() retorna false e
 * os fluxos caem no window.print() tradicional.
 */

import { invoke, isTauri } from '@tauri-apps/api/core'
import type { ConfigImpressao } from '@/shared/stores/impressao.store'

export interface ImpressoraInfo {
  nome: string
  padrao: boolean
}

export interface ServidorDescoberto {
  nome: string
  ip: string
  porta: number
}

export function impressaoDisponivel(): boolean {
  return isTauri()
}

export async function listarImpressoras(): Promise<ImpressoraInfo[]> {
  return invoke<ImpressoraInfo[]>('listar_impressoras')
}

export async function imprimirRaw(nomeImpressora: string, dados: Uint8Array): Promise<void> {
  return invoke('imprimir_raw', { nomeImpressora, dados: Array.from(dados) })
}

export async function imprimirRede(ip: string, porta: number, dados: Uint8Array): Promise<void> {
  return invoke('imprimir_rede', { ip, porta, dados: Array.from(dados) })
}

export async function descobrirServidoresImpressao(): Promise<ServidorDescoberto[]> {
  return invoke<ServidorDescoberto[]>('descobrir_servidores_impressao')
}

export async function obterIpLocal(): Promise<string> {
  return invoke<string>('obter_ip_local')
}

/**
 * Liga ou desliga o servidor de impressão na LAN conforme a config local.
 * O servidor só faz sentido quando este PC tem a térmica instalada (modo windows).
 */
export async function sincronizarServidorImpressao(config: ConfigImpressao): Promise<void> {
  if (!isTauri()) return
  const deveCompartilhar =
    config.compartilhar_impressora && config.tipo_conexao === 'windows' && !!config.impressora_termica
  if (deveCompartilhar) {
    await invoke('iniciar_servidor_impressao', {
      porta: config.porta_compartilhamento,
      nomeImpressora: config.impressora_termica,
      nomeTerminal: config.nome_terminal,
    })
  } else {
    await invoke('parar_servidor_impressao')
  }
}
