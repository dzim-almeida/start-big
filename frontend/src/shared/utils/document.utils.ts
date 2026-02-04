/**
 * Utilities para formatação e manipulação de documentos brasileiros
 * CNP, CPF, CEP, Telefone, etc
 */

/**
 * Formata CNPJ para exibição
 * @param cnpj - CNPJ sem formatação
 * @returns CNPJ formatado (XX.XXX.XXX/XXXX-XX)
 */
export function formatCNPJ(cnpj: string): string {
  const digits = cnpj.replace(/\D/g, '');
  if (digits.length !== 14) return cnpj;
  return digits.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
}

/**
 * Formata CPF para exibição
 * @param cpf - CPF sem formatação
 * @returns CPF formatado (XXX.XXX.XXX-XX)
 */
export function formatCPF(cpf: string): string {
  const digits = cpf.replace(/\D/g, '');
  if (digits.length !== 11) return cpf;
  return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

/**
 * Formata CEP para exibição
 * @param cep - CEP sem formatação
 * @returns CEP formatado (XXXXX-XXX)
 */
export function formatCEP(cep: string): string {
  const digits = cep.replace(/\D/g, '');
  if (digits.length !== 8) return cep;
  return digits.replace(/(\d{5})(\d{3})/, '$1-$2');
}

/**
 * Formata telefone para exibição
 * @param telefone - Telefone sem formatação
 * @returns Telefone formatado
 */
export function formatTelefone(telefone: string): string {
  const digits = telefone.replace(/\D/g, '');
  if (digits.length === 10) {
    return digits.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  }
  if (digits.length === 11) {
    return digits.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  }
  return telefone;
}

/**
 * Remove formatação de documento (CNPJ/CPF)
 * @param doc - Documento formatado
 * @returns Apenas dígitos
 */
export function unmaskDocument(doc: string): string {
  return doc.replace(/\D/g, '');
}

/**
 * Remove formatação de telefone
 * @param phone - Telefone formatado
 * @returns Apenas dígitos
 */
export function unmaskPhone(phone: string): string {
  return phone.replace(/\D/g, '');
}

/**
 * Remove formatação de CEP
 * @param cep - CEP formatado
 * @returns Apenas dígitos
 */
export function unmaskCep(cep: string): string {
  return cep.replace(/\D/g, '');
}
