/**
 * @fileoverview As etapas da OS da marcenaria, na ordem em que a obra anda:
 * Aberta → Aguardando Material → Em Produção → Aguardando Entrega → Finalizada.
 *
 * O status gravado é o enum de todos os segmentos (Spec 01A); os rótulos vêm
 * do contrato do segmento (quem chama passa a função `rotulo`). "Aguardando
 * Material" é opcional: a OS pode ir de Aberta direto para Em Produção, e aí
 * a etapa aparece como já passada.
 */
import type { EtapaStepper } from '@/shared/components/ui/BaseStepper/BaseStepper.vue';

export const FLUXO_OS_MARCENARIA = ['ABERTA', 'AGUARDANDO_PECAS', 'EM_ANDAMENTO', 'AGUARDANDO_RETIRADA', 'FINALIZADA'] as const;

export type StatusDoFluxo = (typeof FLUXO_OS_MARCENARIA)[number];

/**
 * A linha de etapas para um status. Fora do fluxo (Cancelada, Aguardando
 * Aprovação…): tudo pendente — quem chama mostra o status à parte.
 */
export function etapasDaOS(status: string | null | undefined, rotulo: (status: string) => string): EtapaStepper[] {
  const atual = FLUXO_OS_MARCENARIA.indexOf(status as StatusDoFluxo);
  return FLUXO_OS_MARCENARIA.map((etapa, i) => ({
    rotulo: rotulo(etapa),
    // A última etapa (Finalizada) atingida é concluída, não "atual".
    estado: atual < 0 ? 'pendente' : i < atual || (i === atual && etapa === 'FINALIZADA') ? 'concluida' : i === atual ? 'atual' : 'pendente',
  }));
}

/**
 * O próximo passo do botão "Avançar" do rodapé. Finalizar NÃO entra aqui:
 * tem o próprio fluxo (pagamento, garantia) no botão Finalizar.
 */
export function proximoStatus(status: string | null | undefined): StatusDoFluxo | null {
  switch (status) {
    case 'ABERTA':
    case 'AGUARDANDO_PECAS':
      return 'EM_ANDAMENTO';
    case 'EM_ANDAMENTO':
      return 'AGUARDANDO_RETIRADA';
    default:
      return null;
  }
}
