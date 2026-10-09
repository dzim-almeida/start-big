/**
 * @fileoverview Escapa texto digitado pelo usuário antes de ir para um lugar
 * que interpreta HTML.
 *
 * O `BaseConfirmModal` mostra a descrição com `v-html` (aceita <strong>). Um
 * ambiente chamado `<img src=x onerror=...>` viraria código rodando na tela;
 * escapado, aparece só como texto.
 */
const TROCAS: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

/** "<b>Sala</b>" → "&lt;b&gt;Sala&lt;/b&gt;" (aparece igual ao digitado, sem virar HTML). */
export function escaparHtml(texto: string): string {
  return texto.replace(/[&<>"']/g, (caractere) => TROCAS[caractere]);
}
