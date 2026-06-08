import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { OrderServiceReadDataType } from '@/modules/order-service/ordens/schemas/orderServiceQuery.schema'
import type { Comunicado } from '@/modules/mainLayout/services/comunicado.service'

export const useNotificacoesStore = defineStore('notificacoes', () => {
  const osAbandono = ref<OrderServiceReadDataType[]>([])
  const osAtrasadas = ref<OrderServiceReadDataType[]>([])
  const comunicados = ref<Comunicado[]>([])
  const osVistos = ref<Set<number>>(new Set())

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
