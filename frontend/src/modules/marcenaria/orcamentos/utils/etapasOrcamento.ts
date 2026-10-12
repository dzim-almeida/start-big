/**
 * @fileoverview As etapas do orçamento no cabeçalho do editor (redesign
 * 10/2026): Rascunho → Enviado → Aprovado → OS.
 *
 * Vencido e Recusado param em "Enviado" (o selo de status ao lado diz o que
 * houve); Substituído não está em etapa nenhuma (a versão nova é que anda).
 */
import type { StatusOrcamento } from '../constants/orcamento.constants';

export type EstadoEtapa = 'concluida' | 'atual' | 'pendente';
export interface EtapaOrcamento { rotulo: string; estado: EstadoEtapa }

const ROTULOS = ['Rascunho', 'Enviado', 'Aprovado', 'OS'] as const;

/** Índice da etapa atual; -1 = nenhuma. */
function indiceAtual(status: StatusOrcamento | undefined, temOS: boolean): number {
  switch (status) {
    case undefined:
    case 'RASCUNHO':
      return 0;
    case 'ENVIADO':
    case 'VENCIDO':
    case 'RECUSADO':
      return 1;
    case 'APROVADO':
      return temOS ? 3 : 2;
    default:
      return -1;                                     // SUBSTITUIDO
  }
}

export function etapasDoOrcamento(status: StatusOrcamento | undefined, temOS: boolean): EtapaOrcamento[] {
  const atual = indiceAtual(status, temOS);
  return ROTULOS.map((rotulo, i) => ({
    rotulo,
    estado: atual < 0 ? 'pendente' : i < atual ? 'concluida' : i === atual ? 'atual' : 'pendente',
  }));
}
