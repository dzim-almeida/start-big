<script setup lang="ts">
/**
 * @component NfseConfiguracaoModal
 * @description As decisões da NFS-e que dependem do contador, como opção
 * (docs/nfse-fase2-plano.md, G3). Tudo nasce no comportamento de sempre:
 * sem retenção, uma nota por OS, IBS/CBS só o do serviço.
 *
 * E o padrão fiscal dos serviços NOVOS (M2 de docs/nfse-melhorias-plano.md):
 * o cadastro do serviço já nasce com ele. Não muda nenhuma nota.
 */
import { computed, ref, watch } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import { Info, Save } from 'lucide-vue-next';
import type { AxiosError } from 'axios';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { REGIME_TRIBUTACAO_ISS_OPTIONS } from '@/modules/enterprise/constants/empresa.constants';
import type { ApiError } from '@/shared/types/axios.types';

import { nfseService } from '../../services/nfse.service';
import { fiscalService } from '../../services/fiscal.service';
import { useNbsSugeridos } from '../../composables/useNbsSugeridos';
import { formatarCodigoNacional, formatarNbs } from '../../utils/nfse.utils';
import CodigoFiscalBuscaInput from '../shared/CodigoFiscalBuscaInput.vue';
import { fiscalKeys } from '../../constants/fiscal.constants';
import type { NfseConfiguracao } from '../../types/fiscal.types';

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ close: [] }>();

const toast = useToast();
const queryClient = useQueryClient();

const { data } = useQuery({
  queryKey: fiscalKeys.nfseConfiguracao(),
  queryFn: () => nfseService.obterConfiguracao(),
  enabled: () => props.isOpen,
});

const form = ref<NfseConfiguracao>({
  regime_tributacao_iss: null,
  nfse_reter_iss_pj: false,
  nfse_uma_nota_por_codigo: false,
  nfse_ibs_cbs_cst: null,
  nfse_ibs_cbs_cclass: null,
  nfse_padrao_codigo_nacional: null,
  nfse_padrao_nbs: null,
  nfse_padrao_aliquota_iss: null,
});

// Os campos de código trabalham com string ('' = vazio); o form guarda null.
const padraoCodigo = ref('');
const padraoNbs = ref('');
const padraoIss = ref('');

watch(data, (cfg) => {
  if (!cfg) return;
  form.value = { ...cfg };
  padraoCodigo.value = cfg.nfse_padrao_codigo_nacional ?? '';
  padraoNbs.value = cfg.nfse_padrao_nbs ?? '';
  padraoIss.value = cfg.nfse_padrao_aliquota_iss != null ? String(cfg.nfse_padrao_aliquota_iss / 100) : '';
}, { immediate: true });

const nbsSugeridos = useNbsSugeridos(padraoCodigo, computed(() => props.isOpen));
const buscarServicoNacional = async (termo: string) => (await fiscalService.buscarServicoNacional(termo)).resultados;
const buscarNbs = async (termo: string) => (await fiscalService.buscarNbs(termo)).resultados;

const salvar = useMutation({
  mutationFn: () => nfseService.salvarConfiguracao({
    ...form.value,
    nfse_ibs_cbs_cst: form.value.nfse_ibs_cbs_cst || null,
    nfse_ibs_cbs_cclass: form.value.nfse_ibs_cbs_cclass || null,
    nfse_padrao_codigo_nacional: padraoCodigo.value || null,
    nfse_padrao_nbs: padraoNbs.value || null,
    nfse_padrao_aliquota_iss: padraoIss.value
      ? Math.round(Number(padraoIss.value.replace(',', '.')) * 100)
      : null,
  }),
  onSuccess: (cfg) => {
    queryClient.setQueryData(fiscalKeys.nfseConfiguracao(), cfg);
    toast.success('Configuração da NFS-e salva.');
    emit('close');
  },
  onError: (e) => toast.error('Não foi possível salvar', getErrorMessage(e as AxiosError<ApiError>)),
});
</script>

<template>
  <BaseModal :is-open="isOpen" title="Configuração da NFS-e" size="lg" @close="emit('close')">
    <div class="space-y-5">
      <div class="flex items-start gap-3 p-3 bg-brand-primary-light border border-brand-primary/20 rounded-xl text-brand-primary text-sm">
        <Info :size="16" class="mt-0.5 shrink-0" />
        <span>
          Estas opções dependem do enquadramento da empresa. <strong>Na dúvida, pergunte ao seu contador</strong>
          — sem mexer em nada, a nota sai como sempre saiu.
        </span>
      </div>

      <BaseSelect
        :model-value="form.regime_tributacao_iss ?? undefined"
        @update:model-value="form.regime_tributacao_iss = $event === undefined || $event === '' ? null : Number($event)"
        label="Regime especial do ISS"
        :options="REGIME_TRIBUTACAO_ISS_OPTIONS"
        placeholder="Nenhum"
      />

      <div class="space-y-3">
        <div>
          <BaseCheckbox v-model="form.nfse_reter_iss_pj" label="Tomador empresa (CNPJ) retém o ISS" />
          <p class="text-xs text-zinc-500 ml-6">
            Marque se os seus clientes empresa descontam o ISS na fonte. Para pessoa física nunca há retenção.
          </p>
        </div>
        <div>
          <BaseCheckbox v-model="form.nfse_uma_nota_por_codigo" label="Uma nota por código de serviço" />
          <p class="text-xs text-zinc-500 ml-6">
            Quando a OS tem serviços de códigos nacionais diferentes, emite uma NFS-e para cada código. Desmarcado,
            a OS com códigos diferentes fica pendente.
          </p>
        </div>
      </div>

      <div class="pt-4 border-t border-zinc-200">
        <h4 class="text-sm font-semibold text-zinc-700 mb-1">IBS/CBS padrão (reforma tributária)</h4>
        <p class="text-xs text-zinc-500 mb-3">Usado só no serviço que não tem o próprio IBS/CBS no cadastro.</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <BaseInput v-model="form.nfse_ibs_cbs_cst" label="CST IBS/CBS" placeholder="Ex: 000" inputmode="numeric" />
          <BaseInput v-model="form.nfse_ibs_cbs_cclass" label="Classificação tributária" placeholder="Ex: 000001" inputmode="numeric" />
        </div>
      </div>

      <div class="pt-4 border-t border-zinc-200">
        <h4 class="text-sm font-semibold text-zinc-700 mb-1">Padrão para serviços novos</h4>
        <p class="text-xs text-zinc-500 mb-3">
          O serviço que você cadastrar já nasce com estes códigos — você só troca o que for diferente.
          Use os da nota que você mais emite. Não muda nenhum serviço que já existe.
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <CodigoFiscalBuscaInput
            v-model="padraoCodigo"
            label="Código de Tributação Nacional"
            placeholder="Digite o que o serviço é ou o código"
            :digitos="6"
            :formatar="formatarCodigoNacional"
            :buscar="buscarServicoNacional"
          />
          <CodigoFiscalBuscaInput
            v-model="padraoNbs"
            label="NBS"
            placeholder="Clique para ver as opções do código"
            :digitos="9"
            :formatar="formatarNbs"
            :buscar="buscarNbs"
            :sugeridos="nbsSugeridos"
          />
          <BaseInput
            v-model="padraoIss"
            label="Alíquota ISS (%)"
            placeholder="Só regime normal (ex: 5)"
            inputmode="decimal"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3 w-full">
        <BaseButton type="button" variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton
          type="button"
          variant="primary"
          :is-loading="salvar.isPending.value"
          @click="salvar.mutate()"
        >
          <Save :size="16" class="mr-1.5" />
          Salvar
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
