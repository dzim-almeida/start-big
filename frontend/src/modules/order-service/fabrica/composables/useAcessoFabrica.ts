/**
 * @fileoverview O que a pessoa pode na fábrica — a linha "Fábrica" de Cargos
 * (backend: app/services/fabrica/permissoes.py). O backend confere de novo em
 * cada rota; aqui é só para não mostrar o que daria 403.
 *
 * - podeGerenciar: orçar, enviar, registrar a resposta do cliente, liberar compra;
 * - podeVerCusto: custo e margem do orçamento (Gerenciar inclui).
 * Avançar e voltar etapa é de quem trabalha na OS (permissão de Serviços).
 */

import { computed } from 'vue';

import { useCheckPermission } from '@/modules/mainLayout/composables/useCheckPermission';
import { PERMISSIONS } from '@/shared/constants/permissions.constants';

export function useAcessoFabrica() {
  const { hasPermission } = useCheckPermission();

  const podeGerenciar = computed(() => hasPermission(PERMISSIONS.manageFabrica));
  const podeVerCusto = computed(() => hasPermission(PERMISSIONS.viewFabricaCustos));

  return { podeGerenciar, podeVerCusto };
}
