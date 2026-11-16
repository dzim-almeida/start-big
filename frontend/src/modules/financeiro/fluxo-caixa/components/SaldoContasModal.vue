<script setup lang="ts">
/**
 * "Quanto você tem hoje?" — conferir o saldo, não digitá-lo de novo.
 *
 * O sistema sabe tudo que entrou e saiu desde que começou a ser usado, mas não
 * sabe o que já havia na gaveta antes disso. Na primeira vez, o dono informa
 * esse ponto de partida; dali em diante cada venda, OS e conta paga entra no
 * saldo sozinha. É o mesmo desenho do "saldo inicial" do Conta Azul e do Omie.
 *
 * Por isso o campo já vem com o saldo de AGORA (`saldo_atual`), e não com o
 * que o dono digitou semanas atrás: ele confere a gaveta e o banco e, se bater,
 * só confirma. Até 27/10/2026 o campo mostrava a âncora velha e só gravava o
 * que mudasse — e confirmar um saldo que bateu não fazia nada, então o
 * lembrete de conferir nunca saía.
 *
 * O servidor carimba a data E o instante da declaração. O instante é o que
 * impede a venda da manhã de ser contada duas vezes quando o dono confere a
 * gaveta à tarde: ela já está dentro do número que ele acabou de contar.
 *
 * Uma conta por linha, e não um campo só com o total: a projeção soma as
 * contas ATIVAS, e o dono precisa enxergar de onde cada pedaço veio para
 * corrigir a que estiver errada.
 */
import { ref, watch } from 'vue';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { formatDataPura } from '@/shared/utils/date.utils';
import { formatCurrency } from '@/shared/utils/finance';

import { useContasBancariasQuery, useInformarSaldos } from '../../shared/composables/useFinanceiro';
import type { ContaBancaria } from '../../shared/schemas/financeiro.schema';

const props = defineProps<{ aberto: boolean }>();
const emit = defineEmits<{ fechar: [] }>();

const { data: contas, refetch } = useContasBancariasQuery();
const informar = useInformarSaldos();

// Chaveado por id: o v-model de cada linha precisa de um lugar próprio, e o
// índice do array não serve — a lista pode chegar depois de o modal abrir.
const valores = ref<Record<number, number>>({});

/** O que o sistema calcula que a conta tem agora; a âncora se nunca declarou. */
function saldoDoSistema(conta: ContaBancaria): number {
  return conta.saldo_atual ?? conta.saldo_informado ?? 0;
}

function recarregar() {
  const mapa: Record<number, number> = {};
  for (const conta of contas.value ?? []) mapa[conta.id] = saldoDoSistema(conta) / 100;
  valores.value = mapa;
}

watch(() => contas.value, recarregar, { immediate: true });

// A lista fica 5 minutos em cache: ao abrir, busca de novo para o campo trazer
// a venda de agora há pouco.
watch(
  () => props.aberto,
  (aberto) => {
    if (aberto) void refetch();
    recarregar();
  },
  { immediate: true },
);

async function confirmar() {
  await informar.mutateAsync(
    (contas.value ?? []).map((conta) => ({
      id: conta.id,
      saldo_informado: Math.round((valores.value[conta.id] ?? 0) * 100),
    })),
  );
  emit('fechar');
}
</script>

<template>
  <BaseModal :is-open="aberto" title="Saldo de hoje" size="sm" overlay @close="emit('fechar')">
    <div class="flex flex-col gap-4">
      <p class="text-sm text-zinc-500">
        Confira quanto há em cada conta <strong>agora</strong>. Se o número bater com a gaveta e o
        banco, é só confirmar. Se não bater, digite o valor certo.
      </p>

      <div v-for="conta in contas ?? []" :key="conta.id" class="flex flex-col gap-1">
        <BaseMoneyInput v-model="valores[conta.id]" :label="conta.nome" />
        <p class="text-xs text-zinc-400" data-saldo-info>
          <template v-if="conta.saldo_informado_em">
            Pelo sistema: {{ formatCurrency(saldoDoSistema(conta)) }} · conferido em
            {{ formatDataPura(conta.saldo_informado_em) }}
          </template>
          <template v-else>Nunca informado</template>
        </p>
      </div>

      <p class="rounded-xl bg-zinc-50 px-3.5 py-2.5 text-xs text-zinc-500">
        O saldo anda sozinho: cada venda, OS e conta paga entra nele. Uma vez por mês o sistema
        lembra de conferir — é o que pega o que ele não vê, como um troco errado ou uma tarifa do
        banco.
      </p>
    </div>

    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <BaseButton variant="secondary" class="px-5" @click="emit('fechar')">Cancelar</BaseButton>
        <BaseButton
          variant="primary"
          class="px-5"
          :is-loading="informar.isPending.value"
          @click="confirmar"
        >
          Confirmar saldo
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
