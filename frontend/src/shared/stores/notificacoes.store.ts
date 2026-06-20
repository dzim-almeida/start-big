import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { OrderServiceReadDataType } from '@/modules/order-service/ordens/schemas/orderServiceQuery.schema'
import type { Comunicado } from '@/modules/mainLayout/services/comunicado.service'

const STORAGE_KEY = 'notif_os_vistos'

function carregarVistos(): Set<number> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? new Set<number>(JSON.parse(raw)) : new Set()
  } catch {
    return new Set()
  }
}

export const useNotificacoesStore = defineStore('notificacoes', () => {
  const osAbandono = ref<OrderServiceReadDataType[]>([])
  const osAtrasadas = ref<OrderServiceReadDataType[]>([])
  const comunicados = ref<Comunicado[]>([])
  const osVistos = ref<Set<number>>(carregarVistos())

  watch(osVistos, (val) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...val]))
  })

  const totalNaoLidas = computed(() => {
    const alertas = [
      ...osAbandono.value,
      ...osAtrasadas.value,
    ].filter(os => !osVistos.value.has(os.id)).length
    const avisos = comunicados.value.filter(c => !c.lido).length
    return alertas + avisos
  })

  const temOsNaoVistas = computed(() =>
    osAbandono.value.some(os => !osVistos.value.has(os.id)) ||
    osAtrasadas.value.some(os => !osVistos.value.has(os.id))
  )

  function setOsAbandono(lista: OrderServiceReadDataType[]) {
    osAbandono.value = lista
  }

  function setOsAtrasadas(lista: OrderServiceReadDataType[]) {
    osAtrasadas.value = lista
  }

  function setComunicados(lista: Comunicado[]) {
    comunicados.value = lista
  }

  function marcarComunicadoLido(id: number) {
    const c = comunicados.value.find(x => x.id === id)
    if (c) c.lido = true
  }

  function adicionarComunicado(c: Comunicado) {
    comunicados.value.unshift(c)
  }

  function marcarOsVistas() {
    const novos = new Set(osVistos.value)
    osAbandono.value.forEach(os => novos.add(os.id))
    osAtrasadas.value.forEach(os => novos.add(os.id))
    osVistos.value = novos
  }

  function resetar() {
    osAbandono.value = []
    osAtrasadas.value = []
    comunicados.value = []
    osVistos.value = new Set()
    localStorage.removeItem(STORAGE_KEY)
  }

  return {
    osAbandono,
    osAtrasadas,
    comunicados,
    osVistos,
    totalNaoLidas,
    temOsNaoVistas,
    setOsAbandono,
    setOsAtrasadas,
    setComunicados,
    marcarComunicadoLido,
    adicionarComunicado,
    marcarOsVistas,
    resetar,
  }
})
