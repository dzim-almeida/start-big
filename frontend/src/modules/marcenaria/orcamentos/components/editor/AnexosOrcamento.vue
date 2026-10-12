<script setup lang="ts">
/**
 * @component AnexosOrcamento
 * @description Fotos e PDFs da medição (Spec 06B D44-D47).
 *
 * - Entram por botão ou arrastando arquivos (vários de uma vez).
 * - A legenda é editável DEPOIS ("Parede da pia" entre 15 fotos).
 * - Foto abre ampliada aqui mesmo; PDF abre no visualizador do sistema.
 * - Os anexos valem para TODAS as versões do orçamento (06A D30): excluir avisa.
 * - Anexar NÃO passa pela fila de escrita: não mexe na revisão (D47).
 */
import { ref } from 'vue';
import { useQueryClient } from '@tanstack/vue-query';
import { FileText, Paperclip, Trash2, X } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { abrirArquivo } from '@/modules/fiscal/utils/abrirArquivo';
import { useToast } from '@/shared/composables/useToast';
import { getImageUrl } from '@/shared/utils/print.utils';

import { LIMITES, chaveAnexos } from '../../constants/orcamento.constants';
import { useEditor } from '../../composables/useEditorContexto';
import { useAnexosQuery } from '../../composables/useOrcamentoQuery';
import type { AnexoOrcamento } from '../../schemas/orcamentoDetalhe.schema';
import { alterarLegenda, incluirAnexo, removerAnexo } from '../../services/orcamentoAnexos.service';
import { mensagemDoErro } from '../../utils/erros';
import { escaparHtml } from '../../utils/textoSeguro';

const { id, acoes, confirmar } = useEditor();
const toast = useToast();
const queryClient = useQueryClient();
const { data: anexos } = useAnexosQuery(id);

/** Tipos aceitos (o backend confere de novo, 06A §6.9). */
const ACEITOS = 'image/jpeg,image/png,image/webp,application/pdf';

const enviando = ref(0);                                  // quantos arquivos ainda subindo
const arrastando = ref(false);                            // destaque da área de soltar
const seletor = ref<HTMLInputElement | null>(null);
const ampliada = ref<AnexoOrcamento | null>(null);         // foto aberta em tela cheia

/** Recarrega a lista depois de incluir, legendar ou excluir. */
const recarregar = () => queryClient.invalidateQueries({ queryKey: chaveAnexos(id.value ?? 0) });

/** Envia cada arquivo (um por vez: o servidor recebe um por chamada). */
async function enviar(arquivos: FileList | File[]) {
  if (id.value == null) return;
  for (const arquivo of Array.from(arquivos)) {
    enviando.value++;
    try {
      await incluirAnexo(id.value, arquivo);
    } catch (erro) {
      toast.error(`Não foi possível anexar "${arquivo.name}".`, mensagemDoErro(erro));
    } finally {
      enviando.value--;
    }
  }
  await recarregar();
}

function aoEscolher(evento: Event) {
  const campo = evento.target as HTMLInputElement;
  if (campo.files?.length) void enviar(campo.files);
  campo.value = '';                                        // permite escolher o mesmo arquivo de novo
}

function aoSoltar(evento: DragEvent) {
  arrastando.value = false;
  if (!acoes.value.anexos) return;
  const arquivos = evento.dataTransfer?.files;
  if (arquivos?.length) void enviar(arquivos);
}

/** Grava a legenda ao sair do campo (só se mudou). */
async function salvarLegenda(anexo: AnexoOrcamento, evento: Event) {
  const texto = (evento.target as HTMLInputElement).value.trim();
  if ((anexo.legenda ?? '') === texto || id.value == null) return;
  try {
    await alterarLegenda(id.value, anexo.id, texto || null);
    await recarregar();
  } catch (erro) {
    toast.error('Não foi possível salvar a legenda.', mensagemDoErro(erro));
  }
}

async function excluir(anexo: AnexoOrcamento) {
  const ok = await confirmar({
    titulo: 'Excluir anexo',
    descricao: `Este arquivo (<strong>${escaparHtml(anexo.nome_arquivo)}</strong>) é usado por todas as versões deste orçamento. Excluir mesmo assim?`,
    confirmLabel: 'Excluir',
    variant: 'danger',
  });
  if (!ok || id.value == null) return;
  try {
    await removerAnexo(id.value, anexo.id);
    await recarregar();
  } catch (erro) {
    toast.error('Não foi possível excluir o anexo.', mensagemDoErro(erro));
  }
}

