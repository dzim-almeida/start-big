<script setup lang="ts">
/**
 * @component DadosFiscaisSection
 * @description Dados fiscais do serviço para a NFS-e.
 *
 * Componente de apresentação — os campos pertencem ao form principal
 * gerenciado por useServicoFormProvider. Dados fiscais são salvos junto com o
 * serviço. As consultas próprias (rota da NFS-e, busca do código nacional e
 * NBS sugeridos) não gravam nada.
 *
 * Mostra só o que a nota DESTA empresa pede (docs/nfse-melhorias-plano.md, M1,
 * revisão do Alan em 29/10/2026): na Nacional, código nacional + NBS; pela
 * prefeitura, também o que a cidade exige; alíquota de ISS só no regime normal;
 * IBS/CBS e os códigos da prefeitura ficam em "Mais opções". CFOP, CST e
 * unidade saíram: nenhuma nota lê esses campos do serviço.
 */

import { computed, ref } from 'vue';
import { ChevronDown, FileText, Info } from 'lucide-vue-next';
import CodigoFiscalBuscaInput from '@/modules/fiscal/components/shared/CodigoFiscalBuscaInput.vue';
import { fiscalService } from '@/modules/fiscal/services/fiscal.service';
import { useNbsSugeridos } from '@/modules/fiscal/composables/useNbsSugeridos';
import { useNfseRota } from '@/modules/fiscal/composables/useNfseRota';
import { formatarCodigoNacional, formatarNbs } from '@/modules/fiscal/utils/nfse.utils';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useServicoForm } from '../../composables/useServicoForm';
import { CST_IBS_CBS_OPTIONS } from '@/shared/constants/fiscal.constants';

// =============================================
// Props
// =============================================

interface Props {
  submitCount: number;
  disabled?: boolean;
  isCreateMode?: boolean;
}

defineProps<Props>();

// =============================================
// Form context (injetado do pai)
// =============================================

const {
  fiscal_codigo_servico_lc116,
  fiscal_cnae,
  fiscal_aliquota_iss_display,
  fiscal_codigo_tributacao_municipio,
  fiscal_c_class_trib,
  fiscal_cst_ibs_cbs,
  fiscal_aliquota_ibs_display,
  fiscal_aliquota_cbs_display,
  fiscal_c_benef,
  fiscal_codigo_tributacao_nacional,
  fiscal_codigo_nbs,
  nfseDisponivel,
  errors,
} = useServicoForm();

// =============================================
// O que a nota desta empresa pede
// =============================================

const { rota, municipal, exige } = useNfseRota(nfseDisponivel);
const pendente = computed(() => rota.value.rota === 'MUNICIPAL_PENDENTE');
const cidade = computed(() => rota.value.cidade ?? 'a sua cidade');
const regimeNormal = computed(() => rota.value.regime === 'normal');

/** O que a cidade cobra, em português de tela (só na rota municipal). */
const exigidosPelaCidade = computed(() =>
  [
    exige('codigo_tributario_municipio') ? 'código tributário municipal' : null,
    exige('codigo_cnae') ? 'CNAE' : null,
  ].filter(Boolean) as string[],
);

/** "Mais opções" abre sozinho quando já tem algo preenchido lá dentro. */
const temAvancadoPreenchido = computed(
  () =>
    !!(fiscal_c_class_trib.value || fiscal_cst_ibs_cbs.value || fiscal_aliquota_ibs_display.value ||
      fiscal_aliquota_cbs_display.value || fiscal_c_benef.value ||
      (!municipal.value && (fiscal_cnae.value || fiscal_codigo_tributacao_municipio.value))),
);
/** null = ninguém clicou ainda: aberto se houver algo preenchido. */
const mostrarAvancado = ref<boolean | null>(null);
const avancadoAberto = computed(() => mostrarAvancado.value ?? temAvancadoPreenchido.value);

// =============================================
// Código nacional → NBS sugeridos
// =============================================

const nbsSugeridos = useNbsSugeridos(fiscal_codigo_tributacao_nacional, nfseDisponivel);

const buscarServicoNacional = async (termo: string) =>
  (await fiscalService.buscarServicoNacional(termo)).resultados;

const buscarNbs = async (termo: string) => (await fiscalService.buscarNbs(termo)).resultados;
</script>

