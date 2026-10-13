/**
 * Validade e prazo pelo calendário (remodelação item 7).
 *
 * O orçamento guarda validade e prazo de entrega em DIAS (o backend soma os
 * dias ao dia do envio / da aprovação). O calendário só ajuda a escolher:
 *   - escolheu uma data → vira "quantos dias depois da data-base";
 *   - tem os dias → mostra "que data isso dá".
 *
 * As datas aqui são "datas puras" no formato ISO ("2026-10-21"), sem hora,
 * para o fuso horário não empurrar o dia para trás.
 */
import { parseDataPura } from '@/shared/utils/date.utils';

const UM_DIA_MS = 24 * 60 * 60 * 1000;

/** Meia-noite local do dia: compara só o DIA, a hora não atrapalha a conta. */
function inicioDoDia(data: Date): Date {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate());
}

/** Data → "AAAA-MM-DD" (o `padStart` põe o zero na frente: 5 → "05"). */
export function paraIso(data: Date): string {
  const mes = String(data.getMonth() + 1).padStart(2, '0');
  const dia = String(data.getDate()).padStart(2, '0');
  return `${data.getFullYear()}-${mes}-${dia}`;
}

/**
 * Data-base da conta: o dia do evento (envio ou aprovação) se ele já
 * aconteceu; senão, hoje ("se enviar/aprovar hoje, dá tal data").
 * O backend manda o evento com hora ("2026-10-06T13:00:00"): só o dia importa.
 */
export function dataBase(evento: string | null | undefined, hoje: Date = new Date()): Date {
  return inicioDoDia(evento ? parseDataPura(evento.slice(0, 10)) : hoje);
}

/** Base + dias → a data, em ISO. Ex.: 06/10 + 15 dias = "2026-10-21". */
export function dataDepoisDe(base: Date, dias: number): string {
  const resultado = new Date(base.getFullYear(), base.getMonth(), base.getDate() + dias);
  return paraIso(resultado);
}

/**
 * Quantos dias da base até a data escolhida. Ex.: de 06/10 a "2026-10-21" = 15.
 * `Math.round` acerta a conta nos dias em que o relógio muda (horário de verão).
 */
export function diasAte(base: Date, dataIso: string): number {
  const alvo = inicioDoDia(parseDataPura(dataIso));
  return Math.round((alvo.getTime() - inicioDoDia(base).getTime()) / UM_DIA_MS);
}
