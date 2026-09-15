<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useFiscalConfiguracaoMutation } from '../../composables/useFiscalConfiguracaoMutation';
import { useFiscalPlataformaQuery } from '../../composables/useFiscalPlataformaQuery';
import type { EnvioPlataforma, FiscalConfiguracao } from '../../types/fiscal.types';
import { Building, ShieldAlert, CheckCircle2, AlertTriangle } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';

const props = defineProps<{
  isOpen: boolean;
  configuracao?: FiscalConfiguracao;
}>();

const emit = defineEmits<{
  'update:isOpen': [value: boolean];
  'saved': [];
}>();

const serieNfe = ref<number | string>(1);
const ultimoNumeroNfe = ref<number | string>(0);
const serieNfce = ref<number | string>(1);
const ultimoNumeroNfce = ref<number | string>(0);
const cscId = ref('');
const cscToken = ref('');

const error = ref('');
const success = ref(false);
/** O que a plataforma respondeu ao CSC neste salvamento (null = não mexeu no CSC). */
const cscPlataforma = ref<EnvioPlataforma | null>(null);

const { mutateAsync: salvarConfig, isPending } = useFiscalConfiguracaoMutation();

/**
 * O ambiente NÃO se escolhe aqui. Quem decide é a plataforma, por loja — o
 * ERP nem manda `tpAmb`. Este modal tinha um select "Ambiente SEFAZ" que só
 * gravava um rótulo local, e em 15/09/2026 o lojista trocou-o para Produção
 * enquanto a nota seguia saindo em homologação. O select saiu; o que fica é o
 * que a plataforma responde, somente leitura.
 */
const { data: plataforma, isLoading: consultandoPlataforma } = useFiscalPlataformaQuery(
  () => props.isOpen,
);

const ambientePlataforma = computed(() =>
  plataforma.value?.consultou ? plataforma.value.ambiente ?? null : null,
);

const nomeAmbiente = computed(() => {
  if (consultandoPlataforma.value) return 'Consultando a plataforma…';
  if (ambientePlataforma.value === 1) return 'Produção';
  if (ambientePlataforma.value === 2) return 'Homologação (testes)';
  return 'Não confirmado';
});

watch(
  () => [props.isOpen, props.configuracao],
  () => {
    if (props.isOpen && props.configuracao) {
      serieNfe.value = props.configuracao.serie_nfe ?? 1;
      ultimoNumeroNfe.value = props.configuracao.ultimo_numero_nfe ?? 0;
      serieNfce.value = props.configuracao.serie_nfce ?? 1;
      ultimoNumeroNfce.value = props.configuracao.ultimo_numero_nfce ?? 0;
      cscId.value = props.configuracao.csc_id ?? '';
      cscToken.value = props.configuracao.csc_token ?? '';
      error.value = '';
      success.value = false;
      cscPlataforma.value = null;
    }
  },
  { immediate: true }
);

function close() {
  emit('update:isOpen', false);
}

