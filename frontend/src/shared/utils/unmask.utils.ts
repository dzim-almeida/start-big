/**
 * Formata um documento removendo caracteres especiais
 * @param documento - Documento formatado
 * @returns Documento apenas com números
 */
export function unmaskDocument(documento: string): string {
  return documento.replace(/\D/g, '');
}

/**
 * Formata um telefone removendo caracteres especiais
 * @param telefone - Telefone formatado
 * @returns Telefone apenas com números
 */
export function unmaskPhone(telefone: string): string {
  return telefone.replace(/\D/g, '');
}

/**
 * Formata um cep removendo caracteres especiais
 * @param cep - cep formatado
 * @returns cep apenas com números
 */
export function unmaskCep(cep: string): string {
  return cep.replace(/\D/g, '');
}