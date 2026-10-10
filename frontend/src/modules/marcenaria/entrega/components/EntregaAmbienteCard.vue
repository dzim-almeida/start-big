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
import { CheckCircle2, Circle, Plus, Trash2 } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatDataPura } from '@/shared/utils/date.utils';
import { getImageUrl } from '@/shared/utils/print.utils';

import type { EntregaAmbiente, FotoEntrega, Pendencia } from '../schemas/entrega.schema';
import {
  CLASSE_SITUACAO_ENTREGA, nomesDosMontadores, registrada, resumoDoChecklist, ROTULO_SITUACAO_ENTREGA,
  textoDoAgendamento,
} from '../utils/entrega';

const props = defineProps<{
  entrega: EntregaAmbiente;
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
  <section class="rounded-xl border border-zinc-200 bg-white px-4 py-3" :data-testid="`entrega-${entrega.id}`">
    <!-- Cabeçalho: ambiente, situação e o agendamento (D3) -->
    <div class="flex flex-wrap items-start justify-between gap-2">
      <div>
        <p class="text-sm font-bold uppercase tracking-wide text-zinc-800">{{ entrega.ambiente }}</p>
        <div class="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-600">
          <span class="rounded-full border px-2 py-0.5 font-medium" :class="CLASSE_SITUACAO_ENTREGA[situacao]" data-testid="situacao">
            {{ ROTULO_SITUACAO_ENTREGA[situacao] }}
          </span>
          <template v-if="jaRegistrada">
            <span v-if="entrega.data_entrega">entregue em {{ formatDataPura(entrega.data_entrega) }}</span>
            <span v-if="entrega.montadores.length">· {{ nomesDosMontadores(entrega.montadores) }}</span>
            <span v-if="entrega.recebido_por">· recebido por {{ entrega.recebido_por }}</span>
          </template>
          <span v-else-if="entrega.agendamento" data-testid="agendamento-do-ambiente">{{ textoDoAgendamento(entrega.agendamento) }}</span>
          <span v-else class="text-zinc-400">sem instalação agendada</span>
        </div>
      </div>
      <div class="flex flex-wrap gap-2">
        <BaseButton variant="secondary" size="sm" data-testid="imprimir-termo" @click="emit('imprimirTermo')">Imprimir termo</BaseButton>
        <BaseButton v-if="editavel" size="sm" :variant="jaRegistrada ? 'secondary' : 'primary'" data-testid="registrar" @click="emit('registrar')">
          {{ jaRegistrada ? 'Corrigir registro' : 'Registrar entrega' }}
        </BaseButton>
      </div>
    </div>

    <!-- Os móveis do ambiente -->
    <p class="mt-2 text-xs text-zinc-500">
      {{ entrega.moveis.map((m) => `${m.nome} (${m.quantidade}×)`).join(' · ') }}
    </p>

    <!-- Checklist: resumo depois do registro; editável antes (D8) -->
    <div class="mt-2 flex flex-wrap items-center gap-3 text-sm text-zinc-700">
      <span>
        Checklist:
        <template v-if="jaRegistrada"><span data-testid="resumo-checklist">{{ resumoDoChecklist(entrega.checklist) }}</span></template>
        <template v-else>{{ entrega.checklist.length }} itens</template>
      </span>
      <button
        v-if="editavel && !jaRegistrada"
        type="button"
        class="text-xs font-medium text-brand-primary hover:underline cursor-pointer"
        data-testid="editar-checklist"
        @click="emit('editarChecklist')"
      >
        Editar checklist
      </button>
    </div>
    <p v-if="entrega.observacoes" class="mt-1 text-sm text-zinc-600">Observações: {{ entrega.observacoes }}</p>

    <!-- Fotos: termo assinado e montagem (13A D7) -->
    <div v-if="entrega.fotos.length || editavel" class="mt-2 flex flex-wrap items-center gap-2" data-testid="fotos">
      <span class="text-sm text-zinc-700">Fotos:</span>
      <div v-for="foto in entrega.fotos" :key="foto.id" class="group relative">
        <a :href="getImageUrl(foto.url) ?? '#'" target="_blank" rel="noopener" :title="foto.tipo === 'TERMO' ? 'Termo assinado' : 'Montagem'">
          <img :src="getImageUrl(foto.url) ?? ''" :alt="foto.tipo === 'TERMO' ? 'Termo assinado' : 'Montagem'" class="h-12 w-12 rounded-lg border border-zinc-200 object-cover" />
          <span v-if="foto.tipo === 'TERMO'" class="absolute bottom-0 left-0 right-0 rounded-b-lg bg-black/60 text-center text-[9px] font-bold text-white">TERMO</span>
        </a>
        <button
          v-if="editavel"
          type="button"
          class="absolute -right-1.5 -top-1.5 hidden h-5 w-5 items-center justify-center rounded-full bg-white text-red-600 shadow group-hover:flex cursor-pointer"
          aria-label="Excluir foto"
          :data-testid="`excluir-foto-${foto.id}`"
          @click="emit('excluirFoto', foto)"
        >
          <Trash2 :size="12" />
        </button>
      </div>
      <template v-if="editavel">
        <button type="button" class="inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline cursor-pointer" @click="campoTermo?.click()">
          <Plus :size="12" /> Termo
        </button>
        <button type="button" class="inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline cursor-pointer" @click="campoMontagem?.click()">
          <Plus :size="12" /> Montagem
        </button>
        <input ref="campoTermo" type="file" accept="image/*" class="hidden" data-testid="campo-foto-termo" @change="escolheu('TERMO', $event)" />
        <input ref="campoMontagem" type="file" accept="image/*" multiple class="hidden" data-testid="campo-foto-montagem" @change="escolheu('MONTAGEM', $event)" />
      </template>
    </div>

    <!-- Pendências (D7): resolver, reabrir e "+ Pendência" mesmo com a OS finalizada -->
    <div v-if="jaRegistrada" class="mt-2">
      <ul class="flex flex-col gap-1">
        <li v-for="p in entrega.pendencias" :key="p.id" class="flex flex-wrap items-center gap-2 text-sm" :data-testid="`pendencia-${p.id}`">
          <CheckCircle2 v-if="p.situacao === 'RESOLVIDA'" :size="14" class="text-emerald-600" />
          <Circle v-else :size="14" class="text-amber-600" />
          <span :class="p.situacao === 'RESOLVIDA' ? 'text-zinc-400 line-through' : 'text-zinc-800'">{{ p.descricao }}</span>
          <span v-if="p.resolucao" class="text-xs text-zinc-500">— {{ p.resolucao }}<template v-if="p.resolvida_em"> ({{ formatDataPura(p.resolvida_em) }})</template></span>
          <button
            v-if="p.situacao === 'ABERTA'"
            type="button"
            class="text-xs font-medium text-brand-primary hover:underline cursor-pointer"
            :data-testid="`resolver-${p.id}`"
            @click="emit('resolverPendencia', p)"
          >
            Resolver
          </button>
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
      <button type="button" class="mt-1 inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline cursor-pointer" data-testid="nova-pendencia" @click="emit('novaPendencia')">
        <Plus :size="12" /> Pendência
      </button>
    </div>
  </section>
</template>
