<script setup lang="ts">
/**
 * @component PositionCard
 * @description Card for cargo overview
 */

import { computed } from 'vue';
import { BriefcaseBusiness, Pencil, Trash2 } from 'lucide-vue-next';

import { POSITION_CARD_THEMES } from '../constants/positions.constants';

interface Props {
  id: number;
  name: string;
  employees: number;
  permissionsEnabled: number;
  permissionsTotal: number;
  themeIndex?: number;
}

const props = withDefaults(defineProps<Props>(), {
  themeIndex: 0,
});

const emit = defineEmits<{
  (e: 'view', id: number): void;
  (e: 'edit', id: number): void;
  (e: 'remove', id: number): void;
}>();

const theme = computed(() => {
  const index = props.themeIndex % POSITION_CARD_THEMES.length;
  return POSITION_CARD_THEMES[index];
});

const employeeLabel = computed(() => {
  if (props.employees === 1) return '1 colaborador vinculado';
  return `${props.employees} colaboradores vinculados`;
});

const permissionPercent = computed(() => {
  if (!props.permissionsTotal) return 0;
  return Math.round((props.permissionsEnabled / props.permissionsTotal) * 100);
});
</script>

<template>
  <article
    class="group relative w-full cursor-pointer rounded-2xl border border-zinc-100 bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl"
    :class="theme.glow"
    role="button"
    tabindex="0"
    @click="emit('view', id)"
  >
    <div class="flex items-center gap-4">
      <div
        class="flex h-12 w-12 items-center justify-center rounded-2xl ring-1"
        :class="[theme.iconBg, theme.ring]"
      >
        <BriefcaseBusiness :size="20" />
      </div>

      <div class="flex-1">
        <div class="flex items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-zinc-800">{{ name }}</h3>
        </div>
        <p class="mt-0.5 text-xs text-zinc-500">{{ employeeLabel }}</p>

        <div class="mt-3 flex items-center gap-3">
          <span class="text-[10px] font-semibold uppercase tracking-widest text-zinc-400">
            Permissoes
          </span>
          <div class="h-1.5 w-20 rounded-full bg-zinc-100">
            <div
              class="h-full rounded-full bg-brand-primary transition-all"
              :style="{ width: `${permissionPercent}%` }"
            ></div>
          </div>
          <span class="text-[10px] font-semibold text-zinc-500">
            {{ permissionsEnabled }}/{{ permissionsTotal }}
          </span>
        </div>
      </div>

      <div class="hidden items-center gap-1 group-hover:flex">
        <button
          type="button"
          title="Editar"
          class="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-brand-primary/10 hover:text-brand-primary cursor-pointer"
          @click.stop="emit('edit', id)"
        >
          <Pencil :size="18" />
        </button>
        <button
          type="button"
          title="Excluir" 
          class="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-red-50 hover:text-red-600 cursor-pointer"
          @click.stop="emit('remove', id)"
        >
          <Trash2 :size="18" />
        </button>
      </div>
    </div>
  </article>
</template>
