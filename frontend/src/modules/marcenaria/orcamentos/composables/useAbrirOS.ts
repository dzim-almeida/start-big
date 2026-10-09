/**
 * @fileoverview Abrir a OS gerada pela aprovação (Spec 08B D7, D12, §7.5).
 *
 * Usa o mesmo caminho do painel de notificações: busca a OS pelo número e a
 * entrega ao fluxo global de OS, que abre o modal de OS (montado no layout).
 */
import { ref } from 'vue';

import { useOSCreateFlow } from '@/modules/order-service/ordens/composables/useOSCreateFlow';
import { getUniqueOS } from '@/modules/order-service/ordens/services/orderServiceGet.service';
import { useToast } from '@/shared/composables/useToast';

import { mensagemDoErro } from '../utils/erros';

export function useAbrirOS() {
  const { openExistingOS } = useOSCreateFlow();
  const toast = useToast();
  const abrindo = ref(false);

  /** `opcoes.abaInicial`: a aba em que o modal abre (o quadro da fábrica usa 'producao', 12B D16). */
  async function abrirOS(numeroOs: string, opcoes: { abaInicial?: string } = {}): Promise<void> {
    if (abrindo.value) return;                       // clique duplo não abre duas vezes
    abrindo.value = true;
    try {
      openExistingOS(await getUniqueOS(numeroOs), false, opcoes);
    } catch (erro) {
      toast.error('Não foi possível abrir a OS.', mensagemDoErro(erro));
    } finally {
      abrindo.value = false;
    }
  }

  return { abrirOS, abrindo };
}
