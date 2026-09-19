import { computed, ref, type Ref } from 'vue';

import { parseTimestampBackend } from '@/shared/utils/date.utils';

import type {
  DestinatarioAvulsoPayload,
  DocumentoFiscalRead,
  DocumentoItemResumo,
  ItemDevolucaoPayload,
} from '../types/fiscal.types';

/**
 * Lógica da devolução, sem componente: saldo por item, validação de
 * quantidade, total estimado e a janela legal de cancelamento. Tudo em
 * MILÉSIMOS (1000 = 1 UN), como o backend, para a devolução parcial não
 * perder a fração.
 */

export const MILESIMOS = 1000;

/** Janela legal para cancelar, contada da autorização — a mesma do backend. */
export const JANELA_CANCELAMENTO_MS = {
  NFE: 24 * 60 * 60 * 1000,
  NFCE: 30 * 60 * 1000,
} as const;

export const MOTIVO_DEVOLUCAO_MINIMO = 15;
export const MOTIVO_DEVOLUCAO_MAXIMO = 255;

export interface ItemDevolucaoLocal {
  documentoItemId: number;
  nome: string;
  valorUnitario: number;
  quantidadeOriginalMil: number;
  saldoDisponivelMil: number;
  qtdDevolverMil: number;
  selecionado: boolean;
}

/** Passado o prazo, o cancelamento é impossível e a via é a devolução. */
export function prazoCancelamentoExpirado(
  documento: Pick<DocumentoFiscalRead, 'tipo_documento' | 'data_autorizacao' | 'data_emissao'>,
  agora: number = Date.now(),
): boolean {
  const referencia = documento.data_autorizacao ?? documento.data_emissao;
  if (!referencia) return false;
  // O backend serializa UTC SEM fuso; `Date.parse` leria como hora local e
  // deslocaria a janela pelo offset (3 h no Brasil) -- o cupom de 40 min
  // ainda mostraria "Cancelar".
  const inicio = parseTimestampBackend(referencia).getTime();
  if (Number.isNaN(inicio)) return false;
  const janela =
    documento.tipo_documento === 'NFCE' ? JANELA_CANCELAMENTO_MS.NFCE : JANELA_CANCELAMENTO_MS.NFE;
  return agora - inicio > janela;
}

function quantidadeMil(item: DocumentoItemResumo): number {
  return item.quantidade_milesimos ?? Math.round(item.quantidade * MILESIMOS);
}

export function saldoDisponivelMil(item: DocumentoItemResumo): number {
  return Math.max(0, quantidadeMil(item) - (item.quantidade_devolvida_acumulada ?? 0));
}

export function totalmenteDevolvida(itens: DocumentoItemResumo[]): boolean {
  return itens.length > 0 && itens.every((item) => saldoDisponivelMil(item) === 0);
}

/** Linhas do modal: nascem selecionadas com o saldo cheio (devolução total). */
export function montarItensLocais(itens: DocumentoItemResumo[]): ItemDevolucaoLocal[] {
  return itens
    .filter((item) => item.id != null)
    .map((item) => {
      const saldo = saldoDisponivelMil(item);
      return {
        documentoItemId: item.id as number,
        nome: item.nome,
        valorUnitario: item.valor_unitario,
        quantidadeOriginalMil: quantidadeMil(item),
        saldoDisponivelMil: saldo,
        qtdDevolverMil: saldo,
        selecionado: saldo > 0,
      };
    });
}

/** null = válida; senão a mensagem. Nunca deixa passar acima do saldo. */
export function validarQuantidade(qtdMil: number, saldoMil: number): string | null {
  if (!Number.isFinite(qtdMil) || qtdMil <= 0) return 'Informe uma quantidade maior que zero.';
  if (qtdMil > saldoMil) return `Acima do saldo disponível (${saldoMil / MILESIMOS}).`;
  return null;
}

/** Centavos: (milésimos / 1000) × unitário, só dos selecionados. */
export function valorTotalEstimado(itens: ItemDevolucaoLocal[]): number {
  return itens
    .filter((i) => i.selecionado)
    .reduce((soma, i) => soma + Math.round((i.qtdDevolverMil * i.valorUnitario) / MILESIMOS), 0);
}

const soDigitos = (v: string | null | undefined) => (v ?? '').replace(/\D/g, '');

/** Mesmas regras do `DestinatarioAvulsoRequest` do backend. */
export function destinatarioAvulsoValido(d: DestinatarioAvulsoPayload): boolean {
  const doc = soDigitos(d.cpf_ou_cnpj);
  if (doc.length !== 11 && doc.length !== 14) return false;
  if (soDigitos(d.cep).length !== 8) return false;
  if (!/^\d{7}$/.test(d.codigo_municipio)) return false;
  if (d.indicador_inscricao_estadual === 1 && !d.inscricao_estadual?.trim()) return false;
  return [d.nome_razao_social, d.logradouro, d.numero, d.bairro, d.municipio, d.uf].every(
    (campo) => (campo ?? '').trim().length > 0,
  );
}

/** Só dígitos onde o backend exige; o resto vai como digitado. */
export function sanitizarDestinatario(d: DestinatarioAvulsoPayload): DestinatarioAvulsoPayload {
  return {
    ...d,
    cpf_ou_cnpj: soDigitos(d.cpf_ou_cnpj),
    cep: soDigitos(d.cep),
    uf: d.uf.toUpperCase(),
  };
}

export function destinatarioAvulsoVazio(): DestinatarioAvulsoPayload {
  return {
    cpf_ou_cnpj: '',
    nome_razao_social: '',
    indicador_inscricao_estadual: 9,
    inscricao_estadual: null,
    logradouro: '',
    numero: '',
    complemento: null,
    bairro: '',
    codigo_municipio: '',
    municipio: '',
    uf: '',
    cep: '',
  };
}

/** Estado reativo do modal por cima das funções puras acima. */
export function useDevolucaoItens(itensOrigem: Ref<DocumentoItemResumo[]>) {
  const modo = ref<'TOTAL' | 'PARCIAL'>('TOTAL');
  const itens = ref<ItemDevolucaoLocal[]>(montarItensLocais(itensOrigem.value));

  function reiniciar() {
    modo.value = 'TOTAL';
    itens.value = montarItensLocais(itensOrigem.value);
  }

  const errosPorItem = computed<Record<number, string | null>>(() =>
    Object.fromEntries(
      itens.value.map((i) => [
        i.documentoItemId,
        i.selecionado ? validarQuantidade(i.qtdDevolverMil, i.saldoDisponivelMil) : null,
      ]),
    ),
  );

  const itensValidos = computed(
    () =>
      itens.value.some((i) => i.selecionado) &&
      Object.values(errosPorItem.value).every((e) => e === null),
  );

  const total = computed(() => valorTotalEstimado(itens.value));

  /** `null` = devolução total (o backend devolve todo o saldo restante). */
  function itensParaPayload(): ItemDevolucaoPayload[] | null {
    if (modo.value === 'TOTAL') return null;
    return itens.value
      .filter((i) => i.selecionado)
      .map((i) => ({ documento_item_id: i.documentoItemId, quantidade: i.qtdDevolverMil }));
  }

  return { modo, itens, errosPorItem, itensValidos, total, itensParaPayload, reiniciar };
}
