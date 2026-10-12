/**
 * Consulta pública de CNPJ (BrasilAPI, dados da Receita Federal).
 *
 * Usada por Dados da Empresa (o emitente) e pelo cadastro de cliente PJ (o
 * destinatário). Era exclusiva de Dados da Empresa e ignorava o regime, que a
 * Receita informa: o primeiro cliente em produção era MEI (`opcao_pelo_mei`),
 * foi cadastrado como "1 - Simples Nacional" à mão e a SEFAZ recusou três
 * notas com a Rejeição 481 (06/10/2026).
 *
 * O que a Receita NÃO informa, e por isso continua manual:
 *   - Inscrição Estadual — é cadastro do ESTADO (SINTEGRA/CCC), não da Receita;
 *   - Lucro Presumido × Lucro Real — quem não é Simples nem MEI fica para o
 *     contador decidir; o campo não é preenchido.
 */

export interface DadosCnpj {
  razao_social: string;
  nome_fantasia: string;
  cnae_principal: string;
  cnaes_secundarios: string;
  natureza_juridica: string;
  data_abertura: string;
  email: string;
  telefone: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  estado: string;
  cep: string;
  codigo_ibge: string;
  /**
   * Valor de `REGIME_TRIBUTARIO_OPTIONS` quando a Receita responde com certeza:
   * 'MEI' (optante pelo SIMEI) ou 'Simples Nacional'. Vazio quando não é
   * nenhum dos dois ou a Receita não informa — aí quem decide é o contador.
   */
  regime_tributario: '' | 'MEI' | 'Simples Nacional';
}

function formatCNAECode(codigo: number): string {
  const str = String(codigo).padStart(7, '0');
  return `${str.slice(0, 4)}-${str.slice(4, 5)}/${str.slice(5)}`;
}

/**
 * Natureza jurídica no vocabulário do ERP.
 *
 * O MEI vem PRIMEIRO e pelo `opcao_pelo_mei`: na Receita, a natureza do MEI é
 * "Empresário (Individual)" — o mesmo texto do EI —, então só o texto nunca
 * chegaria a 'MEI'.
 */
export function mapNaturezaJuridica(texto: string, porte: string, optanteMei: boolean): string {
  if (optanteMei) return 'MEI';
  const t = (texto || '').toLowerCase();
  if (t.includes('microempreendedor')) return 'MEI';
  if (t.includes('individual de responsabilidade')) return 'EIRELI';
  if (t.includes('empresário') || t.includes('empresario')) return 'EI';
  if (t.includes('unipessoal')) return 'SLU';
  if (t.includes('anônima') || t.includes('anonima')) return 'SA';
  if (t.includes('limitada')) return 'LTDA';
  if (porte === 'MICRO EMPRESA') return 'ME';
  if (porte === 'EMPRESA DE PEQUENO PORTE') return 'EPP';
  return '';
}

/** Regime pelo que a Receita sabe: SIMEI vence Simples; `null`/false não afirma nada. */
export function mapRegimeTributario(
  opcaoPeloMei: boolean | null | undefined,
  opcaoPeloSimples: boolean | null | undefined,
): DadosCnpj['regime_tributario'] {
  if (opcaoPeloMei === true) return 'MEI';
  if (opcaoPeloSimples === true) return 'Simples Nacional';
  return '';
}

/** Converte a resposta crua da BrasilAPI. Separado do `fetch` para ser testável. */
export function converterRespostaBrasilApi(d: Record<string, any>): DadosCnpj {
  const logradouro = [d.descricao_tipo_logradouro, d.logradouro].filter(Boolean).join(' ').trim();
  const cnaesSecundarios = (d.cnaes_secundarios || [])
    .map((c: { codigo: number }) => formatCNAECode(c.codigo))
    .join(', ');

  return {
    razao_social: d.razao_social || '',
    nome_fantasia: d.nome_fantasia || '',
    cnae_principal: d.cnae_fiscal ? formatCNAECode(d.cnae_fiscal) : '',
    cnaes_secundarios: cnaesSecundarios,
    natureza_juridica: mapNaturezaJuridica(d.natureza_juridica || '', d.porte || '', d.opcao_pelo_mei === true),
    data_abertura: d.data_inicio_atividade || '',
    email: d.email || '',
    telefone: d.ddd_telefone_1 || '',
    logradouro,
    numero: d.numero || '',
    complemento: d.complemento || '',
    bairro: d.bairro || '',
    cidade: d.municipio || '',
    estado: d.uf || '',
    cep: d.cep ? String(d.cep) : '',
    // A BrasilAPI chama de `codigo_municipio_ibge`; o código antigo lia
    // `codigo_ibge`, que não existe, e o campo sempre ficava vazio.
    codigo_ibge: String(d.codigo_municipio_ibge ?? d.codigo_ibge ?? ''),
    regime_tributario: mapRegimeTributario(d.opcao_pelo_mei, d.opcao_pelo_simples),
  };
}

/**
 * Por que a consulta falhou (Spec 02 da marcenaria, D1):
 *   - NAO_ENCONTRADO: a Receita respondeu que o CNPJ não existe (404);
 *   - INDISPONIVEL: não deu para perguntar (sem rede, tempo esgotado, 429, 5xx).
 * Antes, as duas viravam "CNPJ não encontrado" e o usuário achava que tinha
 * digitado errado quando, na verdade, estava sem internet.
 */
export type MotivoFalhaCnpj = 'NAO_ENCONTRADO' | 'INDISPONIVEL';

export class ConsultaCnpjErro extends Error {
  motivo: MotivoFalhaCnpj;                      // declarado no corpo (o tsconfig não aceita parameter properties)

  constructor(motivo: MotivoFalhaCnpj) {
    // Mensagem antiga, de propósito: o cadastro de EMPRESA mostra só ela num
    // toast genérico e não pode mudar. Quem quer o motivo lê `motivo`.
    super('CNPJ não encontrado na Receita Federal');
    this.name = 'ConsultaCnpjErro';             // facilita reconhecer o erro no console
    this.motivo = motivo;                       // o cadastro de cliente decide o texto por aqui
  }
}

/** Tempo máximo de espera pela BrasilAPI (Spec 02, D2): sem rede o fetch pode nunca responder. */
export const TEMPO_LIMITE_CNPJ_MS = 8_000;

export async function buscarDadosCNPJ(cnpj: string): Promise<DadosCnpj> {
  const digits = cnpj.replace(/\D/g, '');                             // a API só aceita os 14 dígitos
  const controle = new AbortController();                             // permite cancelar o fetch
  const timer = setTimeout(() => controle.abort(), TEMPO_LIMITE_CNPJ_MS); // corta a espera em 8 s

  let resp: Response;
  try {
    resp = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${digits}`, { signal: controle.signal });
  } catch {
    throw new ConsultaCnpjErro('INDISPONIVEL');                       // sem rede ou tempo esgotado
  } finally {
    clearTimeout(timer);                                              // não deixa o timer vivo
  }

  if (resp.status === 404) throw new ConsultaCnpjErro('NAO_ENCONTRADO'); // a Receita não conhece
  if (!resp.ok) throw new ConsultaCnpjErro('INDISPONIVEL');             // 429 (limite), 5xx...
  return converterRespostaBrasilApi(await resp.json());                 // mapeamento de sempre
}
