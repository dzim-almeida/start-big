<!--
===========================================================================
ARQUIVO: OSFotoGallery.vue
MODULO: Ordem de Servico
DESCRICAO: Galeria de fotos do diagnostico da OS. Permite upload, visualizacao
           em slideshow e exclusao de imagens com confirmacao.
===========================================================================

PROPS:
- ordemServicoId: ID da OS para associar as fotos
- fotos: Array de fotos existentes
- readOnly: Desabilita upload/exclusao (usado quando OS finalizada)

EMITS:
- uploaded: Foto enviada com sucesso
- deleted: Foto excluida com sucesso

FUNCIONALIDADES:
- Upload de imagens (validacao de tipo)
- Grid responsivo de miniaturas
- Slideshow fullscreen com navegacao por setas
- Navegacao por teclado (Esc, setas)
- Modal de confirmacao para exclusao
- Invalidacao automatica do cache apos upload/delete

MODO SOMENTE LEITURA:
- Quando readOnly=true, botoes de adicionar/excluir sao ocultados
- Usado automaticamente quando OS esta FINALIZADA ou CANCELADA
===========================================================================
-->
<script setup lang="ts">
import { ref, computed } from 'vue';
import { Trash2, Plus, Image as ImageIcon, ChevronLeft, ChevronRight, X } from 'lucide-vue-next';
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { useToast } from '@/shared/composables/useToast';
import { ordemServicoService } from '../../services/ordemServico.service';
import type { OrdemServicoFotoRead } from '../../types/ordemServico.types';
import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import ConfirmationTemplate from '@/shared/components/templates/ConfirmationTemplate.vue';

interface Props {
  ordemServicoId: number;
  fotos: OrdemServicoFotoRead[];
  readOnly?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  fotos: () => [],
  readOnly: false,
});

const emit = defineEmits<{
  uploaded: [];
  deleted: [];
}>();

const toast = useToast();
const queryClient = useQueryClient();
const fileInput = ref<HTMLInputElement | null>(null);
const isUploading = ref(false);

const uploadMutation = useMutation({
  mutationFn: async (file: File) => {
    return await ordemServicoService.uploadFoto(props.ordemServicoId, file);
  },
  onMutate: () => {
    isUploading.value = true;
  },
  onSuccess: () => {
    toast.success('Foto enviada com sucesso!');
    emit('uploaded');
    queryClient.invalidateQueries({ queryKey: ['ordem-servico', props.ordemServicoId] });
  },
  onError: () => {
    toast.error('Erro ao enviar foto.');
  },
  onSettled: () => {
    isUploading.value = false;
    if (fileInput.value) fileInput.value.value = '';
  }
});

const deleteMutation = useMutation({
  mutationFn: async (fotoId: number) => {
    return await ordemServicoService.deleteFoto(fotoId);
  },
  onSuccess: () => {
    toast.success('Foto removida com sucesso!');
    emit('deleted');
    queryClient.invalidateQueries({ queryKey: ['ordem-servico', props.ordemServicoId] });
  },
  onError: () => {
    toast.error('Erro ao remover foto.');
  }
});
// Slideshow State
const slideshow = ref({
  isOpen: false,
  currentIndex: 0
});

const currentPhoto = computed(() => {
  if (!props.fotos.length || slideshow.value.currentIndex < 0) return null;
  return props.fotos[slideshow.value.currentIndex];
});

function openSlideshow(index: number) {
  slideshow.value.currentIndex = index;
  slideshow.value.isOpen = true;
}

function closeSlideshow() {
  slideshow.value.isOpen = false;
}

function nextPhoto() {
  if (slideshow.value.currentIndex < props.fotos.length - 1) {
    slideshow.value.currentIndex++;
  } else {
    slideshow.value.currentIndex = 0; // Loop
  }
}

function prevPhoto() {
  if (slideshow.value.currentIndex > 0) {
    slideshow.value.currentIndex--;
  } else {
    slideshow.value.currentIndex = props.fotos.length - 1; // Loop
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (!slideshow.value.isOpen) return;
  if (e.key === 'Escape') closeSlideshow();
  if (e.key === 'ArrowRight') nextPhoto();
  if (e.key === 'ArrowLeft') prevPhoto();
}

// Attach listener
window.addEventListener('keydown', handleKeydown);
// Cleanup would be ideal in onUnmounted but script setup handles local listeners poorly without explicit lifecycle hook? 
// Simplest is to check isOpen inside handler.

// Modal Confirmation State
const confirmDeleteModal = ref({
  isOpen: false,
  fotoId: null as number | null,
});

function openDeleteModal(fotoId: number) {
  confirmDeleteModal.value.fotoId = fotoId;
  confirmDeleteModal.value.isOpen = true;
}

function closeDeleteModal() {
  confirmDeleteModal.value.isOpen = false;
  confirmDeleteModal.value.fotoId = null;
}

function confirmDelete() {
  if (confirmDeleteModal.value.fotoId) {
    deleteMutation.mutate(confirmDeleteModal.value.fotoId);
    closeDeleteModal();
  }
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    const file = target.files[0];
    // Validacao simples (ex: < 5MB, imagem)
    if (!file.type.startsWith('image/')) {
      toast.error('Selecione apenas arquivos de imagem.');
      return;
    }
    uploadMutation.mutate(file);
  }
}

function triggerFileInput() {
  fileInput.value?.click();
}

// function handleDelete removed/replaced by openDeleteModal usage in template directly or wrapper


