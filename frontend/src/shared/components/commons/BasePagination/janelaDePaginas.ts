/**
 * Os números de página que a paginação mostra: no máximo `tamanho` (3), com a
 * página atual no meio. Nas pontas a janela encosta, para continuar mostrando
 * `tamanho` números: página 1 de 10 → [1, 2, 3]; página 10 de 10 → [8, 9, 10].
 */
export function janelaDePaginas(atual: number, total: number, tamanho = 3): number[] {
  if (total <= 0) return [];
  const pagina = Math.min(Math.max(1, atual), total);
  const quantos = Math.min(tamanho, total);
  const inicio = Math.min(Math.max(1, pagina - Math.floor(quantos / 2)), total - quantos + 1);
  return Array.from({ length: quantos }, (_, i) => inicio + i);
}
