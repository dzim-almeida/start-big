/**
 * @fileoverview Formatação dos códigos da NFS-e Nacional.
 *
 * O banco guarda só os dígitos; a tela mostra como o portal da NFS-e e o
 * contador escrevem — é assim que o lojista os reconhece na nota antiga.
 */

const apenasDigitos = (valor: string | null | undefined) => (valor ?? '').replace(/\D/g, '');

/** "010701" → "01.07.01" (item, subitem e desdobro da LC 116). */
export function formatarCodigoNacional(valor: string | null | undefined): string {
  const d = apenasDigitos(valor);
  return d.length === 6 ? `${d.slice(0, 2)}.${d.slice(2, 4)}.${d.slice(4)}` : d;
}

/** "115013000" → "1.1501.30.00". */
export function formatarNbs(valor: string | null | undefined): string {
  const d = apenasDigitos(valor);
  return d.length === 9 ? `${d.slice(0, 1)}.${d.slice(1, 5)}.${d.slice(5, 7)}.${d.slice(7)}` : d;
}
