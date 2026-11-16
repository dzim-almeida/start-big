<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { Undo2, Info, MapPin } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { getAddressByCep } from '@/shared/services/cep.service';
import { formatCurrency } from '@/shared/utils/finance';
import { formatCPF, formatCNPJ } from '@/shared/utils/document.utils';
import type { ApiError } from '@/shared/types/axios.types';
import type { AxiosError } from 'axios';

import { useFiscalDevolucaoMutation } from '../../composables/useFiscalDevolucaoMutation';
import {
  MILESIMOS,
  MOTIVO_DEVOLUCAO_MAXIMO,
  MOTIVO_DEVOLUCAO_MINIMO,
  destinatarioAvulsoValido,
  destinatarioAvulsoVazio,
  sanitizarDestinatario,
  useDevolucaoItens,
} from '../../composables/useDevolucaoItens';
import type { DocumentoFiscalRead, DocumentoItemResumo } from '../../types/fiscal.types';

const props = defineProps<{
  isOpen: boolean;
  documento: DocumentoFiscalRead;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'sucesso', novoDocumentoId: number): void;
}>();

const itensOrigem = computed<DocumentoItemResumo[]>(() => props.documento.itens_resumo ?? []);
const { modo, itens, errosPorItem, itensValidos, total, itensParaPayload, reiniciar } =
  useDevolucaoItens(itensOrigem);

const motivo = ref('');
const devolverEstoque = ref(true);
const destAvulso = ref(destinatarioAvulsoVazio());
const buscandoCep = ref(false);
const erroCep = ref('');

// O backend só exige o avulso quando a nota de origem não tem cliente com
// endereço. `destinatario_id` é a melhor pista daqui; se ainda assim o
// backend responder DESTINATARIO_OBRIGATORIO, a seção é aberta na hora.
const exigirAvulsoPeloBackend = ref(false);
const temDestinatarioOrigem = computed(() => !!props.documento.destinatario_id);
const precisaAvulso = computed(() => !temDestinatarioOrigem.value || exigirAvulsoPeloBackend.value);

const mutation = useFiscalDevolucaoMutation();

const motivoValido = computed(() => {
  const n = motivo.value.trim().length;
  return n >= MOTIVO_DEVOLUCAO_MINIMO && n <= MOTIVO_DEVOLUCAO_MAXIMO;
});

const formularioValido = computed(
  () =>
    motivoValido.value &&
    itensValidos.value &&
    (!precisaAvulso.value || destinatarioAvulsoValido(destAvulso.value)) &&
    !mutation.isPending.value,
);

const indicadorIeOptions = [
  { value: 9, label: 'Não contribuinte (pessoa física / sem IE)' },
  { value: 2, label: 'Isento de IE' },
  { value: 1, label: 'Contribuinte de ICMS (informar IE)' },
];

watch(
  () => props.isOpen,
  (aberto) => {
    if (aberto) {
      reiniciar();
      motivo.value = '';
      devolverEstoque.value = true;
      destAvulso.value = destinatarioAvulsoVazio();
      erroCep.value = '';
      exigirAvulsoPeloBackend.value = false;
    }
  },
);

// Quando volta para TOTAL, cada linha recupera o saldo cheio.
watch(modo, (novo) => {
  if (novo === 'TOTAL') reiniciar();
});

/** Quantidade em UN na tela; milésimos por baixo. */
function qtdEmUnidades(mil: number): number {
  return mil / MILESIMOS;
}
function atualizarQtd(index: number, valor: string | number) {
  const un = Number(valor);
  itens.value[index].qtdDevolverMil = Number.isFinite(un) ? Math.round(un * MILESIMOS) : 0;
}

async function buscarCep() {
  const cep = destAvulso.value.cep.replace(/\D/g, '');
  if (cep.length !== 8) return;
  buscandoCep.value = true;
  erroCep.value = '';
  try {
    const end = await getAddressByCep(cep);
    destAvulso.value = {
      ...destAvulso.value,
      logradouro: end.logradouro || destAvulso.value.logradouro,
      bairro: end.bairro || destAvulso.value.bairro,
      municipio: end.localidade || destAvulso.value.municipio,
      uf: end.uf || destAvulso.value.uf,
      codigo_municipio: end.ibge || destAvulso.value.codigo_municipio,
    };
  } catch {
    erroCep.value = 'CEP não encontrado. Preencha o endereço manualmente.';
  } finally {
    buscandoCep.value = false;
  }
}

