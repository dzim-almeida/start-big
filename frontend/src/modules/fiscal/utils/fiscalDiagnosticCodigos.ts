/**
 * Diagnóstico pelo CÓDIGO da SEFAZ (cStat), antes de qualquer palavra-chave.
 *
 * O diagnóstico procurava palavras soltas na mensagem, e a primeira NF-e real
 * em produção (06/10/2026) mostrou o custo: a 481 ("Código Regime Tributário do
 * EMITENTE diverge...") caiu em "cadastre o certificado e as séries" por causa
 * da palavra "emitente"; a 539 (número já usado por outro sistema) caiu em
 * "ajuste o CSOSN"; a 305 caiu no genérico. Três rejeições, três conselhos
 * errados, cinco números gastos.
 *
 * O cStat identifica a regra sem ambiguidade; a mensagem só descreve. Por isso
 * esta tabela é consultada PRIMEIRO, e as palavras-chave de `fiscalDiagnostic.ts`
 * ficam para código que não está aqui.
 *
 * Só entra código conferido no Manual de Orientação do Contribuinte (MOC) da
 * NF-e. Na dúvida, fica de fora — o genérico mostra a mensagem da SEFAZ, que é
 * melhor do que um conselho errado.
 */
import type { DocumentoFiscalRead } from '../types/fiscal.types';
import type { FiscalDiagnostic } from './fiscalDiagnostic';

