/**
 * @fileoverview Textos da validade do orçamento (Spec 06B §7.12, D49):
 * "vence em 2 dias", "vence hoje", "venceu há 3 dias".
 *
 * A validade é uma DATA PURA (o dia escolhido, sem hora): por isso usa
 * `parseDataPura`, que não converte fuso (senão o dia "andaria" para trás).
 */
import { parseDataPura } from '@/shared/utils/date.utils';

const UM_DIA_MS = 24 * 60 * 60 * 1000;

/** Meia-noite local do dia (para comparar dias inteiros, sem a hora atrapalhar). */
function inicioDoDia(data: Date): number {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate()).getTime();
}

/** Dias de hoje até a validade: 0 = vence hoje; negativo = já venceu. */
export function diasAteValidade(validade: string, hoje: Date = new Date()): number {
  return Math.round((inicioDoDia(parseDataPura(validade)) - inicioDoDia(hoje)) / UM_DIA_MS);
}

/** "vence em 2 dias" / "vence amanhã" / "vence hoje" / "venceu ontem" / "venceu há 3 dias". */
export function textoValidade(validade: string, hoje: Date = new Date()): string {
  const dias = diasAteValidade(validade, hoje);
  if (dias > 1) return `vence em ${dias} dias`;
  if (dias === 1) return 'vence amanhã';
  if (dias === 0) return 'vence hoje';
  if (dias === -1) return 'venceu ontem';
  return `venceu há ${-dias} dias`;
}

/** Cor do texto da validade: âmbar perto de vencer, vermelho vencido (D49). */
export function tomValidade(validade: string, hoje: Date = new Date()): 'normal' | 'atencao' | 'vencido' {
  const dias = diasAteValidade(validade, hoje);
  if (dias < 0) return 'vencido';
  if (dias <= 3) return 'atencao';
  return 'normal';
}