/** Foto: amplia aqui. PDF: abre no visualizador do sistema (como no fiscal). */
function abrir(anexo: AnexoOrcamento) {
  if (anexo.tipo === 'FOTO') ampliada.value = anexo;
  else void abrirArquivo(getImageUrl(anexo.url) ?? anexo.url);
}
</script>

<template>
  <div
    class="rounded-xl border-2 border-dashed p-3 transition-colors"
    :class="arrastando ? 'border-brand-primary bg-brand-primary/5' : 'border-transparent'"
    data-testid="area-anexos"
    @dragover.prevent="arrastando = acoes.anexos"
    @dragleave.prevent="arrastando = false"
    @drop.prevent="aoSoltar"
  >
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      <figure v-for="anexo in anexos ?? []" :key="anexo.id" class="group relative overflow-hidden rounded-lg border border-zinc-200 bg-zinc-50">
        <button type="button" class="block h-28 w-full cursor-pointer" :aria-label="`Abrir ${anexo.nome_arquivo}`" @click="abrir(anexo)">
          <img
            v-if="anexo.tipo === 'FOTO'"
            :src="getImageUrl(anexo.url) ?? ''"
            :alt="anexo.legenda || anexo.nome_arquivo"
            class="h-full w-full object-cover"
            loading="lazy"
          />
          <span v-else class="flex h-full flex-col items-center justify-center gap-1 text-zinc-500">
            <FileText :size="28" />
            <span class="max-w-full truncate px-2 text-[11px]">{{ anexo.nome_arquivo }}</span>
          </span>
        </button>
        <figcaption class="p-1.5">
          <input
            :value="anexo.legenda ?? ''"
            :maxlength="LIMITES.legendaAnexo"
            :disabled="!acoes.anexos"
            placeholder="Legenda"
            :aria-label="`Legenda de ${anexo.nome_arquivo}`"
            class="w-full rounded border border-transparent bg-transparent px-1 py-0.5 text-[11px] text-zinc-700 hover:border-zinc-200 focus:border-zinc-300 focus:bg-white focus:outline-none"
            @blur="salvarLegenda(anexo, $event)"
            @keydown.enter="($event.target as HTMLInputElement).blur()"
          />
        </figcaption>
        <button
          v-if="acoes.anexos"
          type="button"
          class="absolute right-1 top-1 rounded-md bg-white/90 p-1 text-zinc-500 opacity-0 shadow-sm transition-opacity hover:text-red-600 group-hover:opacity-100 focus:opacity-100 cursor-pointer"
          :aria-label="`Excluir ${anexo.nome_arquivo}`"
          @click="excluir(anexo)"
        >
          <Trash2 :size="14" />
        </button>
      </figure>
    </div>

    <div v-if="acoes.anexos" class="mt-3 flex flex-wrap items-center gap-3">
      <input ref="seletor" type="file" :accept="ACEITOS" multiple class="hidden" data-testid="seletor-anexos" @change="aoEscolher" />
      <BaseButton variant="secondary" size="sm" :is-loading="enviando > 0" @click="seletor?.click()">
        <Paperclip :size="14" class="mr-1" /> Anexar
      </BaseButton>
      <span class="text-[11px] text-zinc-400">Fotos (JPG, PNG, WEBP) ou PDF. Pode arrastar vários arquivos para cá.</span>
    </div>
    <p v-else-if="!anexos?.length" class="text-xs text-zinc-400">Nenhum anexo.</p>

    <!-- Foto ampliada (D45) -->
    <Teleport to="body">
      <div
        v-if="ampliada"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6"
        role="dialog"
        aria-modal="true"
        :aria-label="ampliada.legenda || ampliada.nome_arquivo"
        @click.self="ampliada = null"
        @keydown.esc="ampliada = null"
      >
        <button type="button" class="absolute right-4 top-4 rounded-full bg-white/90 p-2 text-zinc-700 cursor-pointer" aria-label="Fechar" @click="ampliada = null">
          <X :size="18" />
        </button>
        <figure class="max-h-full max-w-5xl">
          <img :src="getImageUrl(ampliada.url) ?? ''" :alt="ampliada.legenda || ampliada.nome_arquivo" class="max-h-[80vh] rounded-lg object-contain" />
          <figcaption v-if="ampliada.legenda" class="mt-2 text-center text-sm text-white">{{ ampliada.legenda }}</figcaption>
        </figure>
      </div>
    </Teleport>
  </div>
</template>
