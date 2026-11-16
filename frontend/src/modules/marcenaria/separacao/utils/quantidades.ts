/**
 * @fileoverview Quantidades da separação: a API fala em MILÉSIMOS (inteiros,
 * PR4); a tela mostra "3 un", "26,35 m" com a unidade do produto (10B D4).
 * Nenhuma conta de negócio aqui: só conversão para mostrar e para enviar.
 */
import { formatarNumeroQuantidade, formatarQuantidade, unidadeEhFracionada } from '@/shared/utils/quantidade';
import { lerNumeroDigitado } from '@/modules/marcenaria/orcamentos/utils/conversoes';

/** 3000 + "UN" → "3 un"; 26350 + "M" → "26,35 m" (as casas da unidade). */
export const quantidadeComUnidade = (milesimos: number, unidade: string): string =>
  formatarQuantidade(milesimos / 1000, unidade);

/** Só o número, para o campo do modal: 3000 → "3"; 26350 + "M" → "26,35". */
export const quantidadeParaCampo = (milesimos: number, unidade: string): string =>
  formatarNumeroQuantidade(milesimos / 1000, unidade);

/** Planejado do móvel, sem a unidade ("Balcão 2,2"): até 3 casas, como veio. */
export const quantidadeSimples = (milesimos: number): string =>
  (milesimos / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 3 });

/**
 * O que foi digitado no campo → milésimos, ou uma frase de erro.
 * Unidade inteira (un, chapa, par) não aceita fração: "1,5 un" não existe.
 */
export function lerQuantidade(texto: string, unidade: string): { milesimos: number } | { erro: string } {
  const numero = lerNumeroDigitado(texto.trim());
  if (numero == null || numero <= 0) return { erro: 'A quantidade deve ser maior que zero.' };
  if (!unidadeEhFracionada(unidade) && !Number.isInteger(numero)) {
    return { erro: 'Esta unidade não aceita fração: informe um número inteiro.' };
  }
  return { milesimos: Math.round(numero * 1000) };
}

/** Orçado × real (10B D11): +1200 bp → "+12%"; −909 → "−9,1%"; 0 → "0%". */
export function diferencaTexto(bp: number): string {
  const percentual = (Math.abs(bp) / 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 });
  if (bp > 0) return `+${percentual}%`;
  if (bp < 0) return `−${percentual}%`;
  return '0%';
}
