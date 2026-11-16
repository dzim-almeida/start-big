/**
 * @fileoverview Etiquetas de envio (plano, fase 5): os dados que vêm do
 * backend (`/etiquetas/envio/...`) e como viram valores de campo.
 *
 * O espelho destes tipos no backend é `app/schemas/etiqueta_envio.py`.
 */

import { formatCurrency } from '@/shared/utils/finance';
import { formatPrintDate, formatPrintDoc, formatPrintPhone } from '@/shared/utils/print.utils';
import type { ValoresEtiqueta } from './campos';

/** Só venda: o que se embala e despacha é produto (serviço não se envia). */
export type TipoOrigemEnvio = 'venda';

export interface OrigemEnvioItem {
  tipo: TipoOrigemEnvio;
  id: number;
  numero: string;
  cliente_nome: string | null;
  data: string;
  tem_nfe: boolean;
}

export interface EnderecoEnvio {
  logradouro: string;
  numero: string;
  complemento: string | null;
  bairro: string;
  cidade: string;
  uf: string;
  cep: string;
}

export interface ParteEnvio {
  nome: string;
  documento: string | null;
  inscricao_estadual: string | null;
  telefone: string | null;
  endereco: EnderecoEnvio | null;
}

export interface NfeEnvio {
  numero: number;
  serie: number;
  chave_acesso: string;
  protocolo: string | null;
  data_autorizacao: string | null;
  data_emissao: string | null;
  valor_total: number | null;
  ambiente: number | null;
  /** O destinatário como foi para a nota — o DANFE mostra este, não o cadastro de hoje. */
  destinatario_nome: string | null;
  destinatario_documento: string | null;
}

export interface DadosEnvio {
  tipo: TipoOrigemEnvio;
  id: number;
  numero: string;
  remetente: ParteEnvio;
  destinatario: ParteEnvio | null;
  nfe: NfeEnvio | null;
  /**
   * A5 (embalagens): volumes e peso tirados dos fardos/caixas da venda.
   * `peso_completo` = toda linha é embalagem com peso; só aí a tela preenche
   * sozinha. Envio avulso e backend antigo não mandam.
   */
  volumes_embalagens?: number;
  peso_embalagens_gramas?: number;
  peso_completo?: boolean;
}

/** O que o lojista informa na hora (volumes, peso) — não vem do cadastro. */
export interface DetalhesEnvio {
  volumes: number;
  /** Peso TOTAL em kg; vazio = não imprime. */
  pesoKg: number | null;
  observacao: string;
}

export function formatarCep(cep: string | null | undefined): string {
  const d = (cep ?? '').replace(/\D/g, '');
  return d.length === 8 ? `${d.slice(0, 5)}-${d.slice(5)}` : cep ?? '';
}

/** Chave de acesso em grupos de 4, como no DANFE. */
export function formatarChave(chave: string): string {
  return chave.replace(/\D/g, '').replace(/(\d{4})(?=\d)/g, '$1 ');
}

function linhaEndereco(e: EnderecoEnvio | null): string {
  if (!e) return '';
  const rua = [e.logradouro, e.numero].filter(Boolean).join(', ');
  return [rua, e.complemento].filter(Boolean).join(' — ');
}

function cidadeUf(e: EnderecoEnvio | null): string {
  if (!e) return '';
  return [e.cidade, e.uf].filter(Boolean).join(' - ');
}

function documento(parte: ParteEnvio | null): string {
  if (!parte?.documento) return '';
  const doc = formatPrintDoc(parte.documento);
  return parte.documento.replace(/\D/g, '').length > 11 ? `CNPJ ${doc}` : `CPF ${doc}`;
}

function rotuloOrigem(dados: DadosEnvio): string {
  if (!dados.numero) return '';
  return `Venda ${dados.numero}`;
}

