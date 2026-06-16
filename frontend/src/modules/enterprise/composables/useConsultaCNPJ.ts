export interface CNPJApiData {
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
}

function formatCNAECode(codigo: number): string {
  const str = String(codigo).padStart(7, '0');
  return `${str.slice(0, 4)}-${str.slice(4, 5)}/${str.slice(5)}`;
}

function mapNaturezaJuridica(texto: string, porte: string): string {
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

export async function buscarDadosCNPJ(cnpj: string): Promise<CNPJApiData> {
  const digits = cnpj.replace(/\D/g, '');
  const resp = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${digits}`);

  if (!resp.ok) {
    throw new Error('CNPJ não encontrado na Receita Federal');
  }

  const d = await resp.json();

  const logradouro = [d.descricao_tipo_logradouro, d.logradouro]
    .filter(Boolean)
    .join(' ')
    .trim();

  const cnaesSecundarios = (d.cnaes_secundarios || [])
    .map((c: { codigo: number }) => formatCNAECode(c.codigo))
    .join(', ');

  const cnaePrincipal = d.cnae_fiscal ? formatCNAECode(d.cnae_fiscal) : '';

  const naturezaJuridica = mapNaturezaJuridica(d.natureza_juridica || '', d.porte || '');

  return {
    razao_social: d.razao_social || '',
    nome_fantasia: d.nome_fantasia || '',
    cnae_principal: cnaePrincipal,
    cnaes_secundarios: cnaesSecundarios,
    natureza_juridica: naturezaJuridica,
    data_abertura: d.data_inicio_atividade || '',
    email: d.email || '',
    telefone: d.ddd_telefone_1 || '',
    logradouro,
    numero: d.numero || '',
    complemento: d.complemento || '',
    bairro: d.bairro || '',
    cidade: d.municipio || '',
    estado: d.uf || '',
    cep: d.cep || '',
    codigo_ibge: d.codigo_ibge || '',
  };
}
