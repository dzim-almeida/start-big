<script setup lang="ts">
/**
 * @component Marcenaria
 * @description Configurações › Marcenaria (Spec 04B): os valores padrão que
 * todo orçamento novo copia — markup, perda, custo/hora, RT, prazos — e as
 * listas de etapas de produção e de checklist de vistoria.
 *
 * Como as outras seções, ela só MOSTRA e expõe `form`/`isDirty`/`resetar`;
 * quem salva é o modal de Configurações. Duas permissões mudam a tela:
 *   - sem `view_custos_marcenaria`, o bloco de custos nem existe (a API nem
 *     manda esses campos) e aparece uma frase no lugar (D8);
 *   - sem `manage_custos_marcenaria` (e sem ser master), tudo fica somente
 *     leitura e o modal não oferece "Salvar" (D9).
 */
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';

import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { useCheckPermission } from '@/modules/mainLayout/composables/useCheckPermission';
import { PERMISSIONS } from '@/shared/constants/permissions.constants';
import { useAuthStore } from '@/shared/stores/auth.store';
import { formatCurrency } from '@/shared/utils/finance';

import { useConfiguracaoMarcenariaQuery } from '../../../../composables/queries/useConfiguracaoMarcenariaQuery';
import {
  LIMITES_LISTA,
  errosDoFormulario,
  paraApi,
  paraTela,
  type FormMarcenaria,
} from '../marcenariaForm';
import ListaTextosEditavel from '@/shared/components/ui/ListaTextosEditavel/ListaTextosEditavel.vue';

const { data, isPending, isError, refetch } = useConfiguracaoMarcenariaQuery();

// Quem pode alterar: master ou a permissão de gerir (manage implica view).
const { userData } = storeToRefs(useAuthStore());
const { hasPermission } = useCheckPermission();
const podeGerir = computed(
  () => userData.value?.is_master === true || hasPermission(PERMISSIONS.manageCustosMarcenaria),
);

/** O formulário da tela (% e R$). Vazio até a API responder. */
const form = ref<FormMarcenaria | null>(null);

/** Volta ao que está salvo (também usado pelo "Descartar" do modal). */
function resetar() {
  form.value = data.value ? paraTela(data.value) : null;
}

// Preenche (e repreenche, depois de salvar) quando a resposta chega.
watch(data, resetar, { immediate: true });

/** Mudou algo em relação ao que está salvo? */
const isDirty = computed(
  () => !!form.value && !!data.value && JSON.stringify(form.value) !== JSON.stringify(paraTela(data.value)),
);

/** Erros com as mesmas regras e mensagens do backend (Spec 04A §4.1). */
const erros = computed(() => (form.value ? errosDoFormulario(form.value) : {}));

/** O bloco de custos só existe para quem vê custo (a API manda `inclui_custos`). */
const mostraCustos = computed(() => form.value?.markup_percentual !== undefined);

// --- Exemplos numéricos ao lado de cada parâmetro (D11) ---------------------
const exemploMarkup = computed(() => {
  const markup = form.value?.markup_percentual ?? 0;
  const custoCentavos = 10000;                                          // R$ 100,00 (formatCurrency recebe centavos)
  const precoCentavos = Math.round(custoCentavos * (1 + markup / 100)); // custo + markup
  return `Custo de ${formatCurrency(custoCentavos)} → preço de ${formatCurrency(precoCentavos)} com ${markup.toLocaleString('pt-BR')}%.`;
});
const exemploPerda = computed(() => {
  const perda = form.value?.perda_percentual ?? 0;
  const chapas = 1 + perda / 100;                        // 1 chapa + a perda do corte
  return `1 chapa no projeto → ${chapas.toLocaleString('pt-BR', { maximumFractionDigits: 3 })} chapa no custo com ${perda.toLocaleString('pt-BR')}%.`;
});

defineExpose({ form, isDirty, resetar, paraApi, podeGerir, erros });