const BADGE = {
  emitente:  { bg: 'bg-rose-50',   text: 'text-rose-700',   border: 'border-rose-200' },
  cliente:   { bg: 'bg-amber-50',  text: 'text-amber-700',  border: 'border-amber-200' },
  numeracao: { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200' },
};

/**
 * Lê a chave de acesso que a SEFAZ devolve na 539 ("[chNFe:3526...]").
 *
 * Posições da chave (44 dígitos): UF(2) AAMM(4) CNPJ(14) modelo(2) série(3)
 * número(9) tpEmis(1) código(8) DV(1).
 */
export function lerChaveDaMensagem(mensagem: string | null | undefined) {
  const chave = /chNFe:\s*(\d{44})/.exec(mensagem || '')?.[1];
  if (!chave) return null;
  return {
    chave,
    mes: chave.slice(4, 6),
    ano: `20${chave.slice(2, 4)}`,
    serie: Number(chave.slice(22, 25)),
    numero: Number(chave.slice(25, 34)),
  };
}

type Montador = (documento: DocumentoFiscalRead) => Omit<FiscalDiagnostic, 'cStat'>;

const certificado: Montador = () => ({
  categoria: 'CONFIGURACAO',
  badge: { label: 'Certificado digital', ...BADGE.emitente },
  titulo: 'Problema no Certificado Digital',
  explicacao: 'A SEFAZ recusou o certificado digital usado para assinar a nota (vencido, revogado ou de outra empresa).',
  comoResolver: 'Confira a validade e o CNPJ do certificado em Centro Fiscal › Configurações e envie o certificado atual.',
  acaoPrincipal: { tipo: 'CENTRO_FISCAL', label: 'Abrir Centro Fiscal' },
});

const TABELA: Record<number, Montador> = {
  204: () => ({
    categoria: 'DUPLICIDADE',
    badge: { label: 'cStat 204 · Duplicidade', ...BADGE.numeracao },
    titulo: 'Esta Nota Já Foi Autorizada',
    explicacao: 'A SEFAZ já tem esta mesma nota (mesma chave) autorizada. Ela provavelmente saiu numa tentativa anterior cuja resposta se perdeu.',
    comoResolver: 'Consulte o status: o sistema busca a autorização que já existe. Não reemita — isso gastaria outro número.',
    acaoPrincipal: { tipo: 'RECONSULTAR', label: 'Consultar Status na SEFAZ' },
  }),

  207: () => ({
    categoria: 'CONFIGURACAO',
    badge: { label: 'cStat 207 · CNPJ do emitente', ...BADGE.emitente },
    titulo: 'CNPJ da Sua Empresa Inválido',
    explicacao: 'O CNPJ do emitente (a sua empresa) foi recusado pela SEFAZ.',
    comoResolver: 'Confira o CNPJ em Dados da Empresa — só os 14 dígitos, sem erro de digitação.',
    acaoPrincipal: { tipo: 'CONFIG_FISCAL', label: 'Abrir Dados da Empresa' },
  }),

  208: () => ({
    categoria: 'CLIENTE',
    badge: { label: 'cStat 208 · CNPJ do cliente', ...BADGE.cliente },
    titulo: 'CNPJ do Cliente Inválido',
    explicacao: 'O CNPJ do destinatário (quem comprou) foi recusado pela SEFAZ.',
    comoResolver: 'Corrija o CNPJ no cadastro do cliente e emita de novo.',
    acaoPrincipal: { tipo: 'EDITAR_VENDA', label: 'Corrigir Cliente da Venda' },
  }),

  209: () => ({
    categoria: 'CONFIGURACAO',
    badge: { label: 'cStat 209 · IE do emitente', ...BADGE.emitente },
    titulo: 'Inscrição Estadual da Sua Empresa Inválida',
    explicacao: 'A Inscrição Estadual do emitente (a sua empresa) não confere com o cadastro da SEFAZ.',
    comoResolver: 'Confira a Inscrição Estadual em Dados da Empresa com o cartão do Cadesp/SINTEGRA ou com o contador.',
    acaoPrincipal: { tipo: 'CONFIG_FISCAL', label: 'Abrir Dados da Empresa' },
  }),

  213: () => ({
    categoria: 'CONFIGURACAO',
    badge: { label: 'cStat 213 · Certificado de outro CNPJ', ...BADGE.emitente },
    titulo: 'Certificado Digital de Outra Empresa',
    explicacao: 'O certificado usado para assinar é de um CNPJ diferente do emitente da nota.',
    comoResolver: 'Envie o certificado A1 da própria empresa em Centro Fiscal › Configurações.',
    acaoPrincipal: { tipo: 'CENTRO_FISCAL', label: 'Abrir Centro Fiscal' },
  }),

  237: () => ({
    categoria: 'CLIENTE',
    badge: { label: 'cStat 237 · CPF do cliente', ...BADGE.cliente },
    titulo: 'CPF do Cliente Inválido',
    explicacao: 'O CPF do destinatário (quem comprou) foi recusado pela SEFAZ.',
    comoResolver: 'Corrija o CPF no cadastro do cliente e emita de novo.',
    acaoPrincipal: { tipo: 'EDITAR_VENDA', label: 'Corrigir Cliente da Venda' },
  }),

  280: certificado, 281: certificado, 282: certificado, 283: certificado,
  284: certificado, 285: certificado, 286: certificado,

  301: () => ({
    categoria: 'CONFIGURACAO',
    badge: { label: 'cStat 301 · Uso denegado', ...BADGE.emitente },
    titulo: 'Nota Denegada: Irregularidade da Sua Empresa',
    explicacao: 'A SEFAZ registrou a nota e negou o uso por irregularidade fiscal do EMITENTE (a sua empresa). O número foi consumido.',
    comoResolver: 'Fale com o contador para regularizar a empresa na SEFAZ. Reemitir não adianta enquanto a irregularidade existir.',
  }),

  302: () => ({
    categoria: 'CLIENTE',
    badge: { label: 'cStat 302 · Uso denegado', ...BADGE.cliente },
    titulo: 'Nota Denegada: Irregularidade do Cliente',
    explicacao: 'A SEFAZ registrou a nota e negou o uso por irregularidade fiscal do DESTINATÁRIO. O número foi consumido.',
    comoResolver: 'O cliente precisa regularizar a situação dele na SEFAZ. Se for compra para uso próprio, a nota pode sair no CPF da pessoa — confirme com o contador.',
  }),

  305: () => ({
    categoria: 'CLIENTE',
    badge: { label: 'cStat 305 · Cliente bloqueado', ...BADGE.cliente },
    titulo: 'Cliente Bloqueado na SEFAZ do Estado Dele',
    explicacao: 'O cadastro do destinatário está bloqueado (IE suspensa, inapta ou baixada) no estado dele. Nenhum sistema consegue emitir para ele como está — não é erro do seu cadastro.',
    comoResolver: 'Consulte o CNPJ do cliente no CCC (dfe-portal.svrs.rs.gov.br/NFE/CCC) ou no SINTEGRA. Ele precisa regularizar com o contador dele. Se a compra é para uso próprio da pessoa, a nota pode sair no CPF dela.',
    acaoPrincipal: { tipo: 'EDITAR_VENDA', label: 'Trocar Cliente da Venda' },
  }),

  481: () => ({
    categoria: 'CONFIGURACAO',
    badge: { label: 'cStat 481 · Regime tributário', ...BADGE.emitente },
    titulo: 'Regime Tributário da Sua Empresa Diverge da SEFAZ',
    explicacao: 'O Regime Tributário em Dados da Empresa é diferente do que a SEFAZ tem para o seu CNPJ. O caso mais comum: a empresa é MEI e está cadastrada como "1 - Simples Nacional".',
    comoResolver: 'Confira na Consulta Optantes do Simples Nacional se o CNPJ é optante pelo SIMEI. Se for, troque o Regime Tributário para "4 - MEI" em Dados da Empresa e emita de novo.',
    acaoPrincipal: { tipo: 'CONFIG_FISCAL', label: 'Abrir Dados da Empresa' },
  }),

  539: (documento) => {
    const usada = lerChaveDaMensagem(documento.mensagem_sefaz);
    const quando = usada ? ` em ${usada.mes}/${usada.ano}` : '';
    const qual = usada ? `O nº ${usada.numero} da série ${usada.serie}` : 'Este número';
    return {
      categoria: 'DUPLICIDADE',
      badge: { label: 'cStat 539 · Número já usado', ...BADGE.numeracao },
      titulo: 'Número Já Usado por Outra Nota',
      explicacao: `${qual} já foi emitido${quando} com outra chave — quase sempre por outro sistema que a empresa usava antes do StartBig.`,
      comoResolver: 'Pergunte ao contador qual foi a última nota emitida em cada série no sistema antigo e ajuste a numeração em Centro Fiscal › Configurações. Não inutilize os números para trás: eles podem ter sido usados de verdade.',
      acaoPrincipal: { tipo: 'CENTRO_FISCAL', label: 'Abrir Centro Fiscal' },
    };
  },
};

/** Diagnóstico pelo cStat, ou `null` se o código não está na tabela. */
export function diagnosticoPorCodigo(documento: DocumentoFiscalRead): FiscalDiagnostic | null {
  const cStat = documento.codigo_status_sefaz;
  if (!cStat) return null;
  const montar = TABELA[cStat];
  return montar ? { ...montar(documento), cStat } : null;
}
