<!--
===========================================================================
ARQUIVO: ServicoFormModal.vue
MODULO: Ordem de Servico
DESCRICAO: Modal para cadastro e edicao de servicos no catalogo.
           Permite definir descricao e valor base do servico.
===========================================================================

PROPS:
- isOpen: Controla visibilidade do modal
- servico: Servico existente para edicao (null para novo)

EMITS:
- close: Fecha o modal

FUNCIONALIDADES:
- Cadastro de novo servico (descricao + valor)
- Edicao de servico existente
- Validacao de descricao obrigatoria
- Confirmacao para valor R$ 0,00
- Preview em tempo real do valor formatado
- Feedback via toast notifications

CAMPOS:
- Descricao: Textarea com placeholder exemplo
- Valor: Input monetario com preview formatado

MUTATIONS:
- createMutation: Cria novo servico
- updateMutation: Atualiza servico existente
===========================================================================
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import {
  Wrench,
  DollarSign,
  FileText,
  CheckCircle2,
  Tag,
  AlertCircle
} from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/commons/BaseInput/BaseInput.vue';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { createServico, updateServico } from '../../services/servicos.service';
import type { ServicoCreate, ServicoRead, ServicoUpdate } from '../../types/servicos.types';
import type { ApiError } from '@/shared/types/axios.types';

interface Props {
  isOpen: boolean;
  servico?: ServicoRead | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
}>();

const toast = useToast();
const queryClient = useQueryClient();

const isEditMode = computed(() => !!props.servico);
const modalTitle = computed(() => (isEditMode.value ? 'Editar Serviço' : 'Novo Serviço'));

const apiError = ref<string | null>(null);

const form = ref({
  descricao: '',
  valor: '',
});

watch(
  () => props.servico,
  (servico) => {
    if (servico) {
      form.value = {
        descricao: servico.descricao,
        valor: formatCurrencyInput(servico.valor),
      };
    }
  },
  { immediate: true }
);

function formatCurrencyInput(valueInCents: number): string {
  return (valueInCents / 100).toFixed(2).replace('.', ',');
}

function formatCurrency(valueInCents: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valueInCents / 100);
}

function parseCurrencyToCents(value: string): number {
  const cleanValue = value.replace(/[^\d,]/g, '').replace(',', '.');
  return Math.round(parseFloat(cleanValue || '0') * 100);
}

const valorPreview = computed(() => {
  const cents = parseCurrencyToCents(form.value.valor);
  return formatCurrency(cents);
});

const createMutation = useMutation<ServicoRead, AxiosError<ApiError>, ServicoCreate>({
  mutationFn: createServico,
  onSuccess: () => {
    toast.success('Serviço cadastrado com sucesso!');
    queryClient.invalidateQueries({ queryKey: ['servicos'] });
    handleClose();
  },
  onError: (error) => {
    apiError.value = getErrorMessage(error, 'Erro ao cadastrar serviço');
  },
});

const updateMutation = useMutation<
  ServicoRead,
  AxiosError<ApiError>,
  { id: number; data: ServicoUpdate }
>({
  mutationFn: ({ id, data }) => updateServico(id, data),
  onSuccess: () => {
    toast.success('Serviço atualizado com sucesso!');
    queryClient.invalidateQueries({ queryKey: ['servicos'] });
    handleClose();
  },
  onError: (error) => {
    apiError.value = getErrorMessage(error, 'Erro ao atualizar serviço');
  },
});

const isPending = computed(() => createMutation.isPending.value || updateMutation.isPending.value);

function resetForm() {
  form.value = {
    descricao: '',
    valor: '',
  };
}

function handleClose() {
  resetForm();
  apiError.value = null;
  emit('close');
}

