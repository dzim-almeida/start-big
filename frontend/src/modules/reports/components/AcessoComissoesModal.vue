<script setup lang="ts">
/**
 * @fileoverview "Quem pode ver as comissões": o Master marca os cargos que veem
 * as comissões (e o extrato) de toda a equipe.
 *
 * Pensado para a empresa grande, em que o dono deixa a conferência da comissão
 * com um gerente e não quer emprestar a conta dele para isso. A liberação é só
 * de comissões e extrato: ranking, estoque, contador e o faturamento da loja
 * continuam só do Master (o backend garante; ver
 * services/relatorio/acesso_comissoes.py).
 *
 * Marca por CARGO, nunca pelo nome dele: quem decide é o dono, aqui.
 */
import { computed, ref, watch } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import { AlertTriangle, ShieldCheck } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import { useToast } from '@/shared/composables/useToast';
import { getAcessoComissoes, salvarAcessoComissoes } from '../report.service';
import { reportKeys } from '../query.keys';

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ close: [] }>();

const toast = useToast();
const queryClient = useQueryClient();

const { data, isLoading, isError } = useQuery({
  queryKey: reportKeys.acessoComissoes(),
  queryFn: getAcessoComissoes,
  enabled: computed(() => props.isOpen),
});
const cargos = computed(() => data.value?.cargos ?? []);

/** Marcação em edição; só vai para o servidor no "Salvar". */
const marcados = ref<Set<number>>(new Set());
watch(
  [() => props.isOpen, data],
  ([aberto]) => {
    if (aberto) marcados.value = new Set(cargos.value.filter((c) => c.liberado).map((c) => c.id));
  },
  { immediate: true },
);

function alternar(id: number) {
  const novo = new Set(marcados.value);
  if (novo.has(id)) novo.delete(id);
  else novo.add(id);
  marcados.value = novo;
}

const mudou = computed(() =>
  cargos.value.some((c) => c.liberado !== marcados.value.has(c.id)),
);

const { mutate: salvar, isPending } = useMutation({
  mutationFn: () => salvarAcessoComissoes([...marcados.value]),
  onSuccess: (resposta) => {
    queryClient.setQueryData(reportKeys.acessoComissoes(), resposta);
    toast.success('Acesso às comissões atualizado.');
    emit('close');
  },
  onError: () => toast.error('Não foi possível salvar. Tente novamente.'),
});
</script>

<template>
  <BaseModal
    :is-open="props.isOpen"
    title="Quem pode ver as comissões"
    subtitle="Cargos que veem a comissão e o extrato de toda a equipe"
    size="md"
    @close="emit('close')"
  >
    <div v-if="isError" class="p-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl">
      Não foi possível carregar os cargos. Tente novamente.
    </div>

    <div v-else-if="isLoading" class="py-10 text-center text-sm text-slate-400">Carregando…</div>

    <div v-else-if="!cargos.length" class="py-8 text-center text-xs text-slate-400">
      Nenhum cargo cadastrado. Crie os cargos em <strong>Funcionários</strong>.
    </div>

    <div v-else class="space-y-4">
      <p class="text-xs text-slate-500 leading-relaxed">
        Quem estiver num cargo marcado vê <strong class="font-semibold">a comissão e o extrato de todos</strong>
        os funcionários. Ranking, estoque, contador e o faturamento da loja continuam só seus.
      </p>

      <ul class="divide-y divide-slate-100 border border-slate-200 rounded-xl">
        <li v-for="c in cargos" :key="c.id">
          <label class="flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-slate-50">
            <input
              type="checkbox"
              class="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary cursor-pointer"
              :checked="marcados.has(c.id)"
              @change="alternar(c.id)"
            />
            <span class="flex-1">
              <span class="block text-sm font-medium text-slate-700">{{ c.nome }}</span>
              <span
                v-if="marcados.has(c.id) && !c.abre_relatorios"
                class="mt-1 flex items-center gap-1 text-[11px] text-amber-600"
              >
                <AlertTriangle :size="12" class="shrink-0" />
                Este cargo não abre a tela de Relatórios: libere "Relatórios" nas permissões do cargo.
              </span>
            </span>
          </label>
        </li>
      </ul>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <button
          type="button"
          class="h-9 px-4 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:border-slate-300 transition-colors cursor-pointer"
          @click="emit('close')"
        >
          Cancelar
        </button>
        <button
          type="button"
          :disabled="!mudou || isPending"
          class="inline-flex items-center gap-1.5 h-9 px-4 rounded-lg bg-brand-primary text-white text-xs font-semibold hover:bg-brand-primary/90 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          @click="salvar()"
        >
          <ShieldCheck :size="14" /> {{ isPending ? 'Salvando…' : 'Salvar' }}
        </button>
      </div>
    </template>
  </BaseModal>
</template>
