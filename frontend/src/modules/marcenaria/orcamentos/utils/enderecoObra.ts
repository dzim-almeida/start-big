/**
 * Endereço da obra montado pelo modal (remodelação item 2).
 *
 * O orçamento guarda o endereço da obra como UM texto só (`endereco_obra`, até
 * 255 caracteres no banco). O modal pede o endereço em partes (CEP, rua,
 * número...) para ninguém esquecer nada, e esta função junta as partes no
 * texto que vai para o orçamento e para a proposta.
 *
 * É uma função "pura" (só recebe dados e devolve texto, sem tela nem API):
 * assim dá para testar sozinha.
 */

/** As partes do endereço, como o modal pede. Todas são texto; vazio = "não informado". */
export interface CamposEnderecoObra {
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  estado: string;
}

/** Limite do campo no banco (`endereco_obra`, String(255)). */
export const LIMITE_ENDERECO_OBRA = 255;

/** Campos em branco, para abrir o modal limpo. */
export function camposVazios(): CamposEnderecoObra {
  return { cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade: '', estado: '' };
}

/**
 * Junta as partes num texto só, pulando o que está em branco.
 *
 * Exemplo: "Avenida Paulista, 1000 - Sala 2, Bela Vista, São Paulo/SP, CEP 01310-100"
 */
export function montarEnderecoObra(campos: CamposEnderecoObra): string {
  // `.trim()` tira espaços das pontas: " Rua A " vira "Rua A".
  const c = {
    cep: campos.cep.trim(),
    logradouro: campos.logradouro.trim(),
    numero: campos.numero.trim(),
    complemento: campos.complemento.trim(),
    bairro: campos.bairro.trim(),
    cidade: campos.cidade.trim(),
    estado: campos.estado.trim().toUpperCase(),   // UF sempre maiúscula ("sp" → "SP")
  };

  // 1ª parte: "Rua, número - complemento" (o número e o complemento só entram se existirem).
  let rua = c.logradouro;
  if (c.numero) rua = rua ? `${rua}, ${c.numero}` : c.numero;
  if (c.complemento) rua = rua ? `${rua} - ${c.complemento}` : c.complemento;

  // Cidade e UF andam juntas: "São Paulo/SP"; com só uma delas, vai só ela.
  const cidadeUf = [c.cidade, c.estado].filter(Boolean).join('/');

  // O CEP aparece formatado "00000-000" quando tem os 8 dígitos.
  const digitosCep = c.cep.replace(/\D/g, '');                  // tira tudo que não é número
  const cep = digitosCep.length === 8 ? `CEP ${digitosCep.slice(0, 5)}-${digitosCep.slice(5)}` : '';

  // Junta as partes que sobraram, separadas por vírgula.
  return [rua, c.bairro, cidadeUf, cep].filter(Boolean).join(', ');
}
