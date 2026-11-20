/**
 * @fileoverview Descrição dos modais de confirmação sem HTML (LIC-04 §6.3, D-17).
 *
 * Antes, a descrição era um texto com HTML (`<strong>`), mostrado com `v-html`:
 * um nome digitado como `<img src=x onerror=...>` virava código rodando na tela.
 * Agora a descrição é texto puro, ou uma lista de trechos, em que o destaque é
 * um objeto `{ negrito: '...' }`. O Vue mostra cada trecho como TEXTO: nada do
 * que o usuário digitou é tratado como HTML.
 *
 * Exemplo: ['Excluir o móvel ', { negrito: movel.nome }, '?']
 */

/** Um pedaço da descrição: texto normal, ou texto em negrito. */
export type TrechoDescricao = string | { negrito: string };

/** A descrição inteira: um texto só, ou uma lista de trechos. */
export type DescricaoConfirmacao = string | TrechoDescricao[];
