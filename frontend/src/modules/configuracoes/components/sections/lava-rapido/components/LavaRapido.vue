<script setup lang="ts">
/**
 * Configurações › Lava-Rápido: os PORTES da loja (Spec 02B, SPEC-00 P2a).
 *
 * Cada lava-rápido divide os veículos do seu jeito (hatch/sedã/SUV, P/M/G,
 * caminhão por eixo). A lista inicial vem do sistema; aqui o dono renomeia,
 * reordena, cria e desativa. Porte nunca é apagado: desativado, some da
 * comanda, mas os preços e os veículos que já o usam continuam legíveis.
 *
 * SALVA SOZINHA, campo a campo (fica em `secoesAutoSave` no modal), como as
 * Formas de recebimento: cada porte é um registro independente.
 *
 * Só aparece no segmento com a capacidade `preco_por_porte`.
 */
import { computed, ref, watch } from 'vue'
import { ArrowDown, ArrowUp, Info, Plus } from 'lucide-vue-next'

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue'
import { useTiposDeTrabalho } from '@/modules/order-service/shared/segmento/useTiposDeTrabalho'
import { usePortesMutations, usePortesQuery } from '@/modules/lava-rapido/shared/composables/usePortes'
import type { Porte } from '@/modules/lava-rapido/shared/schemas/porte.schema'
import { useCapacidades } from '@/modules/order-service/shared/segmento/useCapacidades'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'
import { useConfiguracoesOSQuery } from '@/modules/configuracoes/composables/queries/useConfiguracoesOSQuery'
import { useSalvarConfiguracoesOSMutation } from '@/modules/configuracoes/composables/mutates/useSalvarConfiguracoesOSMutation'

const { opcoes: tiposDeVeiculo } = useTiposDeTrabalho()
const { data: portes, isLoading } = usePortesQuery()
const { criar, atualizar } = usePortesMutations()

/** Tipo de veículo aberto (Carro, Moto, Caminhão...). */
const tipoAtivo = ref('')
watch(
  tiposDeVeiculo,
  (opcoes) => {
    if (!tipoAtivo.value && opcoes.length) tipoAtivo.value = opcoes[0].value
  },
  { immediate: true },
)

/** Portes do tipo: ativos primeiro, na ordem dos botões; desativados no fim. */
const portesDoTipo = computed<Porte[]>(() =>
  (portes.value ?? [])
    .filter((p) => p.tipo_veiculo === tipoAtivo.value)
    .sort((a, b) => Number(b.ativo) - Number(a.ativo) || a.ordem - b.ordem || a.id - b.id),
)
const ativos = computed(() => portesDoTipo.value.filter((p) => p.ativo))

/**
 * Rascunho dos nomes, por id. Não se escreve no cache da query: ele é a
 * verdade do servidor, e a tela mostraria como salvo o que ainda não saiu daqui.
 */
const nomes = ref<Record<number, string>>({})
watch(
  portes,
  (lista) => {
    const n: Record<number, string> = {}
    for (const p of lista ?? []) n[p.id] = p.nome
    nomes.value = n
  },
  { immediate: true },
)

function salvarNome(porte: Porte) {
  const nome = (nomes.value[porte.id] ?? '').trim()
  if (!nome) {                                   // vazio não vale: volta ao gravado
    nomes.value[porte.id] = porte.nome
    return
  }
  if (nome === porte.nome) return
  atualizar.mutate({ id: porte.id, dados: { nome } })
}

function alternarAtivo(porte: Porte) {
  atualizar.mutate({ id: porte.id, dados: { ativo: !porte.ativo } })
}

/** Troca a posição com o vizinho (só entre os ativos, que são os botões). */
function mover(porte: Porte, direcao: -1 | 1) {
  const lista = ativos.value
  const i = lista.findIndex((p) => p.id === porte.id)
  const vizinho = lista[i + direcao]
  if (!vizinho) return
  // Reescreve a ordem dos dois com a posição na lista: a ordem gravada pode
  // ter buracos ou empates (porte novo entra com max+1).
  atualizar.mutate({ id: porte.id, dados: { ordem: i + direcao } })
  atualizar.mutate({ id: vizinho.id, dados: { ordem: i } })
}

// --- Vagas por horário (SPEC-00 O11, 14/11/2026) -------------------------------
// Quantos veículos a loja atende ao mesmo tempo. A agenda AVISA quando um
// horário passa disso, sem travar. 0/vazio = sem limite. Salva sozinha, como
// os portes; o PUT leva só este campo (o backend ignora o que não veio).
const { tem } = useCapacidades()
const configStore = useConfiguracoesStore()
useConfiguracoesOSQuery()
const salvarConfigOS = useSalvarConfiguracoesOSMutation()
const vagas = ref<number | null>(configStore.vagasAgenda || null)
watch(() => configStore.vagasAgenda, (v) => { vagas.value = v || null })
function salvarVagas() {
  const valor = Math.max(0, Math.min(99, Math.round(Number(vagas.value) || 0)))
  vagas.value = valor || null
  if (valor === configStore.vagasAgenda) return
  salvarConfigOS.mutate({ vagas_agenda: valor })
}