async function handleSave() {
  error.value = '';
  success.value = false;
  cscPlataforma.value = null;

  try {
    const salvo = await salvarConfig({
      serie_nfe: Number(serieNfe.value) || 1,
      ultimo_numero_nfe: Number(ultimoNumeroNfe.value) || 0,
      serie_nfce: Number(serieNfce.value) || 1,
      ultimo_numero_nfce: Number(ultimoNumeroNfce.value) || 0,
      csc_id: cscId.value?.trim() || null,
      csc_token: cscToken.value?.trim() || null,
    } as any);

    success.value = true;
    cscPlataforma.value = salvo?.csc_plataforma ?? null;
    emit('saved');
    // O CSC que NÃO chegou na emissora é o aviso mais importante desta tela:
    // fechar sozinho o esconderia. Só fecha sozinho quando não há o que ler.
    if (!cscPlataforma.value || cscPlataforma.value.aceito) {
      setTimeout(() => {
        close();
      }, 1200);
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Erro ao salvar as configurações fiscais.';
  }
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Configuração de Emissão Estadual"
    subtitle="Configure os parâmetros de emissão da NF-e e NFC-e junto à SEFAZ."
    size="lg"
    @close="close"
  >
    <div class="space-y-6">
      <div v-if="error" class="p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3">
        <LucideIcon :icon="ShieldAlert" class="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
        <p class="text-sm text-red-600 font-medium">{{ error }}</p>
      </div>

      <div v-if="success" class="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3">
        <LucideIcon :icon="CheckCircle2" class="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
        <p class="text-sm text-emerald-700 font-medium">
          {{ cscPlataforma?.aceito ? 'Configurações salvas e CSC cadastrado na emissora.' : 'Configurações salvas com sucesso!' }}
        </p>
      </div>

      <!-- O CSC foi salvo aqui mas NÃO chegou na emissora: sem isto o cartão
           dizia "Configurado" e o cupom saía sem QR Code. -->
      <div
        v-if="cscPlataforma && !cscPlataforma.aceito"
        :class="[
          'p-4 rounded-xl border flex items-start gap-3',
          cscPlataforma.indisponivel ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200',
        ]"
      >
        <LucideIcon
          :icon="cscPlataforma.indisponivel ? AlertTriangle : ShieldAlert"
          :class="['w-5 h-5 shrink-0 mt-0.5', cscPlataforma.indisponivel ? 'text-amber-500' : 'text-red-500']"
        />
        <div class="text-sm leading-relaxed" :class="cscPlataforma.indisponivel ? 'text-amber-800' : 'text-red-700'">
          <p class="font-semibold">
            {{ cscPlataforma.indisponivel ? 'O CSC ficou só neste computador.' : 'A emissora recusou o CSC.' }}
          </p>
          <p class="text-xs mt-1">
            {{ cscPlataforma.mensagem || 'A plataforma de emissão não confirmou o cadastro.' }}
            Quem monta o QR Code da NFC-e é a emissora — até o CSC estar cadastrado lá,
            o cupom sai sem QR Code. Confira no cartão <strong>Plataforma de Emissão</strong>.
          </p>
        </div>
      </div>

      <!-- Ambiente: definido pela plataforma, somente leitura -->
      <div class="bg-zinc-50/80 p-5 rounded-xl border border-zinc-200/80 space-y-3">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <LucideIcon :icon="Building" class="w-4 h-4 text-brand-primary" />
            <h4 class="text-sm font-bold text-zinc-800">Ambiente SEFAZ</h4>
          </div>
          <span
            :class="[
              'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border',
              ambientePlataforma === 1
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : ambientePlataforma === 2
                  ? 'bg-blue-50 text-blue-700 border-blue-200'
                  : 'bg-zinc-100 text-zinc-600 border-zinc-200',
            ]"
          >
            <span
              :class="[
                'inline-flex h-2 w-2 rounded-full',
                ambientePlataforma === 1 ? 'bg-emerald-500' : ambientePlataforma === 2 ? 'bg-blue-500' : 'bg-zinc-400',
              ]"
            />
            {{ nomeAmbiente }}
          </span>
        </div>
        <p class="text-xs text-zinc-500 leading-relaxed">
          Quem define o ambiente é a plataforma de emissão, por loja — não há como
          trocá-lo por aqui. Em homologação as notas não têm valor fiscal; em produção,
          toda nota autorizada é um documento real.
        </p>
        <p
          v-if="ambientePlataforma == null && !consultandoPlataforma"
          class="flex items-start gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 leading-relaxed"
        >
          <LucideIcon :icon="AlertTriangle" class="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-500" />
          <span>
            Não deu para consultar a plataforma agora. O ambiente real de cada nota
            aparece no detalhe dela depois que a SEFAZ responde.
          </span>
        </p>
      </div>

      <!-- Parâmetros NF-e -->
      <div class="border border-zinc-200/80 rounded-xl p-5 space-y-4">
        <h4 class="text-sm font-bold text-zinc-800 flex items-center justify-between">
          <span>NF-e (Modelo 55)</span>
          <span class="text-xs font-normal text-zinc-500">Nota Fiscal Eletrônica</span>
        </h4>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <BaseInput
            v-model="serieNfe"
            type="number"
            label="Série da NF-e"
            placeholder="Ex: 1"
            :disabled="isPending || success"
          />
          <BaseInput
            v-model="ultimoNumeroNfe"
            type="number"
            label="Último Número Emitido"
            placeholder="Ex: 0"
            :disabled="isPending || success"
          />
        </div>
      </div>

      <!-- Parâmetros NFC-e e CSC -->
      <div class="border border-zinc-200/80 rounded-xl p-5 space-y-4">
        <h4 class="text-sm font-bold text-zinc-800 flex items-center justify-between">
          <span>NFC-e (Modelo 65) & CSC</span>
          <span class="text-xs font-normal text-zinc-500">Nota de Consumidor / Cupom</span>
        </h4>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <BaseInput
            v-model="serieNfce"
            type="number"
            label="Série da NFC-e"
            placeholder="Ex: 1"
            :disabled="isPending || success"
          />
          <BaseInput
            v-model="ultimoNumeroNfce"
            type="number"
            label="Último Número Emitido"
            placeholder="Ex: 0"
            :disabled="isPending || success"
          />
        </div>

        <div class="pt-3 border-t border-zinc-100 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="sm:col-span-1">
            <BaseInput
              v-model="cscId"
              label="ID do Token CSC"
              placeholder="Ex: 000001"
              :disabled="isPending || success"
            />
          </div>
          <div class="sm:col-span-2">
            <BaseInput
              v-model="cscToken"
              label="Código de Segurança (Token CSC)"
              placeholder="Ex: A1B2C3D4E5F6..."
              :disabled="isPending || success"
            />
          </div>
        </div>
        <p class="text-xs text-zinc-500">
          O CSC é obrigatório para o QR Code da NFC-e e é gerado no portal de NFC-e da SEFAZ
          do seu estado, <strong>para o ambiente em uso</strong> (o de homologação não vale em
          produção). Ao salvar, ele é enviado à plataforma de emissão, que o cadastra na emissora.
        </p>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-3 w-full">
        <BaseButton
          variant="secondary"
          @click="close"
          :disabled="isPending"
        >
          Cancelar
        </BaseButton>
        <BaseButton
          variant="primary"
          @click="handleSave"
          :is-loading="isPending"
          :disabled="success"
        >
          Salvar Configurações
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>