async function handleSubmit() {
  if (!formularioValido.value) return;
  try {
    const novo = await mutation.mutateAsync({
      documentoId: props.documento.id,
      payload: {
        motivo: motivo.value.trim(),
        devolver_estoque: devolverEstoque.value,
        itens: itensParaPayload(),
        destinatario_avulso: precisaAvulso.value ? sanitizarDestinatario(destAvulso.value) : null,
      },
    });
    emit('sucesso', novo.id);
    emit('close');
  } catch (err) {
    const detail = (err as AxiosError<ApiError>)?.response?.data?.detail as { codigo?: string } | undefined;
    if (detail?.codigo === 'DESTINATARIO_OBRIGATORIO') exigirAvulsoPeloBackend.value = true;
    // O toast já foi dado pela mutation.
  }
}

const documentoOrigemFormatado = computed(() => {
  const d = props.documento.destinatario_documento ?? '';
  return d.length === 14 ? formatCNPJ(d) : d.length === 11 ? formatCPF(d) : d;
});
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Emitir NF-e de Devolução"
    :subtitle="`Devolução da ${documento.tipo_documento === 'NFCE' ? 'NFC-e' : 'NF-e'} nº ${documento.numero_documento ?? '—'} · Série ${documento.serie ?? '—'}`"
    size="2xl"
    @close="emit('close')"
  >
    <div class="space-y-5">
      <!-- Resumo da nota de origem -->
      <div class="rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-xs text-zinc-600 space-y-1">
        <p><span class="font-semibold text-zinc-800">Chave:</span> <span class="font-mono">{{ documento.chave_acesso ?? '—' }}</span></p>
        <p v-if="documento.destinatario_nome">
          <span class="font-semibold text-zinc-800">Cliente:</span> {{ documento.destinatario_nome }}
          <span v-if="documentoOrigemFormatado" class="text-zinc-400">· {{ documentoOrigemFormatado }}</span>
        </p>
        <p class="flex items-start gap-1.5 text-[11px] text-zinc-500 pt-1">
          <LucideIcon :icon="Info" class="w-3.5 h-3.5 shrink-0 mt-0.5" />
          A NF-e de devolução (modelo 55, entrada, finalidade 4) referencia esta nota na SEFAZ e
          consome um número da sequência de NF-e. Os valores espelham a nota original.
        </p>
      </div>

      <!-- Modo -->
      <div class="flex items-center gap-4">
        <span class="text-xs font-bold uppercase tracking-wider text-zinc-400">Devolver</span>
        <label class="inline-flex items-center gap-1.5 text-sm cursor-pointer">
          <input v-model="modo" type="radio" value="TOTAL" class="accent-brand-primary" data-testid="modo-total" />
          Tudo o que ainda não foi devolvido
        </label>
        <label class="inline-flex items-center gap-1.5 text-sm cursor-pointer">
          <input v-model="modo" type="radio" value="PARCIAL" class="accent-brand-primary" data-testid="modo-parcial" />
          Só alguns itens / quantidades
        </label>
      </div>

      <!-- Itens -->
      <div class="rounded-xl border border-zinc-200 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-zinc-50 text-[11px] uppercase tracking-wider text-zinc-400">
            <tr>
              <th class="px-3 py-2 text-left w-8"></th>
              <th class="px-3 py-2 text-left">Produto</th>
              <th class="px-3 py-2 text-right">Qtd. original</th>
              <th class="px-3 py-2 text-right">Saldo</th>
              <th class="px-3 py-2 text-right w-32">Qtd. a devolver</th>
              <th class="px-3 py-2 text-right">Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in itens"
              :key="item.documentoItemId"
              :class="['border-t border-zinc-100', !item.selecionado && 'opacity-50']"
              :data-testid="`item-devolucao-${item.documentoItemId}`"
            >
              <td class="px-3 py-2">
                <input
                  v-model="item.selecionado"
                  type="checkbox"
                  class="accent-brand-primary"
                  :disabled="modo === 'TOTAL' || item.saldoDisponivelMil === 0"
                />
              </td>
              <td class="px-3 py-2 text-zinc-800">{{ item.nome }}</td>
              <td class="px-3 py-2 text-right tabular-nums">{{ qtdEmUnidades(item.quantidadeOriginalMil) }}</td>
              <td class="px-3 py-2 text-right tabular-nums" :class="item.saldoDisponivelMil === 0 ? 'text-zinc-400' : ''">
                {{ qtdEmUnidades(item.saldoDisponivelMil) }}
              </td>
              <td class="px-3 py-2 text-right">
                <input
                  type="number"
                  :value="qtdEmUnidades(item.qtdDevolverMil)"
                  :min="1 / MILESIMOS"
                  :max="qtdEmUnidades(item.saldoDisponivelMil)"
                  step="any"
                  :disabled="modo === 'TOTAL' || !item.selecionado"
                  class="w-24 rounded-lg border px-2 py-1 text-right text-sm tabular-nums disabled:bg-zinc-50"
                  :class="errosPorItem[item.documentoItemId] ? 'border-red-400' : 'border-zinc-200'"
                  @input="atualizarQtd(index, ($event.target as HTMLInputElement).value)"
                />
                <p v-if="errosPorItem[item.documentoItemId]" class="text-[10px] text-red-500 mt-0.5 text-right">
                  {{ errosPorItem[item.documentoItemId] }}
                </p>
              </td>
              <td class="px-3 py-2 text-right tabular-nums">
                {{ formatCurrency(Math.round((item.qtdDevolverMil * item.valorUnitario) / MILESIMOS)) }}
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="itens.length === 0" class="p-4 text-xs text-zinc-500">
          Esta nota não tem itens registrados; não é possível devolver pelo sistema.
        </p>
      </div>

      <!-- Destinatário -->
      <div v-if="precisaAvulso" class="rounded-xl border border-amber-200 bg-amber-50/50 p-4 space-y-3">
        <div class="flex items-start gap-2">
          <LucideIcon :icon="MapPin" class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <p class="text-xs text-amber-900 leading-relaxed">
            A nota de origem não identificou o comprador com endereço. A NF-e exige o destinatário
            completo — informe quem está devolvendo.
          </p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <BaseInput v-model="destAvulso.cpf_ou_cnpj" label="CPF / CNPJ" placeholder="Só números" inputmode="numeric" />
          <BaseInput v-model="destAvulso.nome_razao_social" label="Nome / Razão social" />
          <BaseSelect v-model="destAvulso.indicador_inscricao_estadual" label="Inscrição estadual" :options="indicadorIeOptions" />
          <BaseInput
            v-if="destAvulso.indicador_inscricao_estadual === 1"
            v-model="destAvulso.inscricao_estadual"
            label="IE"
          />
          <div class="flex items-end gap-2">
            <BaseInput v-model="destAvulso.cep" label="CEP" placeholder="00000000" inputmode="numeric" :error="erroCep" class="flex-1" @blur="buscarCep" />
            <BaseButton variant="secondary" size="sm" :is-loading="buscandoCep" @click="buscarCep">Buscar</BaseButton>
          </div>
          <BaseInput v-model="destAvulso.codigo_municipio" label="Código IBGE do município" placeholder="7 dígitos" inputmode="numeric" />
          <BaseInput v-model="destAvulso.logradouro" label="Logradouro" />
          <BaseInput v-model="destAvulso.numero" label="Número" />
          <BaseInput v-model="destAvulso.complemento" label="Complemento" />
          <BaseInput v-model="destAvulso.bairro" label="Bairro" />
          <BaseInput v-model="destAvulso.municipio" label="Município" />
          <BaseInput v-model="destAvulso.uf" label="UF" placeholder="SP" />
        </div>
      </div>

      <!-- Motivo e estoque -->
      <div class="space-y-3">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-zinc-500 mb-1">
            Motivo / Justificativa da devolução
          </label>
          <textarea
            v-model="motivo"
            rows="3"
            :maxlength="MOTIVO_DEVOLUCAO_MAXIMO"
            data-testid="motivo-devolucao"
            class="w-full rounded-lg border border-zinc-200 p-2.5 text-sm focus:border-brand-primary focus:outline-none"
            :placeholder="`Ex.: cliente devolveu a mercadoria com defeito (mínimo ${MOTIVO_DEVOLUCAO_MINIMO} caracteres)`"
          />
          <p class="text-[11px] text-zinc-400 text-right tabular-nums">{{ motivo.trim().length }}/{{ MOTIVO_DEVOLUCAO_MAXIMO }}</p>
        </div>
        <BaseCheckbox v-model="devolverEstoque" label="Retornar itens ao estoque da loja quando a SEFAZ autorizar" />
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full gap-3">
        <div class="text-sm">
          <span class="text-zinc-500">Total da devolução:</span>
          <span class="font-bold text-zinc-900 ml-1" data-testid="total-devolucao">{{ formatCurrency(total) }}</span>
        </div>
        <div class="flex gap-3">
          <BaseButton variant="secondary" :disabled="mutation.isPending.value" @click="emit('close')">Cancelar</BaseButton>
          <BaseButton
            variant="primary"
            data-testid="btn-transmitir-devolucao"
            :disabled="!formularioValido"
            :is-loading="mutation.isPending.value"
            @click="handleSubmit"
          >
            <LucideIcon :icon="Undo2" class="w-4 h-4 mr-1" />
            Transmitir NF-e de Devolução
          </BaseButton>
        </div>
      </div>
    </template>
  </BaseModal>
</template>
