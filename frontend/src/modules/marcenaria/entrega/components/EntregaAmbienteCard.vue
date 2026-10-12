<script setup lang="ts">
/**
 * @component EntregaAmbienteCard
 * @description A entrega de UM ambiente na aba Entrega (Spec 13B D3, D7, D8).
 *
 * Mostra a situação, o agendamento, os móveis e os botões "Imprimir termo" e
 * "Registrar entrega" (pendente) ou "Corrigir registro" (registrado). Depois
 * do registro: data, montadores, quem recebeu, o checklist resumido,
 * observações, pendências e fotos. Nenhum preço.
 *
 * Só desenha e avisa o pai: quem grava é a aba.
 */
import { computed, ref } from 'vue';
import { CalendarDays, Camera, CheckCircle2, CheckSquare, Circle, Plus, Printer, Square, Trash2, XSquare } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseStatusPill, { type TomStatus } from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import AmbienteSecao from '@/modules/marcenaria/shared/components/AmbienteSecao.vue';
import { formatDataPura } from '@/shared/utils/date.utils';
import { getImageUrl } from '@/shared/utils/print.utils';

import type { EntregaAmbiente, FotoEntrega, Pendencia, SituacaoEntrega } from '../schemas/entrega.schema';
import {
  nomesDosMontadores, registrada, resumoDoChecklist, ROTULO_SITUACAO_ENTREGA,
  textoDoAgendamento,
} from '../utils/entrega';

const props = defineProps<{
  entrega: EntregaAmbiente;
  /** Posição do ambiente na OS (1, 2, 3…), mostrada como "01". */
  numero: number;
  /** A OS aceita mudanças (13B D10). Pendências valem mesmo fechada. */
  editavel: boolean;
}>();

const emit = defineEmits<{
  imprimirTermo: [];
  registrar: [];
  editarChecklist: [];
  novaPendencia: [];
  resolverPendencia: [pendencia: Pendencia];
  reabrirPendencia: [pendencia: Pendencia];
  enviarFoto: [tipo: 'TERMO' | 'MONTAGEM', arquivo: File];
  excluirFoto: [foto: FotoEntrega];
}>();

const jaRegistrada = computed(() => registrada(props.entrega));
const situacao = computed(() => props.entrega.situacao);
const temNaoOk = computed(() => props.entrega.checklist.some((item) => item.marcacao === 'nao_ok'));

const TOM_SITUACAO: Record<SituacaoEntrega, TomStatus> = { PENDENTE: 'neutro', CONFORME: 'sucesso', COM_RESSALVAS: 'alerta' };

// --- Fotos: dois campos escondidos, um por tipo -------------------------------------
const campoTermo = ref<HTMLInputElement | null>(null);
const campoMontagem = ref<HTMLInputElement | null>(null);

function escolheu(tipo: 'TERMO' | 'MONTAGEM', evento: Event) {
  const campo = evento.target as HTMLInputElement;
  for (const arquivo of campo.files ?? []) emit('enviarFoto', tipo, arquivo);
  campo.value = '';                                    // a mesma foto pode ser escolhida de novo
}
</script>

