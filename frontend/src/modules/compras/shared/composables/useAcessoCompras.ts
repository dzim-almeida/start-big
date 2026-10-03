/**
 * @fileoverview A loja tem Compras, e o cargo deixa usar?
 *
 * Duas perguntas, como no backend (services/compras/permissoes.py):
 * - `moduloAtivo`: a LOJA contratou (licença). Sem resposta da licença = não.
 * - `podeVer` / `podeGerenciar`: a PESSOA pode (linha "Compras" de Cargos).
 *
 * O backend confere de novo em cada rota — aqui é só para não mostrar o que
 * daria 403.
 */

import { computed } from 'vue';

import { useCheckPermission } from '@/modules/mainLayout/composables/useCheckPermission';
import { MODULOS } from '@/shared/constants/modulos.constants';
import { PERMISSIONS } from '@/shared/constants/permissions.constants';
import { useModulosStore } from '@/shared/stores/modulos.store';

export function useAcessoCompras() {
  const modulosStore = useModulosStore();
  const { hasPermission } = useCheckPermission();

  const moduloAtivo = computed(() => modulosStore.temModulo(MODULOS.COMPRAS));
  /** Linha Compras OU linha Recebimento (o almoxarife também lê, sem preço). */
  const podeVer = computed(
    () => moduloAtivo.value && (hasPermission(PERMISSIONS.purchases) || hasPermission(PERMISSIONS.receiving)),
  );
  /** Dar entrada no que chegou — caixa de receber, ou quem gerencia compras. */
  const podeReceber = computed(() => moduloAtivo.value && hasPermission(PERMISSIONS.receivePurchases));
  const podeGerenciar = computed(() => moduloAtivo.value && hasPermission(PERMISSIONS.managePurchases));
  /** Preço de compra (D14). O backend já manda nulo para quem não pode. */
  const podeVerCusto = computed(() => moduloAtivo.value && hasPermission(PERMISSIONS.viewPurchaseCosts));

  /** Cancelar pedido — a caixa Excluir da linha Compras. */
  const podeCancelar = computed(() => moduloAtivo.value && hasPermission(PERMISSIONS.cancelPurchases));

  return { moduloAtivo, podeVer, podeGerenciar, podeVerCusto, podeCancelar, podeReceber };
}
