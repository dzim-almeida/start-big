<script setup lang="ts">
/**
 * Etiqueta de estado ("Separado", "Em pedido", "Terceirizada").
 *
 * Os tons são os mesmos do BaseStatsCard, mais `info`, para a mesma cor dizer
 * a mesma coisa em qualquer tela: `sucesso` = pronto/ok, `alerta` = pendente,
 * `perigo` = deu errado, `info` = em andamento, `neutro` = sem destaque.
 * Cor nunca vem sozinha: o texto da etiqueta diz o estado.
 */
export type TomStatus = 'neutro' | 'info' | 'sucesso' | 'alerta' | 'perigo';

withDefaults(
  defineProps<{
    tom?: TomStatus;
    /** Aviso longo que pode quebrar linha (o padrão é uma linha só, para tabela). */
    quebraLinha?: boolean;
  }>(),
  { tom: 'neutro', quebraLinha: false },
);

const TONS: Record<TomStatus, string> = {
  neutro: 'bg-zinc-100 text-zinc-600 border-zinc-200',
  info: 'bg-brand-primary-light text-brand-primary border-brand-primary/20',
  sucesso: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  alerta: 'bg-amber-50 text-amber-700 border-amber-200',
  perigo: 'bg-red-50 text-red-700 border-red-200',
};
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1 border px-2.5 py-0.5 text-xs font-semibold',
      quebraLinha ? 'whitespace-normal rounded-lg leading-snug' : 'whitespace-nowrap rounded-full',
      TONS[tom],
    ]"
  >
    <slot />
  </span>
</template>