<template>
  <div :data-testid="`entrega-${entrega.id}`">
    <AmbienteSecao
      :numero="numero"
      :nome="entrega.ambiente"
      :subtitulo="entrega.moveis.map((m) => `${m.nome} (${m.quantidade}×)`).join(' · ')"
      :inativo="!jaRegistrada"
    >
      <template #direita>
        <div class="flex flex-wrap items-center justify-end gap-2">
          <span data-testid="situacao"><BaseStatusPill :tom="TOM_SITUACAO[situacao]">{{ ROTULO_SITUACAO_ENTREGA[situacao] }}</BaseStatusPill></span>
          <BaseButton variant="secondary" size="sm" data-testid="imprimir-termo" @click="emit('imprimirTermo')">
            <Printer :size="14" class="mr-1" /> Imprimir termo
          </BaseButton>
          <BaseButton v-if="editavel" size="sm" :variant="jaRegistrada ? 'secondary' : 'primary'" data-testid="registrar" @click="emit('registrar')">
            {{ jaRegistrada ? 'Corrigir registro' : 'Registrar entrega' }}
          </BaseButton>
        </div>
      </template>

      <!-- Quando: registrada (data, montadores, quem recebeu) ou agendada (D3) -->
      <p class="flex flex-wrap items-center gap-x-1.5 text-sm text-zinc-600">
        <CalendarDays :size="15" class="text-zinc-400" aria-hidden="true" />
        <template v-if="jaRegistrada">
          <span v-if="entrega.data_entrega">entregue em {{ formatDataPura(entrega.data_entrega) }}</span>
          <span v-if="entrega.montadores.length">· {{ nomesDosMontadores(entrega.montadores) }}</span>
          <span v-if="entrega.recebido_por">· recebido por {{ entrega.recebido_por }}</span>
        </template>
        <span v-else-if="entrega.agendamento" data-testid="agendamento-do-ambiente">{{ textoDoAgendamento(entrega.agendamento) }}</span>
        <span v-else class="text-zinc-500">sem instalação agendada</span>
      </p>

      <div class="grid grid-cols-1 gap-5 lg:grid-cols-[22rem_minmax(0,1fr)]">
        <!-- Checklist de vistoria: marcado depois do registro; editável antes (D8) -->
        <div class="flex flex-col gap-3 rounded-xl border border-zinc-100 bg-zinc-50 p-4">
          <div class="flex items-center justify-between gap-2">
            <span class="text-xs font-semibold uppercase tracking-wider text-zinc-600">Checklist de vistoria</span>
            <span v-if="jaRegistrada" class="text-xs font-bold" :class="temNaoOk ? 'text-amber-700' : 'text-emerald-700'" data-testid="resumo-checklist">
              {{ resumoDoChecklist(entrega.checklist) }}
            </span>
            <span v-else class="text-xs text-zinc-500">{{ entrega.checklist.length }} itens</span>
          </div>
          <ul class="flex flex-col gap-2">
            <li
              v-for="(item, i) in entrega.checklist"
              :key="i"
              class="flex items-start gap-2.5 rounded-lg border bg-white px-3 py-2 text-sm"
              :class="item.marcacao === 'nao_ok' ? 'border-amber-200 bg-amber-50' : 'border-zinc-200'"
            >
              <CheckSquare v-if="item.marcacao === 'ok'" :size="16" class="mt-0.5 shrink-0 text-emerald-600" aria-label="ok" />
              <XSquare v-else-if="item.marcacao === 'nao_ok'" :size="16" class="mt-0.5 shrink-0 text-amber-700" aria-label="não ok" />
              <Square v-else :size="16" class="mt-0.5 shrink-0 text-zinc-300" aria-label="sem marcação" />
              <span class="text-zinc-800">{{ item.texto }}</span>
            </li>
          </ul>
          <button
            v-if="editavel && !jaRegistrada"
            type="button"
            class="self-start text-xs font-medium text-brand-primary hover:underline cursor-pointer"
            data-testid="editar-checklist"
            @click="emit('editarChecklist')"
          >
            Editar checklist
          </button>
          <template v-if="entrega.observacoes">
            <span class="text-xs font-semibold uppercase tracking-wider text-zinc-600">Observações</span>
            <p class="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm italic text-zinc-700">{{ entrega.observacoes }}</p>
          </template>
        </div>

        <div class="flex min-w-0 flex-col gap-5">
          <!-- Pendências (D7): resolver, reabrir e "+ Pendência" mesmo com a OS finalizada -->
          <div v-if="jaRegistrada" class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold uppercase tracking-wider text-zinc-600">Pendências</span>
              <button type="button" class="inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline cursor-pointer" data-testid="nova-pendencia" @click="emit('novaPendencia')">
                <Plus :size="12" /> Pendência
              </button>
            </div>
            <p v-if="!entrega.pendencias.length" class="text-sm text-zinc-500">Nenhuma pendência.</p>
            <ul class="flex flex-col gap-2">
              <li
                v-for="p in entrega.pendencias"
                :key="p.id"
                class="flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm"
                :class="p.situacao === 'RESOLVIDA' ? 'border-zinc-200 bg-white' : 'border-amber-200 bg-amber-50'"
                :data-testid="`pendencia-${p.id}`"
              >
                <span class="flex min-w-0 items-start gap-2">
                  <CheckCircle2 v-if="p.situacao === 'RESOLVIDA'" :size="16" class="mt-0.5 shrink-0 text-emerald-600" />
                  <Circle v-else :size="16" class="mt-0.5 shrink-0 text-amber-600" />
                  <span>
                    <span :class="p.situacao === 'RESOLVIDA' ? 'text-zinc-500 line-through' : 'font-medium text-amber-900'">{{ p.descricao }}</span>
                    <span v-if="p.resolucao" class="block text-xs text-zinc-500">{{ p.resolucao }}<template v-if="p.resolvida_em"> ({{ formatDataPura(p.resolvida_em) }})</template></span>
                  </span>
                </span>
                <BaseButton
                  v-if="p.situacao === 'ABERTA'"
                  variant="ghost"
                  size="sm"
                  :data-testid="`resolver-${p.id}`"
                  @click="emit('resolverPendencia', p)"
                >
                  Resolver
                </BaseButton>
                <button
                  v-else
                  type="button"
                  class="text-xs font-medium text-zinc-500 hover:underline cursor-pointer"
                  :data-testid="`reabrir-${p.id}`"
                  @click="emit('reabrirPendencia', p)"
                >
                  Reabrir
                </button>
              </li>
            </ul>
          </div>

          <!-- Fotos: termo assinado e montagem (13A D7) -->
          <div v-if="entrega.fotos.length || editavel" class="flex flex-col gap-2" data-testid="fotos">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-xs font-semibold uppercase tracking-wider text-zinc-600">Fotos ({{ entrega.fotos.length }})</span>
              <div v-if="editavel" class="flex gap-3">
                <button type="button" class="inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline cursor-pointer" @click="campoTermo?.click()">
                  <Plus :size="12" /> Termo assinado
                </button>
                <button type="button" class="inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline cursor-pointer" @click="campoMontagem?.click()">
                  <Camera :size="12" /> Foto da montagem
                </button>
                <input ref="campoTermo" type="file" accept="image/*" class="hidden" data-testid="campo-foto-termo" @change="escolheu('TERMO', $event)" />
                <input ref="campoMontagem" type="file" accept="image/*" multiple class="hidden" data-testid="campo-foto-montagem" @change="escolheu('MONTAGEM', $event)" />
              </div>
            </div>
            <p v-if="!entrega.fotos.length" class="text-sm text-zinc-500">Nenhuma foto ainda.</p>
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
              <figure v-for="foto in entrega.fotos" :key="foto.id" class="group relative m-0 overflow-hidden rounded-xl border border-zinc-200 bg-white">
                <a :href="getImageUrl(foto.url) ?? '#'" target="_blank" rel="noopener" :title="foto.tipo === 'TERMO' ? 'Termo assinado' : 'Montagem'">
                  <img :src="getImageUrl(foto.url) ?? ''" :alt="foto.tipo === 'TERMO' ? 'Termo assinado' : 'Montagem'" class="h-32 w-full object-cover" />
                </a>
                <figcaption class="flex items-center justify-between gap-2 px-3 py-2">
                  <span class="truncate text-xs text-zinc-600">{{ foto.tipo === 'TERMO' ? 'Termo assinado' : 'Montagem' }}</span>
                  <BaseStatusPill v-if="foto.tipo === 'TERMO'" tom="info">Termo</BaseStatusPill>
                </figcaption>
                <button
                  v-if="editavel"
                  type="button"
                  class="absolute right-2 top-2 hidden h-7 w-7 items-center justify-center rounded-full bg-white text-red-600 shadow group-hover:flex cursor-pointer"
                  aria-label="Excluir foto"
                  :data-testid="`excluir-foto-${foto.id}`"
                  @click="emit('excluirFoto', foto)"
                >
                  <Trash2 :size="14" />
                </button>
              </figure>
            </div>
          </div>
        </div>
      </div>
    </AmbienteSecao>
  </div>
</template>