function handleSubmit() {
  apiError.value = null;

  if (!form.value.descricao.trim()) {
    apiError.value = 'Informe a descrição do serviço';
    return;
  }

  const valorCentavos = parseCurrencyToCents(form.value.valor);

  if (valorCentavos <= 0) {
    if (confirm('O valor do serviço é R$ 0,00. Deseja continuar?') === false) {
       return;
    }
  }

  if (isEditMode.value && props.servico) {
    const data: ServicoUpdate = {
      descricao: form.value.descricao || undefined,
      valor: valorCentavos !== undefined ? valorCentavos : undefined,
    };
    updateMutation.mutate({ id: props.servico.id, data });
  } else {
    const data: ServicoCreate = {
      descricao: form.value.descricao,
      valor: valorCentavos,
    };
    createMutation.mutate(data);
  }
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title=""
    size="md"
    @close="handleClose"
  >
    <!-- HEADER PREMIUM -->
    <template #header>
      <div class="bg-[#0F172A] px-6 py-5 rounded-t-2xl shadow-lg relative overflow-hidden">
        <!-- Efeito de fundo sutil removido -->
        
        <div class="relative z-10 flex justify-between items-start">
           <div>
              <h3 class="text-xl font-black text-white tracking-wide uppercase flex items-center gap-2">
                 <Wrench :size="20" class="text-brand-primary" />
                 {{ modalTitle }}
              </h3>
              <p class="text-brand-primary/20 text-xs mt-1 font-medium max-w-xs leading-relaxed opacity-80">
                 {{ isEditMode ? 'Edite as informações do item selecionado' : 'Adicione um novo serviço ou peça ao catálogo' }}
              </p>
           </div>
           
           <button 
             type="button" 
             class="text-white/50 hover:text-white hover:bg-white/10 rounded-lg p-1.5 transition-colors"
             @click="handleClose"
           >
             <span class="sr-only">Fechar</span>
             <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
           </button>
        </div>
      </div>
    </template>

    <div class="p-1">
      <!-- Erro da API -->
      <div
        v-if="apiError"
        class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 animate-fadeIn"
      >
        <AlertCircle :size="20" class="text-red-600 shrink-0 mt-0.5" />
        <div>
          <h4 class="text-sm font-bold text-red-700">Atenção</h4>
          <p class="text-xs text-red-600 mt-1">{{ apiError }}</p>
        </div>
      </div>

      <form class="space-y-6" @submit.prevent="handleSubmit">
        
        <!-- Bloco Principal -->
        <div class="bg-white rounded-xl border border-slate-200 p-5 space-y-5 shadow-sm">
          
          <!-- Descricao -->
          <div class="space-y-2">
            <label class="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wide">
              <span class="bg-brand-primary-light text-brand-primary p-1 rounded">
                <FileText :size="14" />
              </span>
              Descrição do Serviço <span class="text-red-500">*</span>
            </label>
            <div class="relative group">
              <textarea
                v-model="form.descricao"
                class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-brand-primary-light0 focus:ring-4 focus:ring-brand-primary-light0/10 transition-all resize-none"
                rows="3"
                placeholder="Ex: Troca de Display iPhone 14 Pro Max (Qualidade Original)"
                required
              ></textarea>
              <div class="absolute bottom-3 right-3">
                 <Tag :size="14" class="text-slate-300 group-focus-within:text-brand-primary transition-colors" />
              </div>
            </div>
            <p class="text-[10px] text-slate-400 px-1">
               Utilize uma descrição clara e detalhada para facilitar a busca nas Ordens de Serviço.
            </p>
          </div>

          <div class="border-t border-slate-100"></div>

          <!-- Valor -->
          <div class="space-y-2">
            <label class="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wide">
              <span class="bg-brand-primary-light text-brand-primary p-1 rounded">
                <DollarSign :size="14" />
              </span>
              Valor Base (R$)
            </label>
            
            <div class="grid grid-cols-2 gap-4 items-center">
               <div class="relative">
                 <BaseInput
                   v-model="form.valor"
                   placeholder="0,00"
                   required
                   class="font-mono font-bold text-lg"
                 />
               </div>
               
               <!-- Preview Visual -->
               <div class="bg-brand-primary-light/50 border border-brand-primary-light rounded-xl p-3 flex flex-col justify-center items-end">
                  <span class="text-[10px] font-bold text-brand-primary uppercase">Valor Atual</span>
                  <span class="text-xl font-black text-brand-primary tracking-tight">{{ valorPreview }}</span>
               </div>
            </div>
          </div>

        </div>

        <!-- Info Box -->
        <div class="bg-brand-primary-light rounded-xl p-4 border border-brand-primary-light flex gap-3">
           <div class="bg-white p-1.5 rounded-lg shadow-sm border border-brand-primary-light h-fit text-brand-primary">
              <CheckCircle2 :size="16" />
           </div>
           <div class="space-y-1">
              <h4 class="text-xs font-bold text-brand-primary">Cadastro Rápido</h4>
              <p class="text-[11px] leading-relaxed text-brand-primary/80">
                 Este serviço será salvo no catálogo geral e poderá ser reutilizado em futuras ordens de serviço.
              </p>
           </div>
        </div>

      </form>
    </div>

    <!-- FOOTER -->
    <template #footer>
      <div class="flex justify-between items-center bg-slate-50 -m-6 p-4 border-t border-slate-200 mt-2 rounded-b-2xl">
        <div class="text-[10px] text-slate-400 px-2">
           <span class="text-red-500 font-bold">*</span> Campos Obrigatórios
        </div>
        <div class="flex gap-3">
          <BaseButton 
            type="button" 
            variant="secondary" 
            :disabled="isPending" 
            @click="handleClose"
            class="hover:bg-white hover:border-slate-300"
          >
            CANCELAR
          </BaseButton>
          <BaseButton 
            type="button" 
            variant="primary"
            :is-loading="isPending" 
            @click="handleSubmit"
            class="px-8 shadow-lg shadow-brand-primary-light0/20"
          >
            {{ isEditMode ? 'SALVAR ALTERAÇÕES' : 'CADASTRAR' }}
          </BaseButton>
        </div>
      </div>
    </template>
  </BaseModal>
</template>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
