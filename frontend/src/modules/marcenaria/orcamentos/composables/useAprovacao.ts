/**
 * @fileoverview Aprovar e desfazer a aprovação (Spec 08B §7.3).
 *
 * Os dois passam pela fila de escrita (06B D7): mandam a revisão do cache e a
 * resposta substitui o detalhe. Uma OS nasce (ou é cancelada): as listas de OS
 * e o painel do início ficam velhos e são invalidados.
 */
import { useQueryClient } from '@tanstack/vue-query';
import type { Ref } from 'vue';

import { dashboardKeys } from '@/modules/home/constants/dashboard.constants';
import { ORDER_SERVICE_QUERY_KEY, ORDER_SERVICE_STATS_QUERY_KEY } from '@/modules/order-service/ordens/constants/core.constant';

import type { AprovacaoEntrada, DesfazerEntrada } from '../schemas/aprovacao.schema';
import type { OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import { aprovarOrcamento, desfazerAprovacao } from '../services/aprovacao.service';
import { codigoDoErro } from '../utils/erros';
import type { FilaOrcamento } from './useFilaOrcamento';

export function useAprovacao(id: Ref<number | null>, fila: FilaOrcamento) {
  const queryClient = useQueryClient();

  /** Uma OS nasceu ou foi cancelada: a lista de OS e o dashboard recarregam quando vistos. */
  function invalidarOS() {
    void queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    void queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_STATS_QUERY_KEY] });
    void queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
  }

  /** Aprova pela fila. Devolve o detalhe novo, com `os` preenchido (o editor abre o OSCriadaModal). */
  async function aprovar(entrada: AprovacaoEntrada): Promise<OrcamentoDetalhe> {
    const orcamentoId = id.value!;
    const detalhe = await fila.enfileirar((revisao) => aprovarOrcamento(orcamentoId, revisao, entrada));
    invalidarOS();
    return detalhe;
  }

  /**
   * Desfaz. Quando a loja exige PIN para cancelar OS, a API responde
   * REQUER_APROVACAO_GERENTE: pede o PIN e reenvia (D17). PIN errado pede de
   * novo. Devolve null se o usuário desistir do PIN.
   */
  async function desfazer(
    entrada: DesfazerEntrada,
    /** `pinErrado`: true quando o PIN anterior foi recusado (a tela avisa antes de pedir de novo). */
    pedirPin: (pinErrado: boolean) => Promise<string | null>,
  ): Promise<OrcamentoDetalhe | null> {
    const orcamentoId = id.value!;
    let corpo = entrada;
    for (;;) {
      try {
        const detalhe = await fila.enfileirar((revisao) => desfazerAprovacao(orcamentoId, revisao, corpo));
        invalidarOS();
        return detalhe;
      } catch (erro) {
        const codigo = codigoDoErro(erro);
        if (codigo !== 'REQUER_APROVACAO_GERENTE' && codigo !== 'PIN_GERENTE_INVALIDO') throw erro;
        const pin = await pedirPin(codigo === 'PIN_GERENTE_INVALIDO');   // null = o usuário desistiu
        if (!pin) return null;
        corpo = { ...entrada, codigo_gerente: pin };
      }
    }
  }

  return { aprovar, desfazer };
}
