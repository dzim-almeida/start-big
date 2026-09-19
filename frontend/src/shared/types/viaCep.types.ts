/**
 * Response da API ViaCEP
 */
export interface ViaCepResponse {
  cep: string;
  logradouro: string;
  complemento: string;
  bairro: string;
  localidade: string;
  uf: string;
  /** Código IBGE do município (7 dígitos) — a NF-e exige no destinatário. */
  ibge?: string;
  erro?: boolean;
}