/** Classes do campo numérico, iguais às das outras seções. */
const CLASSE_NUMERO =
  'mt-1 w-28 border border-zinc-200 rounded-lg px-3 py-2 text-sm text-zinc-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-primary/30 focus:border-brand-primary disabled:bg-zinc-50 disabled:text-zinc-500';
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Marcenaria</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Valores padrão que todo orçamento novo copia</p>
    </div>

    <!-- Carregando / erro -->
    <p v-if="isPending" class="text-sm text-zinc-400 animate-pulse">Carregando parâmetros…</p>
    <div v-else-if="isError" class="flex flex-col items-start gap-2">
      <p class="text-sm text-red-600">Não foi possível carregar os parâmetros da marcenaria.</p>
      <button type="button" class="text-xs font-medium text-brand-primary hover:underline" @click="refetch()">
        Tentar de novo
      </button>
    </div>

    <template v-else-if="form">
      <!-- Somente leitura sem a permissão de alterar (D9). -->
      <p v-if="!podeGerir" class="text-xs text-zinc-500 bg-zinc-50 border border-zinc-200 rounded-lg px-3 py-2" data-testid="somente-leitura">
        Só quem tem a permissão de alterar os parâmetros da marcenaria pode editar.
      </p>

      <!-- PREÇO E CUSTOS (só para quem vê custo; D8) -->
      <div v-if="mostraCustos" class="flex flex-col" data-testid="bloco-custos">
        <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Preço e custos</p>

        <div class="py-3 border-b border-zinc-100">
          <label class="text-xs font-medium text-zinc-600">Markup padrão (%)</label>
          <p class="text-[11px] text-zinc-400 mt-0.5">{{ exemploMarkup }}</p>
          <input v-model.number="form.markup_percentual" type="number" min="0" max="1000" step="0.01" :disabled="!podeGerir" :class="CLASSE_NUMERO" />
          <span class="ml-2 text-xs text-zinc-400">%</span>
          <p v-if="erros.markup_percentual" class="text-[11px] text-red-600 mt-1">{{ erros.markup_percentual }}</p>
        </div>

        <div class="py-3 border-b border-zinc-100">
          <label class="text-xs font-medium text-zinc-600">Perda padrão (%)</label>
          <p class="text-[11px] text-zinc-400 mt-0.5">{{ exemploPerda }} Vale para os produtos marcados com "Sofre perda".</p>
          <input v-model.number="form.perda_percentual" type="number" min="0" max="50" step="0.01" :disabled="!podeGerir" :class="CLASSE_NUMERO" />
          <span class="ml-2 text-xs text-zinc-400">%</span>
          <p v-if="erros.perda_percentual" class="text-[11px] text-red-600 mt-1">{{ erros.perda_percentual }}</p>
        </div>

        <div class="py-3 border-b border-zinc-100">
          <label class="text-xs font-medium text-zinc-600">Custo da mão de obra por hora</label>
          <p class="text-[11px] text-zinc-400 mt-0.5 mb-2">Usado quando a mão de obra do móvel é calculada por horas.</p>
          <div class="w-36">
            <BaseMoneyInput v-model="form.custo_hora_reais" :disabled="!podeGerir" />
          </div>
          <!-- R$ 0,00: a mão de obra por horas sai zerada (D12). -->
          <p v-if="!form.custo_hora_reais" class="text-[11px] text-amber-700 mt-1" data-testid="aviso-custo-hora">
            Sem custo por hora, a mão de obra calculada por horas sai zerada nos orçamentos.
          </p>
          <p v-if="erros.custo_hora_reais" class="text-[11px] text-red-600 mt-1">{{ erros.custo_hora_reais }}</p>
        </div>

        <div class="py-3 border-b border-zinc-100">
          <label class="text-xs font-medium text-zinc-600">RT padrão do arquiteto (%)</label>
          <p class="text-[11px] text-zinc-400 mt-0.5">Reserva técnica paga ao arquiteto que indicou o cliente. Pode ser trocada em cada orçamento.</p>
          <input v-model.number="form.rt_percentual" type="number" min="0" max="30" step="0.01" :disabled="!podeGerir" :class="CLASSE_NUMERO" />
          <span class="ml-2 text-xs text-zinc-400">%</span>
          <p v-if="erros.rt_percentual" class="text-[11px] text-red-600 mt-1">{{ erros.rt_percentual }}</p>
        </div>

        <!-- Modo do RT: o rótulo técnico sozinho não diz o efeito (D13). -->
        <fieldset class="py-3 border-b border-zinc-100">
          <legend class="text-xs font-medium text-zinc-600">Como o RT entra no orçamento</legend>
          <label class="mt-2 flex items-start gap-2 cursor-pointer">
            <input v-model="form.rt_modo" type="radio" value="MARGEM" :disabled="!podeGerir" class="mt-0.5 accent-brand-primary" />
            <span>
              <span class="text-xs font-medium text-zinc-700">Sai da margem</span>
              <span class="block text-[11px] text-zinc-400">O preço não muda: a marcenaria paga o arquiteto com o próprio lucro.</span>
            </span>
          </label>
          <label class="mt-2 flex items-start gap-2 cursor-pointer">
            <input v-model="form.rt_modo" type="radio" value="PRECO" :disabled="!podeGerir" class="mt-0.5 accent-brand-primary" />
            <span>
              <span class="text-xs font-medium text-zinc-700">Embutido no preço</span>
              <span class="block text-[11px] text-zinc-400">O preço sobe para cobrir o RT.</span>
            </span>
          </label>
        </fieldset>

        <!-- Prazo para pagar o RT (Spec 09B D11) -->
        <div class="py-3 border-b border-zinc-100">
          <label class="text-xs font-medium text-zinc-600">Prazo para pagar o RT (dias após finalizar a OS)</label>
          <p class="text-[11px] text-zinc-400 mt-0.5">A conta a pagar do arquiteto nasce quando a OS é finalizada e vence depois deste prazo.</p>
          <input v-model.number="form.rt_vencimento_dias" type="number" min="0" max="180" :disabled="!podeGerir" :class="CLASSE_NUMERO" data-testid="rt-vencimento" />
          <span class="ml-2 text-xs text-zinc-400">dias</span>
          <p v-if="erros.rt_vencimento_dias" class="text-[11px] text-red-600 mt-1">{{ erros.rt_vencimento_dias }}</p>
        </div>
      </div>
      <!-- Sem view_custos_marcenaria: a API nem manda os custos (D8). -->
      <p v-else class="text-xs text-zinc-500" data-testid="custos-ocultos">
        Os custos e margens estão ocultos para o seu perfil.
      </p>

      <!-- PRAZOS -->
      <div class="flex flex-col">
        <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Prazos</p>
        <div class="py-3 border-b border-zinc-100">
          <label class="text-xs font-medium text-zinc-600">Validade do orçamento</label>
          <input v-model.number="form.validade_dias" type="number" min="1" max="365" :disabled="!podeGerir" :class="CLASSE_NUMERO" />
          <span class="ml-2 text-xs text-zinc-400">dias</span>
          <p v-if="erros.validade_dias" class="text-[11px] text-red-600 mt-1">{{ erros.validade_dias }}</p>
        </div>
        <div class="py-3 border-b border-zinc-100">
          <label class="text-xs font-medium text-zinc-600">Prazo de entrega padrão</label>
          <p class="text-[11px] text-zinc-400 mt-0.5">Contado da aprovação do orçamento.</p>
          <input v-model.number="form.prazo_entrega_dias" type="number" min="1" max="365" :disabled="!podeGerir" :class="CLASSE_NUMERO" />
          <span class="ml-2 text-xs text-zinc-400">dias</span>
          <p v-if="erros.prazo_entrega_dias" class="text-[11px] text-red-600 mt-1">{{ erros.prazo_entrega_dias }}</p>
        </div>
      </div>

      <!-- Cada OS copia as listas: mudar aqui não altera as que já existem (D15). -->
      <p class="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
        Mudanças valem para os próximos orçamentos e OS. As que já existem mantêm as etapas e o checklist que receberam.
      </p>

      <div class="flex flex-col">
        <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Etapas de produção</p>
        <ListaTextosEditavel
          v-model="form.etapas_producao"
          :max-itens="LIMITES_LISTA.etapas.maxItens"
          :max-caracteres="LIMITES_LISTA.etapas.maxCaracteres"
          rotulo-item="etapa"
          :disabled="!podeGerir"
        />
        <p v-if="erros.etapas_producao" class="text-[11px] text-red-600 mt-1">{{ erros.etapas_producao }}</p>
      </div>

      <div class="flex flex-col">
        <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Checklist de vistoria</p>
        <ListaTextosEditavel
          v-model="form.checklist_vistoria"
          :max-itens="LIMITES_LISTA.checklist.maxItens"
          :max-caracteres="LIMITES_LISTA.checklist.maxCaracteres"
          rotulo-item="item do checklist"
          :disabled="!podeGerir"
        />
        <p v-if="erros.checklist_vistoria" class="text-[11px] text-red-600 mt-1">{{ erros.checklist_vistoria }}</p>
      </div>
    </template>
  </div>
</template>
