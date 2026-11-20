/**
 * @fileoverview O ÚNICO lugar que sabe onde o token do login do ERP fica
 * (LIC-04 §6.2, ADR-003, ACORDO D-27).
 *
 * O token fica na `sessionStorage`: ela sobrevive a recarregar a página, mas o
 * navegador (e a janela do Tauri) a apaga ao fechar a janela. Por isso o sistema
 * pede login toda vez que é aberto, e o token nunca é gravado em disco.
 *
 * Os outros arquivos chamam estas funções; nunca usam sessionStorage nem
 * localStorage direto para o token. Este arquivo não importa nada, então não
 * entra em importação circular com o axios.
 */

/** Nome da chave na sessionStorage. É o mesmo nome que as versões antigas usavam. */
const CHAVE = 'access_token';

/** Guarda o token depois do login ou do setup. */
export function guardarToken(token: string): void {
  sessionStorage.setItem(CHAVE, token); // sobrevive a recarregar a página, some ao fechar a janela
}

/** Lê o token da janela atual. `null` = ninguém logado nesta janela. */
export function lerToken(): string | null {
  return sessionStorage.getItem(CHAVE);
}

/** Apaga o token: logout ou sessão expirada. */
export function apagarToken(): void {
  sessionStorage.removeItem(CHAVE);
}

/**
 * Apaga o token que versões antigas do app gravaram no `localStorage` (que é
 * gravado em disco). Chamado uma vez, ao abrir o app (`App.vue`).
 */
export function limparTokenAntigo(): void {
  localStorage.removeItem(CHAVE);
}