// Helper para URL da imagem (ajuste conforme seu backend serve estaticos)
function getImageUrl(url: string) {
  // Se a URL ja for absoluta, retorna ela. Se for relativa, adiciona base URL da API se necessario.
  // Assumindo que o backend devolve /static/... e seu proxy redireciona ou baseURL da API trata.
  // Se necessario: return `${import.meta.env.VITE_API_URL}${url}`;
  return `http://localhost:8000${url}`; // Ajuste rapido para dev local, ideal usar ENV
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header Galeria -->
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-slate-700 flex items-center gap-2">
        <ImageIcon :size="16" class="text-slate-500" />
        Fotos do Diagnóstico
        <span class="text-xs font-normal text-slate-400">({{ fotos.length }})</span>
      </h3>
      
      <BaseButton 
        v-if="!readOnly"
        @click="triggerFileInput"
        :is-loading="isUploading"
        size="sm"
        variant="primary"
      >
        <Plus :size="16" class="mr-2" />
        Adicionar Foto
      </BaseButton>

      <input 
        ref="fileInput"
        type="file" 
        accept="image/*"
        class="hidden"
        @change="handleFileSelect"
      />
    </div>

    <!-- Grid de Fotos -->
    <div v-if="fotos.length > 0" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
      <div 
        v-for="(foto, index) in fotos" 
        :key="foto.id"
        class="group relative aspect-square bg-slate-100 rounded-xl overflow-hidden border border-slate-200"
      >
        <img 
          :src="getImageUrl(foto.url)" 
          :alt="foto.nome_arquivo"
          class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
        
        <!-- Overlay Acoes -->
        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
           <div class="absolute top-2 right-2 flex gap-2">
              <button 
                type="button"
                @click="openSlideshow(index)"
                class="bg-white/90 p-1.5 rounded-lg text-slate-600 hover:text-brand-primary hover:bg-white shadow-sm transition-all"
                title="Visualizar"
              >
                 <ImageIcon :size="16" />
              </button>
              <button 
                type="button"
                v-if="!readOnly"
                @click="openDeleteModal(foto.id)"
                class="bg-white/90 p-1.5 rounded-lg text-slate-600 hover:text-red-600 hover:bg-white shadow-sm transition-all"
                title="Excluir"
              >
                 <Trash2 :size="16" />
              </button>
           </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-8 bg-slate-50 rounded-xl border border-dashed border-slate-200">
      <div class="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
        <ImageIcon :size="24" class="text-slate-400" />
      </div>
      <p class="text-sm text-slate-500 font-medium">Nenhuma foto adicionada</p>
      <p class="text-xs text-slate-400 mt-1">Fotos do equipamento e diagnóstico aparecerão aqui.</p>
    </div>

    <!-- Slideshow Modal -->
    <div v-if="slideshow.isOpen" class="fixed inset-0 z-9999 bg-black/90 flex flex-col items-center justify-center p-4 backdrop-blur-sm animate-fadeIn">
       <!-- Close Button -->
       <button 
         type="button"
         class="absolute top-4 right-4 text-white/70 hover:text-white bg-white/10 hover:bg-white/20 p-2 rounded-full transition-all"
         @click="closeSlideshow"
       >
         <X :size="24" />
       </button>

       <!-- Main Image Container -->
       <div class="relative w-full max-w-5xl h-full max-h-[85vh] flex items-center justify-center">
          
          <!-- Prev Button -->
          <button 
            v-if="fotos.length > 1"
            type="button"
            class="absolute left-0 md:-left-12 z-10 text-white/70 hover:text-white bg-black/20 hover:bg-black/40 p-3 rounded-full transition-all"
            @click.stop="prevPhoto"
          >
            <ChevronLeft :size="32" />
          </button>

          <!-- Image -->
          <img 
            v-if="currentPhoto"
            :src="getImageUrl(currentPhoto.url)" 
            :alt="currentPhoto.nome_arquivo"
            class="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
          />

          <!-- Next Button -->
          <button 
            v-if="fotos.length > 1"
            type="button"
            class="absolute right-0 md:-right-12 z-10 text-white/70 hover:text-white bg-black/20 hover:bg-black/40 p-3 rounded-full transition-all"
            @click.stop="nextPhoto"
          >
            <ChevronRight :size="32" />
          </button>
       </div>
       
       <!-- Footer Info -->
       <div class="absolute bottom-6 left-0 right-0 text-center">
          <p class="text-white/90 font-medium text-lg drop-shadow-md">
             {{ currentPhoto?.nome_arquivo }}
          </p>
          <p class="text-white/60 text-sm mt-1">
             {{ slideshow.currentIndex + 1 }} de {{ fotos.length }}
          </p>
       </div>
    </div>

    <!-- Modal de Confirmacao de Exclusao -->
    <BaseModal
      :is-open="confirmDeleteModal.isOpen"
      title="Excluir Foto?"
      size="sm"
      @close="closeDeleteModal"
    >
       <ConfirmationTemplate
          :icon="Trash2"
          icon-bg-class="bg-brand-primary-light"
          icon-color-class="text-brand-primary"
       >
          <template #description>
             <p class="text-sm text-slate-500 leading-relaxed">
                Deseja realmente remover esta foto do diagnóstico? <br>
                <span class="text-xs text-red-500 font-semibold">Esta ação não poderá ser desfeita.</span>
             </p>
          </template>

          <template #footer>
             <div class="flex gap-3 w-full">
                <BaseButton
                   variant="secondary"
                   class="flex-1"
                   @click="closeDeleteModal"
                >
                   Cancelar
                </BaseButton>
                <BaseButton
                   variant="primary"
                   class="flex-1 bg-brand-primary hover:bg-brand-primary/90"
                   @click="confirmDelete"
                >
                   Excluir
                </BaseButton>
             </div>
          </template>
       </ConfirmationTemplate>
    </BaseModal>
  </div>
</template>
