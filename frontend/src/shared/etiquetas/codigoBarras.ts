/**
 * @fileoverview Escolha e validação da simbologia do código de barras
 * (docs/etiquetas-plano.md §5.2).
 *
 * Regra de ouro: um EAN com dígito verificador errado NÃO vira um EAN errado
 * no papel — o leitor do caixa o recusaria, ou pior, leria outro produto. Ele
 * cai para Code 128, que codifica qualquer texto, e a tela avisa.
 */

/** Formatos que o renderizador sabe desenhar (nomes do JsBarcode). */
export type Simbologia = 'EAN13' | 'EAN8' | 'UPC' | 'ITF14' | 'CODE128';

export type SimbologiaPreferida = 'auto' | Simbologia;

export interface CodigoResolvido {
  simbologia: Simbologia;
  valor: string;
  /** Preenchido quando a preferência não pôde ser atendida. */
  aviso?: string;
}

const COMPRIMENTO_GTIN: Record<Exclude<Simbologia, 'CODE128'>, number> = {
  EAN13: 13,
  EAN8: 8,
  UPC: 12,
  ITF14: 14,
};

/** Dígito verificador GS1 (módulo 10, pesos 3 e 1 da direita para a esquerda). */
export function digitoVerificadorGs1(corpo: string): number {
  let soma = 0;
  for (let i = 0; i < corpo.length; i++) {
    const digito = Number(corpo[corpo.length - 1 - i]);
    soma += digito * (i % 2 === 0 ? 3 : 1);
  }
  return (10 - (soma % 10)) % 10;
}

/** GTIN-8/12/13/14 com dígito verificador certo. */
export function gtinValido(valor: string): boolean {
  if (!/^\d+$/.test(valor) || ![8, 12, 13, 14].includes(valor.length)) return false;
  return digitoVerificadorGs1(valor.slice(0, -1)) === Number(valor[valor.length - 1]);
}

function simbologiaPorComprimento(valor: string): Simbologia | null {
  if (!gtinValido(valor)) return null;
  switch (valor.length) {
    case 13: return 'EAN13';
    case 8: return 'EAN8';
    case 12: return 'UPC';
    case 14: return 'ITF14';
    default: return null;
  }
}

/**
 * Decide como o valor sai no papel. `null` quando não há o que imprimir.
 *
 * Code 128 aceita só ASCII imprimível: acento vira o caractere sem acento, o
 * resto sai — é código interno digitado à mão, não dado fiscal.
 */
export function resolverCodigo(bruto: string | null | undefined, preferida: SimbologiaPreferida = 'auto'): CodigoResolvido | null {
  const valor = (bruto ?? '').trim();
  if (!valor) return null;

  const natural = simbologiaPorComprimento(valor);

  if (preferida === 'auto') {
    return natural ? { simbologia: natural, valor } : { simbologia: 'CODE128', valor: paraCode128(valor) };
  }
  if (preferida === 'CODE128') return { simbologia: 'CODE128', valor: paraCode128(valor) };

  if (valor.length === COMPRIMENTO_GTIN[preferida] && gtinValido(valor)) {
    return { simbologia: preferida, valor };
  }
  return {
    simbologia: 'CODE128',
    valor: paraCode128(valor),
    aviso: `"${valor}" não é um ${nomeSimbologia(preferida)} válido — impresso em Code 128.`,
  };
}

export function nomeSimbologia(simbologia: Simbologia): string {
  return { EAN13: 'EAN-13', EAN8: 'EAN-8', UPC: 'UPC-A', ITF14: 'ITF-14 (DUN-14)', CODE128: 'Code 128' }[simbologia];
}

function paraCode128(valor: string): string {
  return valor
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^\x20-\x7e]/g, '');
}