/** Valores comuns a todos os volumes; o contador "N/M" entra por volume. */
export function valoresDoEnvio(dados: DadosEnvio, detalhes: DetalhesEnvio): ValoresEtiqueta {
  const r = dados.remetente;
  const d = dados.destinatario;
  const nfe = dados.nfe;
  const peso = detalhes.pesoKg ? `${detalhes.pesoKg.toLocaleString('pt-BR', { maximumFractionDigits: 3 })} kg` : '';

  return {
    'remetente.nome': r.nome,
    'remetente.documento': documento(r),
    'remetente.endereco': linhaEndereco(r.endereco),
    'remetente.bairro': r.endereco?.bairro ?? '',
    'remetente.cidade_uf': cidadeUf(r.endereco),
    'remetente.cep': formatarCep(r.endereco?.cep),
    'remetente.telefone': formatPrintPhone(r.telefone ?? undefined),
    'destinatario.nome': d?.nome ?? '',
    'destinatario.documento': documento(d),
    'destinatario.endereco': linhaEndereco(d?.endereco ?? null),
    'destinatario.bairro': d?.endereco?.bairro ?? '',
    'destinatario.cidade_uf': cidadeUf(d?.endereco ?? null),
    'destinatario.cep': formatarCep(d?.endereco?.cep),
    'destinatario.telefone': formatPrintPhone(d?.telefone ?? undefined),
    'envio.origem': rotuloOrigem(dados),
    'envio.codigo': dados.numero,
    'envio.peso': peso,
    'envio.observacao': detalhes.observacao,
    'nfe.numero': nfe ? `NF-e ${nfe.numero} · Série ${nfe.serie}` : '',
    'nfe.chave': nfe?.chave_acesso ?? '',
    'nfe.chave_formatada': nfe ? formatarChave(nfe.chave_acesso) : '',
    'nfe.protocolo': nfe?.protocolo ? `${nfe.protocolo}${nfe.data_autorizacao ? ` — ${formatPrintDate(nfe.data_autorizacao)}` : ''}` : '',
    'nfe.data_emissao': nfe?.data_emissao ? formatPrintDate(nfe.data_emissao) : '',
    'nfe.valor_total': nfe?.valor_total != null ? formatCurrency(nfe.valor_total) : '',
    'nfe.homologacao': nfe?.ambiente === 2 ? 'EMITIDA EM HOMOLOGAÇÃO — SEM VALOR FISCAL' : '',
    'remetente.ie': r.inscricao_estadual ? `IE ${r.inscricao_estadual}` : '',
    'remetente.uf': r.endereco?.uf ?? '',
    'destinatario.ie': d?.inscricao_estadual ? `IE ${d.inscricao_estadual}` : '',
    'destinatario.uf': d?.endereco?.uf ?? '',
    'data.impressao': new Date().toLocaleDateString('pt-BR'),
  };
}

/**
 * Valores do DANFE Simplificado: os da NOTA, não os editados na tela. O
 * destinatário sai como foi enviado à SEFAZ; endereço e UF vêm do cadastro
 * (a nota não os guarda à parte).
 */
export function valoresDoDanfe(dados: DadosEnvio): ValoresEtiqueta {
  const valores = valoresDoEnvio(dados, { volumes: 1, pesoKg: null, observacao: '' });
  const nfe = dados.nfe;
  if (nfe?.destinatario_nome) valores['destinatario.nome'] = nfe.destinatario_nome;
  if (nfe?.destinatario_documento) {
    valores['destinatario.documento'] = documento({ ...(dados.destinatario ?? {}), documento: nfe.destinatario_documento } as ParteEnvio);
  }
  return valores;
}

/** Um jogo de valores por volume: "1/3", "2/3", "3/3". */
export function etiquetasDosVolumes(base: ValoresEtiqueta, volumes: number): ValoresEtiqueta[] {
  const total = Math.max(1, Math.round(volumes));
  return Array.from({ length: total }, (_, i) => ({
    ...base,
    'volume.contador': `${i + 1}/${total}`,
    'volume.rotulo': `VOLUME ${i + 1} DE ${total}`,
  }));
}

/** Dados de exemplo para o preview e o editor sem origem escolhida. */
export const DADOS_EXEMPLO: DadosEnvio = {
  tipo: 'venda',
  id: 0,
  numero: '41',
  remetente: {
    nome: 'Minha Loja LTDA',
    documento: '11222333000181',
    inscricao_estadual: '123456789',
    telefone: '8835810000',
    endereco: { logradouro: 'Rua da Loja', numero: '10', complemento: null, bairro: 'Centro', cidade: 'Cidade', uf: 'CE', cep: '63500000' },
  },
  destinatario: {
    nome: 'Cliente de Exemplo',
    documento: '52998224725',
    inscricao_estadual: null,
    telefone: '88999990000',
    endereco: { logradouro: 'Rua do Cliente', numero: '250', complemento: 'Casa B', bairro: 'Bairro Novo', cidade: 'Cidade', uf: 'CE', cep: '63500123' },
  },
  nfe: {
    numero: 11,
    serie: 1,
    chave_acesso: '23260911222333000181550010000000111000000110',
    protocolo: '123260000000001',
    data_autorizacao: '2026-09-20T13:30:00',
    data_emissao: '2026-09-20T13:29:00',
    valor_total: 128000,
    ambiente: 2,
    destinatario_nome: 'CLIENTE DE EXEMPLO',
    destinatario_documento: '52998224725',
  },
};
