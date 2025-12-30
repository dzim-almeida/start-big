<script setup lang="ts">
/**
 * @component SegmentIcons
 * @description Componente que renderiza ícones SVG para os segmentos de negócio.
 * Utiliza ícones coloridos e estilizados para uma aparência profissional.
 */

interface Props {
  icon: string;
  size?: 'sm' | 'md' | 'lg';
}

withDefaults(defineProps<Props>(), {
  size: 'md',
});

const sizeClasses: Record<string, string> = {
  sm: 'w-5 h-5',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
};
</script>

<template>
  <!-- Assistência Técnica - Computador -->
  <svg
    v-if="icon === 'computer'"
    :class="sizeClasses[size]"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Monitor -->
    <rect x="8" y="8" width="48" height="36" rx="3" fill="#E3F2FD" stroke="#1976D2" stroke-width="2"/>
    <!-- Tela -->
    <rect x="12" y="12" width="40" height="28" rx="1" fill="#BBDEFB"/>
    <!-- Tela interna com gradiente -->
    <rect x="14" y="14" width="36" height="24" fill="#64B5F6"/>
    <!-- Base do monitor -->
    <path d="M24 44H40V48H24V44Z" fill="#1976D2"/>
    <!-- Suporte -->
    <rect x="20" y="48" width="24" height="4" rx="1" fill="#1565C0"/>
    <!-- Ícone na tela -->
    <circle cx="32" cy="26" r="6" fill="#1976D2"/>
    <path d="M29 26L31 28L35 24" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>

  <!-- Oficina Mecânica - Chave e engrenagem -->
  <svg
    v-else-if="icon === 'wrench'"
    :class="sizeClasses[size]"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Engrenagem -->
    <circle cx="40" cy="24" r="12" fill="#E0E0E0" stroke="#616161" stroke-width="2"/>
    <circle cx="40" cy="24" r="6" fill="#9E9E9E"/>
    <!-- Dentes da engrenagem -->
    <rect x="38" y="10" width="4" height="6" fill="#616161"/>
    <rect x="38" y="32" width="4" height="6" fill="#616161"/>
    <rect x="50" y="22" width="6" height="4" fill="#616161"/>
    <rect x="24" y="22" width="6" height="4" fill="#616161"/>
    <!-- Chave inglesa -->
    <path d="M12 52L28 36" stroke="#FF8F00" stroke-width="4" stroke-linecap="round"/>
    <path d="M28 36C30 34 34 34 36 36C38 38 38 42 36 44L28 36Z" fill="#FFB300"/>
    <circle cx="14" cy="50" r="4" fill="#FF6F00"/>
  </svg>

  <!-- Mercado - Loja/Barraca -->
  <svg
    v-else-if="icon === 'store'"
    :class="sizeClasses[size]"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Toldo listrado -->
    <path d="M8 20L12 8H52L56 20H8Z" fill="#F44336"/>
    <path d="M16 8L14 20" stroke="#FFEB3B" stroke-width="4"/>
    <path d="M28 8L26 20" stroke="#FFEB3B" stroke-width="4"/>
    <path d="M40 8L38 20" stroke="#FFEB3B" stroke-width="4"/>
    <path d="M52 8L50 20" stroke="#FFEB3B" stroke-width="4"/>
    <!-- Ondas do toldo -->
    <path d="M8 20Q14 28 20 20Q26 12 32 20Q38 28 44 20Q50 12 56 20" fill="#E53935" stroke="#C62828" stroke-width="1"/>
    <!-- Estrutura da loja -->
    <rect x="12" y="28" width="40" height="28" fill="#FFF8E1"/>
    <!-- Prateleiras/produtos -->
    <rect x="16" y="32" width="12" height="8" rx="1" fill="#4CAF50"/>
    <rect x="30" y="32" width="8" height="8" rx="1" fill="#FF9800"/>
    <rect x="40" y="32" width="8" height="8" rx="1" fill="#2196F3"/>
    <rect x="16" y="44" width="8" height="8" rx="1" fill="#9C27B0"/>
    <rect x="26" y="44" width="10" height="8" rx="1" fill="#F44336"/>
    <rect x="38" y="44" width="10" height="8" rx="1" fill="#00BCD4"/>
  </svg>

  <!-- Marcenaria - Madeira/Serra -->
  <svg
    v-else-if="icon === 'hammer'"
    :class="sizeClasses[size]"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Tábua de madeira -->
    <rect x="8" y="28" width="48" height="20" rx="2" fill="#8D6E63"/>
    <line x1="8" y1="33" x2="56" y2="33" stroke="#6D4C41" stroke-width="1"/>
    <line x1="8" y1="38" x2="56" y2="38" stroke="#6D4C41" stroke-width="1"/>
    <line x1="8" y1="43" x2="56" y2="43" stroke="#6D4C41" stroke-width="1"/>
    <!-- Serra circular -->
    <circle cx="44" cy="20" r="12" fill="#BDBDBD" stroke="#757575" stroke-width="2"/>
    <circle cx="44" cy="20" r="3" fill="#424242"/>
    <!-- Dentes da serra -->
    <path d="M44 8L46 12L42 12Z" fill="#616161"/>
    <path d="M44 32L46 28L42 28Z" fill="#616161"/>
    <path d="M32 20L36 22L36 18Z" fill="#616161"/>
    <path d="M56 20L52 22L52 18Z" fill="#616161"/>
    <!-- Serragem -->
    <circle cx="20" cy="52" r="2" fill="#D7CCC8"/>
    <circle cx="28" cy="54" r="1.5" fill="#BCAAA4"/>
    <circle cx="36" cy="52" r="2" fill="#D7CCC8"/>
  </svg>

  <!-- Eletricista - Raio -->
  <svg
    v-else-if="icon === 'bolt'"
    :class="sizeClasses[size]"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Círculo de fundo -->
    <circle cx="32" cy="32" r="24" fill="#FFF3E0"/>
    <!-- Raio principal -->
    <path d="M36 8L20 32H30L24 56L48 28H36L42 8H36Z" fill="#FF9800"/>
    <path d="M34 12L22 32H30L26 50L44 30H36L40 12H34Z" fill="#FFB300"/>
    <!-- Faíscas -->
    <circle cx="14" cy="20" r="2" fill="#FFCA28"/>
    <circle cx="50" cy="44" r="2" fill="#FFCA28"/>
    <circle cx="18" cy="48" r="1.5" fill="#FFE082"/>
    <!-- Pessoa com capacete -->
    <circle cx="48" cy="14" r="6" fill="#FFE0B2"/>
    <path d="M42 12H54V10C54 8 52 6 48 6C44 6 42 8 42 10V12Z" fill="#FFC107"/>
  </svg>

  <!-- Outros - Grid/Categorias -->
  <svg
    v-else-if="icon === 'grid'"
    :class="sizeClasses[size]"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Grid 2x2 com cores variadas -->
    <rect x="8" y="8" width="22" height="22" rx="4" fill="#FF7043"/>
    <rect x="34" y="8" width="22" height="22" rx="4" fill="#42A5F5"/>
    <rect x="8" y="34" width="22" height="22" rx="4" fill="#66BB6A"/>
    <rect x="34" y="34" width="22" height="22" rx="4" fill="#FFCA28"/>
    <!-- Ícones dentro de cada quadrado -->
    <circle cx="19" cy="19" r="4" fill="#FFCCBC"/>
    <rect x="42" y="15" width="8" height="8" rx="1" fill="#BBDEFB"/>
    <path d="M15 41L19 49L23 41H15Z" fill="#C8E6C9"/>
    <path d="M45 38L49 42L45 46L41 42L45 38Z" fill="#FFF8E1"/>
  </svg>

  <!-- Building icon para confirmação -->
  <svg
    v-else-if="icon === 'building'"
    :class="sizeClasses[size]"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Prédio principal -->
    <rect x="12" y="16" width="40" height="40" rx="2" fill="#E3F2FD"/>
    <rect x="12" y="16" width="40" height="40" rx="2" stroke="#1976D2" stroke-width="2"/>
    <!-- Janelas -->
    <rect x="18" y="22" width="8" height="8" rx="1" fill="#1976D2"/>
    <rect x="28" y="22" width="8" height="8" rx="1" fill="#1976D2"/>
    <rect x="38" y="22" width="8" height="8" rx="1" fill="#1976D2"/>
    <rect x="18" y="34" width="8" height="8" rx="1" fill="#1976D2"/>
    <rect x="28" y="34" width="8" height="8" rx="1" fill="#1976D2"/>
    <rect x="38" y="34" width="8" height="8" rx="1" fill="#1976D2"/>
    <!-- Porta -->
    <rect x="26" y="46" width="12" height="10" rx="1" fill="#1565C0"/>
    <!-- Teto -->
    <path d="M10 16L32 4L54 16H10Z" fill="#1976D2"/>
  </svg>

  <!-- Fallback -->
  <div
    v-else
    :class="[sizeClasses[size], 'bg-gray-200 rounded-lg flex items-center justify-center']"
  >
    <span class="text-gray-500 text-xs">?</span>
  </div>
</template>
