/**
 * @fileoverview Atalho "Etiqueta de envio" da OS e da venda.
 *
 * Leva à aba Etiquetas › Envio já com a origem escolhida (a ProductsView lê o
 * `?envio=tipo:id` e o apaga da URL). As rotas do envio no backend conferem a
 * permissão de OS/venda — o atalho não abre dado que o usuário não veria.
 */

import type { RouteLocationRaw } from 'vue-router';

import type { TipoOrigemEnvio } from './envio';

export function rotaEtiquetaEnvio(tipo: TipoOrigemEnvio, id: number): RouteLocationRaw {
  return { path: '/produtos', query: { envio: `${tipo}:${id}` } };
}