<template>
  <!-- Cabeçalho da seção -->
  <div class="flex items-center gap-3 mb-6">
    <div class="w-10 h-10 bg-brand-primary-light rounded-xl flex items-center justify-center text-brand-primary">
      <LucideIcon :icon="FileText" />
    </div>
    <h3 class="text-lg font-semibold text-zinc-800">Dados Fiscais</h3>
  </div>

  <!-- Aviso: serviço ainda não cadastrado (modo criação) -->
  <div
    v-if="isCreateMode"
    class="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-sm"
  >
    <Info :size="16" class="mt-0.5 shrink-0" />
    <span>
      Os dados fiscais do serviço podem ser preenchidos após o cadastro inicial. Salve o
      serviço primeiro e depois acesse a edição para preencher as informações fiscais.
    </span>
  </div>

  <!-- Formulário fiscal (modo edição) -->
  <div v-else class="space-y-5">
    <!-- O que a nota pede, conforme a rota da empresa -->
    <div
      v-if="pendente"
      class="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-sm"
    >
      <Info :size="16" class="mt-0.5 shrink-0" />
      <span>
        A NFS-e de {{ cidade }} ainda está sendo configurada pelo suporte StartBig. Você já pode
        preencher o código nacional e o NBS abaixo; a emissão é liberada quando a configuração terminar.
      </span>
    </div>
    <div
      v-else
      class="flex items-start gap-3 p-3 bg-brand-primary-light border border-brand-primary/20 rounded-xl text-brand-primary text-sm"
    >
      <Info :size="16" class="mt-0.5 shrink-0" />
      <span v-if="municipal">
        A sua NFS-e sai pelo <strong>sistema da prefeitura de {{ cidade }}</strong>. Preencha o
        <strong>Código de Tributação Nacional</strong> e o <strong>NBS</strong>
        <template v-if="exigidosPelaCidade.length">
          e também o que a prefeitura pede: <strong>{{ exigidosPelaCidade.join(' e ') }}</strong>
        </template>.
      </span>
      <span v-else>
        A sua NFS-e sai pelo <strong>padrão nacional</strong> (o mesmo do portal nfse.gov.br).
        Para emitir, o serviço precisa de só dois códigos: o <strong>Código de Tributação Nacional</strong>
        e o <strong>NBS</strong>. O resto é opcional.
      </span>
    </div>

    <!-- Os dois códigos que toda NFS-e pede -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <CodigoFiscalBuscaInput
        v-model="fiscal_codigo_tributacao_nacional"
        label="Código de Tributação Nacional"
        placeholder="Digite o que o serviço é (ex: manutenção) ou o código"
        :digitos="6"
        :formatar="formatarCodigoNacional"
        :buscar="buscarServicoNacional"
        :disabled="disabled"
        :error="submitCount > 0 ? errors.fiscal_codigo_tributacao_nacional : undefined"
        ajuda="Diz que tipo de serviço é. Na nota que você já emite pelo portal, é o 'Código de Tributação Nacional' (ex: 14.01.01)."
      />

      <CodigoFiscalBuscaInput
        v-model="fiscal_codigo_nbs"
        label="NBS"
        placeholder="Clique para ver as opções do código acima"
        :digitos="9"
        :formatar="formatarNbs"
        :buscar="buscarNbs"
        :sugeridos="nbsSugeridos"
        :disabled="disabled"
        :error="submitCount > 0 ? errors.fiscal_codigo_nbs : undefined"
        ajuda="Escolhido o código nacional, clique aqui: aparecem as opções que a Receita indica para ele. Na sua nota, é o 'Código da NBS' (ex: 1.2001.20.00)."
      />
    </div>

    <p v-if="fiscal_codigo_servico_lc116 && !municipal" class="text-xs text-zinc-500">
      Item da LC 116: <strong class="text-zinc-700">{{ fiscal_codigo_servico_lc116 }}</strong>
      — preenchido pelo código nacional.
    </p>

    <!-- O que a prefeitura pede (rota municipal) -->
    <div v-if="municipal" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <BaseInput
        v-model="fiscal_codigo_tributacao_municipio"
        :label="exige('codigo_tributario_municipio') ? 'Código tributário municipal (obrigatório)' : 'Código tributário municipal'"
        placeholder="Ex: 1401"
        :disabled="disabled"
        :error="submitCount > 0 ? errors.fiscal_codigo_tributacao_municipio : undefined"
        :ajuda="`O código do serviço na lista da prefeitura de ${cidade}. O contador ou a prefeitura informam.`"
      />
      <BaseInput
        v-model="fiscal_cnae"
        :label="exige('codigo_cnae') ? 'CNAE (obrigatório)' : 'CNAE'"
        placeholder="Ex: 9512-6/00"
        :disabled="disabled"
        inputmode="numeric"
        mask="####-#/##"
        :error="submitCount > 0 ? errors.fiscal_cnae : undefined"
        ajuda="A atividade da empresa ligada a este serviço (está no cartão CNPJ)."
      />
      <BaseInput
        v-model="fiscal_codigo_servico_lc116"
        label="Item da LC 116"
        placeholder="Ex: 14.01"
        :disabled="disabled"
        inputmode="numeric"
        mask="##.##"
        :error="submitCount > 0 ? errors.fiscal_codigo_servico_lc116 : undefined"
        ajuda="Vem do código nacional; troque só se a prefeitura pedir outro."
      />
    </div>

    <!-- Alíquota de ISS: só no regime normal (MEI e Simples não informam) -->
    <div v-if="regimeNormal" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <BaseInput
        v-model="fiscal_aliquota_iss_display"
        label="Alíquota ISS (%)"
        placeholder="Ex: 5"
        :disabled="disabled"
        inputmode="decimal"
        :error="submitCount > 0 ? errors.fiscal_aliquota_iss_display : undefined"
        ajuda="Percentual de ISS da sua cidade para este serviço (entre 2% e 5%)."
      />
    </div>

    <!-- Mais opções: IBS/CBS e, fora da rota municipal, os códigos da prefeitura -->
    <div class="pt-4 border-t border-zinc-200">
      <button
        type="button"
        class="flex items-center gap-2 text-sm font-semibold text-zinc-600 hover:text-zinc-800"
        @click="mostrarAvancado = !avancadoAberto"
      >
        <ChevronDown :size="16" :class="['transition-transform', avancadoAberto ? 'rotate-180' : '']" />
        Mais opções
        <span class="text-xs font-normal text-zinc-400">— não precisa preencher para emitir</span>
      </button>

      <div v-if="avancadoAberto" class="mt-4 space-y-5">
        <div>
          <h4 class="text-sm font-semibold text-zinc-700">Reforma Tributária (IBS/CBS)</h4>
          <p class="text-xs text-zinc-500 mt-1 mb-3">
            Opcional em 2026: a nota de MEI e Simples sai sem isso. Se ficar em branco, vale o padrão
            da Configuração da NFS-e. Preencha só se o seu contador pedir.
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <BaseInput
              v-model="fiscal_c_class_trib"
              label="Classif. Tributária"
              placeholder="Ex: 000001"
              :disabled="disabled"
              :error="submitCount > 0 ? errors.fiscal_c_class_trib : undefined"
            />
            <BaseSelect
              v-model="fiscal_cst_ibs_cbs"
              label="CST IBS/CBS"
              :options="CST_IBS_CBS_OPTIONS"
              :disabled="disabled"
              placeholder="Pesquise o CST..."
              :error="submitCount > 0 ? errors.fiscal_cst_ibs_cbs : undefined"
            />
            <BaseInput
              v-model="fiscal_aliquota_ibs_display"
              label="Alíquota IBS (%)"
              placeholder="Ex: 0,1"
              :disabled="disabled"
              inputmode="decimal"
              :error="submitCount > 0 ? errors.fiscal_aliquota_ibs_display : undefined"
            />
            <BaseInput
              v-model="fiscal_aliquota_cbs_display"
              label="Alíquota CBS (%)"
              placeholder="Ex: 0,9"
              :disabled="disabled"
              inputmode="decimal"
              :error="submitCount > 0 ? errors.fiscal_aliquota_cbs_display : undefined"
            />
            <BaseInput
              v-model="fiscal_c_benef"
              label="Cód. Benefício Fiscal"
              placeholder="Ex: BR123456"
              :disabled="disabled"
              :error="submitCount > 0 ? errors.fiscal_c_benef : undefined"
            />
          </div>
        </div>

        <div v-if="!municipal">
          <h4 class="text-sm font-semibold text-zinc-700">Códigos da prefeitura</h4>
          <p class="text-xs text-zinc-500 mt-1 mb-3">
            Só valem quando a nota sai pelo sistema da prefeitura. Pelo padrão nacional, não são usados.
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <BaseInput
              v-model="fiscal_codigo_tributacao_municipio"
              label="Código tributário municipal"
              placeholder="Ex: 1401"
              :disabled="disabled"
              :error="submitCount > 0 ? errors.fiscal_codigo_tributacao_municipio : undefined"
            />
            <BaseInput
              v-model="fiscal_cnae"
              label="CNAE"
              placeholder="Ex: 9512-6/00"
              :disabled="disabled"
              inputmode="numeric"
              mask="####-#/##"
              :error="submitCount > 0 ? errors.fiscal_cnae : undefined"
            />
            <BaseInput
              v-model="fiscal_codigo_servico_lc116"
              label="Item da LC 116"
              placeholder="Ex: 14.01"
              :disabled="disabled"
              inputmode="numeric"
              mask="##.##"
              :error="submitCount > 0 ? errors.fiscal_codigo_servico_lc116 : undefined"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
