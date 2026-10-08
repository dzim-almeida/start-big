/**
 * @fileoverview Atalho "Etiqueta de envio" da lista de vendas.
 *
 * Leva à aba Etiquetas › Envio já com a venda escolhida (a ProductsView lê o
 * `?envio=venda:id` e o apaga da URL). As rotas do envio no backend conferem a
 * permissão de vendas — o atalho não abre dado que o usuário não veria.
 */

import type { RouteLocationRaw } from 'vue-router';

export function rotaEtiquetaEnvio(vendaId: number): RouteLocationRaw {
  return { path: '/produtos', query: { envio: `venda:${vendaId}` } };
}
