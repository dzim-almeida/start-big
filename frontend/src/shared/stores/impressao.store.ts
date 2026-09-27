/**
 * @fileoverview Store de configuração de impressão
 * @description Configuração LOCAL por PC (a impressora é hardware da máquina):
 * persiste em localStorage, não no backend. Cada caixa/terminal guarda a sua.
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { Bobina } from '@/shared/services/escpos'

export type TipoConexaoImpressora = 'windows' | 'rede'
export type ModoAutoImpressao = 'automatico' | 'perguntar' | 'nao'
export type FormatoDocumento = 'cupom' | 'a4'

export interface ConfigImpressao {
  tipo_conexao: TipoConexaoImpressora
  impressora_termica: string | null
  ip_impressora: string | null
  porta_impressora: number
  bobina: Bobina
  auto_imprimir_venda: ModoAutoImpressao
  auto_imprimir_os: ModoAutoImpressao
  // Documento padrão de cada operação (cupom térmico ou recibo em folha A4)
  formato_venda: FormatoDocumento
  formato_os: FormatoDocumento
  gaveta_ativa: boolean
  abrir_gaveta_na_venda: boolean
  // Servidor de impressão na LAN: este PC compartilha sua térmica com os outros caixas
  compartilhar_impressora: boolean
  porta_compartilhamento: number
  nome_terminal: string
  // Etiquetas (docs/etiquetas-plano.md §6). Calibração é por terminal: cada
  // impressora puxa o papel com a sua folga.
  etiqueta_deslocamento_x_mm: number
  etiqueta_deslocamento_y_mm: number
  /** Chave do último modelo usado na fila (`preset:...` ou `loja:<id>`). */
  etiqueta_modelo: string | null
  /** Idem, para a etiqueta de envio (volume ou DANFE) — papel diferente do estoque. */
  etiqueta_modelo_envio: string | null
}

const STORAGE_KEY = 'startbig-impressao'
// Chave anterior ao rename do produto. Lida uma unica vez na migracao para o caixa
// nao perder a impressora ja configurada ao atualizar.
const STORAGE_KEY_LEGADA = 'bigpdv-impressao'

const CONFIG_PADRAO: ConfigImpressao = {
  tipo_conexao: 'windows',
  impressora_termica: null,
  ip_impressora: null,
  porta_impressora: 9100,
  bobina: '80',
  auto_imprimir_venda: 'automatico',
  auto_imprimir_os: 'automatico',
  formato_venda: 'cupom',
  formato_os: 'cupom',
  gaveta_ativa: false,
  abrir_gaveta_na_venda: true,
  compartilhar_impressora: false,
  porta_compartilhamento: 9100,
  nome_terminal: 'Caixa Principal',
  etiqueta_deslocamento_x_mm: 0,
  etiqueta_deslocamento_y_mm: 0,
  etiqueta_modelo: null,
  etiqueta_modelo_envio: null,
}

export const useImpressaoStore = defineStore('impressao', () => {
  const config = ref<ConfigImpressao>({ ...CONFIG_PADRAO })

  function carregar() {
    try {
      const salvo = localStorage.getItem(STORAGE_KEY) ?? localStorage.getItem(STORAGE_KEY_LEGADA)
      if (salvo) {
        config.value = { ...CONFIG_PADRAO, ...JSON.parse(salvo) }
        // Regrava na chave nova e descarta a antiga.
        localStorage.setItem(STORAGE_KEY, JSON.stringify(config.value))
        localStorage.removeItem(STORAGE_KEY_LEGADA)
      }
    } catch {
      config.value = { ...CONFIG_PADRAO }
    }
  }

  function salvar(novo: ConfigImpressao) {
    config.value = { ...novo }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config.value))
  }

  const impressoraConfigurada = computed(() => {
    if (config.value.tipo_conexao === 'rede') return !!config.value.ip_impressora
    return !!config.value.impressora_termica
  })

  return { config, carregar, salvar, impressoraConfigurada }
})
