<script setup lang="ts">
import BaseProgressBar from '@/shared/components/ui/BaseProgressBar/BaseProgressBar.vue';
import BaseStatusPill from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';

/**
 * @component AmbienteSecao
 * O bloco de um ambiente nas abas da OS (Produção, Entrega) e no editor:
 * número "01", nome, contagem de móveis, uma linha de apoio e, à direita, o
 * progresso ou o que vier no slot `direita`. O corpo e o rodapé são slots.
 *
 * `numero` é a posição na lista (1, 2, 3) — formatado com dois dígitos.
 * Sem `progresso`, não desenha barra.
 */
withDefaults(
  defineProps<{
    numero: number;
    nome: string;
    contagem?: string;
    subtitulo?: string;
    progresso?: number | null;
    rotuloProgresso?: string;
    detalheProgresso?: string;
    /** Cabeçalho com fundo azulado (seção que agrupa cards) ou branco (seção simples). */
    destaque?: boolean;
    /** Ambiente que ainda não começou: o número fica cinza. */
    inativo?: boolean;
  }>(),
  { progresso: null, destaque: false, inativo: false, rotuloProgresso: 'Progresso do ambiente' },
);
</script>

<template>
  <!-- SEM `overflow-hidden` (remodelação item 19): ele cortava os menus que abrem para
       baixo dentro do ambiente (o da etapa, com "Concluir"/"Reabrir", e o "⋯" do móvel):
       o item de baixo ficava escondido e o clique não pegava. Os cantos arredondados
       ficam com quem tem fundo: o cabeçalho (em cima; e embaixo quando está sozinho)
       e o rodapé. -->
  <section class="rounded-2xl border border-zinc-200 bg-white">
    <header
      :class="[
        'flex flex-wrap items-center justify-between gap-4 rounded-t-2xl border-b border-zinc-200 px-6 py-4 last:rounded-b-2xl last:border-b-0',
        destaque ? 'bg-brand-primary-light/50' : 'bg-white',
      ]"
    >
      <div class="flex min-w-0 items-center gap-3.5">
        <span
          :class="[
            'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-bold tabular-nums',
            inativo ? 'bg-zinc-200 text-zinc-600' : 'bg-brand-primary text-white',
          ]"
          aria-hidden="true"
        >
          {{ String(numero).padStart(2, '0') }}
        </span>
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <h3 class="text-base font-semibold text-zinc-900">{{ nome }}</h3>
            <BaseStatusPill v-if="contagem" tom="info">{{ contagem }}</BaseStatusPill>
            <slot name="etiquetas" />
          </div>
          <p v-if="subtitulo" class="text-xs text-zinc-500">{{ subtitulo }}</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <slot name="direita">
          <div v-if="progresso !== null" class="w-56">
            <BaseProgressBar
              :valor="progresso"
              :rotulo="rotuloProgresso"
              :detalhe="detalheProgresso"
              :tom="progresso >= 100 ? 'sucesso' : 'primario'"
            />
          </div>
        </slot>
      </div>
    </header>

    <div v-if="$slots.default" class="flex flex-col gap-4 px-6 py-5">
      <slot />
    </div>

    <footer v-if="$slots.rodape" class="rounded-b-2xl border-t border-zinc-200 bg-zinc-50 px-6 py-3.5">
      <slot name="rodape" />
    </footer>
  </section>
</template>
