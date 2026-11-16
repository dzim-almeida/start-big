/**
 * @fileoverview "Mover" a OS de status sem perder o formulário (Spec 12B D13).
 *
 * A pergunta da produção ("Mover a OS para Em Produção?") não pode gravar o
 * formulário inteiro: o marceneiro pode ter digitado uma observação na outra
 * aba e ainda não salvo. Aqui o PUT vai SÓ com `status`, e o modal aberto
 * recebe o novo status em dois lugares — no "persistido" (`localOSData`) e no
 * campo da tela —, sem tocar em mais nada.
 */
import type { ComputedRef, Ref } from 'vue';
import { useQueryClient } from '@tanstack/vue-query';

import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';
import type { OsStatusEnumDataType } from '../../schemas/enums/osEnums.schema';
import { updateOrderService } from '../../services/orderServiceUpdate.service';
import { ORDER_SERVICE_QUERY_KEY, OS_CUSTOMER_QUERY_KEY } from '../../constants/core.constant';

interface Dependencias {
  osNumber: ComputedRef<string | null>;
  currentOSData: ComputedRef<OrderServiceReadDataType | null>;
  localOSData: Ref<OrderServiceReadDataType | null>;
  /** O campo de status do formulário de edição (o resto do formulário não entra). */
  campoStatus: Ref<string | null | undefined>;
}

export function useOSAplicarStatus({ osNumber, currentOSData, localOSData, campoStatus }: Dependencias) {
  const queryClient = useQueryClient();

  /** Grava só o status. Erro: sobe para quem chamou (a aba mostra o toast). */
  async function aplicarStatusSalvo(status: OsStatusEnumDataType): Promise<void> {
    const numero = osNumber.value;
    if (!numero || !currentOSData.value) return;
    const os = await updateOrderService({ osNumber: numero, updatedOS: { status } });
    localOSData.value = { ...currentOSData.value, status: os.status };   // só o status muda no persistido
    campoStatus.value = os.status;                                       // e no campo da tela
    // A lista de OS e o histórico do cliente mostram o status: ficam velhos.
    void queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    void queryClient.invalidateQueries({ queryKey: OS_CUSTOMER_QUERY_KEY });
  }

  return { aplicarStatusSalvo };
}
