/**
 * @fileoverview Permissões do orçamento num lugar só (Spec 06B §7.3).
 *
 * Serve às telas que ainda NÃO têm um orçamento carregado (menu, lista,
 * atalhos). Dentro do editor, quem decide é a resposta da API (`acoes` e
 * `inclui_custos`, D13): o backend é a regra única.
 *
 * Atenção: o `hasPermission` do projeto não considera o `is_master` (04B §6.2),
 * então o dono do sistema é tratado aqui, como no resto do projeto.
 */
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

import { useCheckPermission } from '@/modules/mainLayout/composables/useCheckPermission';
import { PERMISSIONS } from '@/shared/constants/permissions.constants';
import { useAuthStore } from '@/shared/stores/auth.store';
import type { Permissions } from '@/shared/types/auth.types';

export function usePermissoesOrcamento() {
  const { hasPermission } = useCheckPermission();            // permissões do cargo
  const { userData } = storeToRefs(useAuthStore());          // usuário logado
  // Dono do sistema passa em tudo (padrão do projeto).
  const isMaster = computed(() => userData.value?.is_master === true);
  // Uma "pergunta" reativa por chave: muda sozinha se o cargo for recarregado.
  const pode = (chave: Permissions) => computed(() => isMaster.value || hasPermission(chave));

  return {
    /** Menu e lista. */
    podeVer: pode(PERMISSIONS.viewOrcamentosMarcenaria),
    /** Botões "Novo orçamento" (lista, atalho e tela de OS). */
    podeGerir: pode(PERMISSIONS.manageOrcamentosMarcenaria),
    /** Excluir rascunho nunca enviado. */
    podeExcluir: pode(PERMISSIONS.deleteOrcamentosMarcenaria),
    /** Coluna "Margem" da lista e custos na busca de insumos (04B). */
    podeVerCustos: pode(PERMISSIONS.viewCustosMarcenaria),
    /** Cadastro rápido de insumo (D35): a mesma chave que o `POST /produtos` exige. */
    podeCriarProduto: pode(PERMISSIONS.products),
    /** Funcionário do usuário logado (vendedor padrão, D22). */
    funcionarioId: computed(() => userData.value?.funcionario_id ?? null),
  };
}