const novoNome = ref('')
function adicionar() {
  const nome = novoNome.value.trim()
  if (!nome) return
  criar.mutate(
    { tipo_veiculo: tipoAtivo.value, nome },
    { onSuccess: () => { novoNome.value = '' } },
  )
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-semibold text-gray-800">Portes dos veículos</h3>
      <p class="mt-1 max-w-2xl text-sm text-gray-500">
        O porte decide o preço da lavagem. Ajuste a lista do jeito que a sua loja cobra — os
        preços de cada porte ficam no cadastro de cada serviço.
      </p>
    </div>

    <div class="flex gap-2.5 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3">
      <Info :size="16" class="mt-0.5 shrink-0 text-blue-500" />
      <p class="text-xs text-blue-800">
        Desativar um porte tira ele da comanda, mas não apaga os preços nem os veículos que já
        o usam. As alterações são salvas na hora.
      </p>
    </div>

    <!-- Tipo de veículo -->
    <div class="flex flex-wrap gap-2" role="tablist">
      <button
        v-for="tipo in tiposDeVeiculo"
        :key="tipo.value"
        type="button"
        role="tab"
        :aria-selected="tipoAtivo === tipo.value"
        class="rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors"
        :class="tipoAtivo === tipo.value
          ? 'border-brand-primary bg-brand-primary text-white'
          : 'border-gray-200 bg-white text-gray-600 hover:border-brand-primary hover:text-brand-primary'"
        @click="tipoAtivo = tipo.value"
      >
        {{ tipo.label }}
      </button>
    </div>

    <p v-if="isLoading" class="text-sm text-gray-500">Carregando…</p>

    <ul v-else class="flex flex-col divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white">
      <li
        v-for="porte in portesDoTipo"
        :key="porte.id"
        class="flex flex-wrap items-end gap-3 px-5 py-3"
        :class="!porte.ativo && 'bg-gray-50'"
      >
        <div class="min-w-48 flex-1">
          <BaseInput
            v-model="nomes[porte.id]"
            :label="porte.ativo ? 'Nome do porte' : 'Nome do porte (desativado)'"
            :disabled="!porte.ativo"
            @blur="salvarNome(porte)"
            @keyup.enter="salvarNome(porte)"
          />
        </div>

        <div v-if="porte.ativo" class="flex gap-1 pb-1">
          <button
            type="button"
            class="rounded-lg border border-gray-200 p-2 text-gray-500 hover:text-brand-primary disabled:opacity-30"
            :disabled="ativos[0]?.id === porte.id"
            title="Subir"
            @click="mover(porte, -1)"
          >
            <ArrowUp :size="14" />
          </button>
          <button
            type="button"
            class="rounded-lg border border-gray-200 p-2 text-gray-500 hover:text-brand-primary disabled:opacity-30"
            :disabled="ativos[ativos.length - 1]?.id === porte.id"
            title="Descer"
            @click="mover(porte, 1)"
          >
            <ArrowDown :size="14" />
          </button>
        </div>

        <div class="pb-0.5">
          <BaseButton size="sm" :variant="porte.ativo ? 'ghost-danger' : 'ghost'" @click="alternarAtivo(porte)">
            {{ porte.ativo ? 'Desativar' : 'Reativar' }}
          </BaseButton>
        </div>
      </li>

      <!-- Novo porte -->
      <li class="flex flex-wrap items-end gap-3 px-5 py-3">
        <div class="min-w-48 flex-1">
          <BaseInput
            v-model="novoNome"
            label="Novo porte"
            placeholder="Ex: SUV 7 lugares"
            @keyup.enter="adicionar"
          />
        </div>
        <div class="pb-0.5">
          <BaseButton size="sm" :is-loading="criar.isPending.value" :disabled="!novoNome.trim()" @click="adicionar">
            <Plus :size="14" class="mr-1" /> Adicionar
          </BaseButton>
        </div>
      </li>
    </ul>

    <!-- Vagas da agenda: só com a Agenda ligada -->
    <div v-if="tem('agenda_servicos')" class="flex flex-col gap-2 border-t border-gray-100 pt-6">
      <h3 class="text-base font-semibold text-gray-800">Vagas por horário (Agenda)</h3>
      <p class="max-w-2xl text-sm text-gray-500">
        Quantos veículos a loja consegue atender ao mesmo tempo (boxes, lavadores). Ao agendar
        num horário que já está cheio, a agenda avisa — mas deixa agendar. Deixe em branco
        para não ter limite.
      </p>
      <div class="w-40">
        <BaseInput
          v-model.number="vagas"
          type="number"
          label="Vagas"
          placeholder="Sem limite"
          data-testid="config-vagas-agenda"
          @blur="salvarVagas"
          @keyup.enter="salvarVagas"
        />
      </div>
    </div>
  </div>
</template>
