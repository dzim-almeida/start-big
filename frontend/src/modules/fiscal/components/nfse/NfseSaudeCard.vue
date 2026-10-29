<script setup lang="ts">
/**
 * @component NfseSaudeCard
 * @description "Saúde Fiscal" da aba NFS-e: a mesma barra da aba NF-e, com o
 * que falta para a NFS-e sair (empresa, rota, certificado, serviços).
 *
 * Pedido do Alan na revisão de 29/10/2026 (docs/nfse-melhorias-plano.md, M4).
 * Só leitura; o popover diz o que fazer e leva à tela dos serviços.
 */
import { computed, ref } from 'vue';
import { Activity, CheckCircle2, XCircle } from 'lucide-vue-next';
import { useRouter } from 'vue-router';

import { useNfseSaudeQuery } from '../../composables/useNfse';

const { data: saude } = useNfseSaudeQuery();
const router = useRouter();
const aberto = ref(false);

const percentual = computed(() => saude.value?.percentual ?? 0);
const pendencias = computed(() => saude.value?.pendencias ?? 0);

const corBarra = computed(() => {
  if (percentual.value === 100) return 'bg-emerald-500';
  if (percentual.value >= 75) return 'bg-emerald-400';
  if (percentual.value >= 50) return 'bg-amber-400';
  return 'bg-red-500';
});

const corTexto = computed(() => {
  if (percentual.value === 100) return 'text-emerald-600';
  if (percentual.value >= 50) return 'text-amber-600';
  return 'text-red-600';
});

function abrirServicos() {
  aberto.value = false;
  router.push('/servicos');
}
</script>

<template>
  <div class="relative">
    <button
      type="button"
      class="flex items-center gap-3 px-4 py-2 rounded-xl border border-zinc-200 bg-white hover:border-zinc-300 hover:shadow-sm transition-all cursor-pointer"
      data-nfse-saude
      @click="aberto = !aberto"
    >
      <Activity :size="16" :class="corTexto" />
      <div class="flex flex-col items-start">
        <span class="text-xs font-semibold text-zinc-700 leading-none">Saúde Fiscal</span>
        <div class="flex items-center gap-2 mt-1">
          <div class="w-16 h-1.5 rounded-full bg-zinc-100 overflow-hidden">
            <div
              :class="['h-full rounded-full transition-all duration-700', corBarra]"
              :style="{ width: percentual + '%' }"
            />
          </div>
          <span :class="['text-[10px] font-bold tabular-nums', corTexto]">{{ percentual }}%</span>
        </div>
      </div>
      <span
        v-if="pendencias > 0"
        class="inline-flex items-center justify-center min-w-5 h-5 px-1.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700"
      >
        {{ pendencias }}
      </span>
    </button>

    <Transition name="popover">
      <div
        v-if="aberto && saude"
        class="absolute right-0 top-full mt-2 z-50 w-85 max-h-120 overflow-y-auto rounded-2xl shadow-xl border border-zinc-200 bg-white p-4 space-y-3"
      >
        <p class="text-sm font-semibold text-zinc-800">O que a NFS-e precisa</p>
        <div v-for="item in saude.itens" :key="item.chave" class="flex items-start gap-2">
          <CheckCircle2 v-if="item.ok" :size="16" class="mt-0.5 shrink-0 text-emerald-500" />
          <XCircle v-else :size="16" class="mt-0.5 shrink-0 text-red-500" />
          <div class="min-w-0">
            <p class="text-xs font-semibold text-zinc-700">{{ item.titulo }}</p>
            <p class="text-xs text-zinc-500">{{ item.detalhe }}</p>

            <ul v-if="item.servicos?.length" class="mt-1.5 space-y-0.5">
              <li v-for="s in item.servicos" :key="s.id" class="text-[11px] text-zinc-600 truncate" :title="`${s.nome}: falta ${s.falta}`">
                • {{ s.nome }} <span class="text-zinc-400">— falta {{ s.falta }}</span>
              </li>
              <li v-if="(item.total_faltando ?? 0) > item.servicos.length" class="text-[11px] text-zinc-400">
                e mais {{ (item.total_faltando ?? 0) - item.servicos.length }}…
              </li>
            </ul>
            <button
              v-if="item.chave === 'servicos' && !item.ok"
              type="button"
              class="mt-1.5 text-xs font-semibold text-brand-primary hover:underline"
              @click="abrirServicos"
            >
              Abrir o cadastro de serviços
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <div v-if="aberto" class="fixed inset-0 z-40" @click="aberto = false" />
  </div>
</template>
