/**
 * @fileoverview Textos e regras de tela dos terceirizados (Spec 11B D2, D3).
 * Nenhuma regra de negócio aqui: a situação vem pronta da API (11A); isto só
 * decide o que MOSTRAR e quais botões habilitar.
 */
import { formatDataPura, parseDataPura } from '@/shared/utils/date.utils';

import type { MovelTerceirizado, SituacaoTerceirizado } from '../schemas/terceirizado.schema';

/** A situação como o usuário lê. */
export const ROTULO_SITUACAO: Record<SituacaoTerceirizado, string> = {
  A_PEDIR: 'A pedir',
  ENVIADO: 'Pedido enviado',
  RECEBIDO: 'Recebido',
  CONFERIDO: 'Conferido',
};

/**
 * O selo da linha (D2): "Pedido em rascunho" quando o pedido do Compras ainda
 * não saiu; "Recebido com problema" quando há problema registrado.
 */
export function seloDaSituacao(movel: MovelTerceirizado): { texto: string; classe: string } {
  if (movel.situacao === 'A_PEDIR' && movel.pedido?.origem === 'COMPRAS') {
    return { texto: 'Pedido em rascunho', classe: 'bg-zinc-100 text-zinc-700 border-zinc-200' };
  }
  if (movel.situacao === 'RECEBIDO' && movel.problema) {
    return { texto: 'Recebido com problema', classe: 'bg-red-50 text-red-700 border-red-200' };
  }
  const classes: Record<SituacaoTerceirizado, string> = {
    A_PEDIR: 'bg-zinc-100 text-zinc-700 border-zinc-200',
    ENVIADO: 'bg-blue-50 text-blue-700 border-blue-200',
    RECEBIDO: 'bg-amber-50 text-amber-800 border-amber-200',
    CONFERIDO: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  };
  return { texto: ROTULO_SITUACAO[movel.situacao], classe: classes[movel.situacao] };
}

/** "PC-000123" (Compras), "Pedido 4521" (anotado com número) ou "Pedido anotado". */
export function nomeDoPedido(movel: MovelTerceirizado): string | null {
  const pedido = movel.pedido;
  if (!pedido) return null;
  if (pedido.origem === 'COMPRAS') return pedido.codigo;
  return pedido.numero ? `Pedido ${pedido.numero}` : 'Pedido anotado';
}

/** "PC-000123 · chega 20/10" (Compras) ou "Pedido 4521 · chega 20/10" (à mão). */
export function textoDoPedido(movel: MovelTerceirizado): string | null {
  const nome = nomeDoPedido(movel);
  if (!nome) return null;
  // A previsão só interessa enquanto o móvel está a caminho; "20/10" sem o ano.
  const chega = movel.previsao && movel.situacao === 'ENVIADO' ? ` · chega ${formatDataPura(movel.previsao).slice(0, 5)}` : '';
  return `${nome}${chega}`;
}

/** Dias de atraso em relação à previsão (o backend já disse SE está atrasado). */
export function diasDeAtraso(movel: MovelTerceirizado, hoje = new Date()): number {
  if (!movel.atrasado || !movel.previsao) return 0;
  const previsao = parseDataPura(movel.previsao);
  const inicioDeHoje = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  return Math.max(1, Math.round((inicioDeHoje.getTime() - previsao.getTime()) / 86_400_000));
}

/** "700 × 2200 × 600 mm" (só as medidas preenchidas). */
export function textoDasMedidas(movel: MovelTerceirizado): string {
  const { largura_mm: l, altura_mm: a, profundidade_mm: p } = movel.medidas;
  const partes = [l, a, p].filter((m): m is number => m != null && m > 0);
  return partes.length ? `${partes.join(' × ')} mm` : '';
}

export type AcaoEmLote = 'pedir' | 'enviar' | 'receber' | 'conferir';

/** De onde cada ação parte (11A D1). */
const ORIGEM: Record<AcaoEmLote, SituacaoTerceirizado> = {
  pedir: 'A_PEDIR', enviar: 'A_PEDIR', receber: 'ENVIADO', conferir: 'RECEBIDO',
};

/**
 * D3: a ação só habilita quando TODOS os marcados partem da situação certa e
 * são da mesma central (um pedido cobre vários móveis). O motivo vai no `title`.
 */
export function podeAplicar(acao: AcaoEmLote, marcados: MovelTerceirizado[]): { ok: boolean; motivo?: string } {
  const origem = ORIGEM[acao];
  if (!marcados.length) return { ok: false, motivo: 'Marque pelo menos um móvel.' };
  if (acao !== 'conferir' && new Set(marcados.map((m) => m.central?.id ?? null)).size > 1) {
    return { ok: false, motivo: 'Marque móveis da mesma central.' };
  }
  if (marcados.some((m) => m.situacao !== origem)) return { ok: false, motivo: `Só móveis "${ROTULO_SITUACAO[origem]}".` };
  if ((acao === 'pedir' || acao === 'enviar') && marcados.some((m) => m.pedido?.origem === 'COMPRAS')) {
    return { ok: false, motivo: 'Há móvel com pedido em rascunho no Compras.' };
  }
  if (acao === 'receber' && marcados.some((m) => m.pedido?.origem === 'COMPRAS')) {
    return { ok: false, motivo: 'Móvel com pedido no Compras é recebido por lá.' };
  }
  return { ok: true };
}

/** Para qual situação o "voltar um passo" leva (a confirmação diz, 11B D7). */
export function voltaPara(movel: MovelTerceirizado): SituacaoTerceirizado | null {
  if (movel.situacao === 'CONFERIDO') return 'RECEBIDO';
  if (movel.pedido?.origem === 'COMPRAS') return null;     // os outros passos voltam pelo Compras
  if (movel.situacao === 'RECEBIDO') return 'ENVIADO';
  if (movel.situacao === 'ENVIADO') return 'A_PEDIR';
  return null;
}

/**
 * A data de HOJE no relógio da loja, como a API espera ("2026-10-09").
 * Não usa `toISOString()`: ele está em UTC, e depois das 21h no Brasil já
 * seria amanhã.
 */
export function hojeIso(agora = new Date()): string {
  const mes = String(agora.getMonth() + 1).padStart(2, '0');   // getMonth() começa em 0
  const dia = String(agora.getDate()).padStart(2, '0');
  return `${agora.getFullYear()}-${mes}-${dia}`;
}
