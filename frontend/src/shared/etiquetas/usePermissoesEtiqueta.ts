/**
 * @fileoverview O que o cargo do usuário deixa fazer nas etiquetas (linha
 * "Etiquetas" da tela de Cargos). O backend confere de novo em cada rota —
 * aqui é só para não mostrar botão que daria 403.
 */

import { computed } from 'vue';

import { useCheckPermission } from '@/modules/mainLayout/composables/useCheckPermission';
import { PERMISSIONS } from '@/shared/constants/permissions.constants';

export function usePermissoesEtiqueta() {
  const { hasPermission } = useCheckPermission();
  return {
    podeVer: computed(() => hasPermission(PERMISSIONS.labels)),
    podeGerenciar: computed(() => hasPermission(PERMISSIONS.manageLabels)),
    podeExcluir: computed(() => hasPermission(PERMISSIONS.deleteLabels)),
  };
}
