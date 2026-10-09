/**
 * @fileoverview O que o CLIENTE pode ver do orçamento (Spec 06B §7.13 e D14;
 * Spec 07 §6.1).
 *
 * Função pura usada pela visão do cliente (06B) e pela proposta impressa
 * (Spec 07): as duas mostram exatamente a mesma coisa, porque vêm daqui.
 *
 * O tipo de saída NÃO tem campo de custo, margem, insumo, parâmetro nem preço
 * por móvel (T5, P4). Por isso cada campo é copiado PELO NOME: nunca
 * `...detalhe` nem `...movel`, que levariam junto o que o cliente não pode ver.
 * Um teste varre as chaves da saída para garantir isso.
 */
import { formatDataPura } from '@/shared/utils/date.utils';
import { formatPrintDoc, formatPrintPhone } from '@/shared/utils/print.utils';

import type { StatusOrcamento } from '../constants/orcamento.constants';
import type { AjusteOrcamento, OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';

/** Um móvel como o cliente vê: sem preço, sem insumos. */
export interface MovelProposta {
  nome: string;
  descricao: string;
  /** "L 700 × A 2200 × P 600 mm" (Spec 07 D14). */
  medidas: string;
  quantidade: number;
}

/** Um ambiente com o total dele (subtotal bruto, como a 06A devolve). */
export interface AmbienteProposta {
  nome: string;
  totalCentavos: number;
  moveis: MovelProposta[];
}

/** Desconto ou sinal: o valor em R$ e, no modo percentual, o "5%". */
export interface AjusteProposta {
  centavos: number;
  percentualTexto: string | null;
}

/** Tudo o que a proposta e a visão do cliente mostram. Nada de custo. */
export interface DadosProposta {
  codigo: string;
  versao: number;
  status: StatusOrcamento;
  /** Data de hoje: "09/10/2026". */
  emitidaEm: string;
  /** "até 21/10/2026" (já enviado) ou "15 dias a partir do envio" (prévia). */
  validadeTexto: string;
  /** "PRÉVIA — proposta ainda não enviada" e afins (Spec 07 D6), ou null. */
  faixa: string | null;
  cliente: { nome: string; documento: string; telefone: string; email: string; endereco: string };
  projeto: { nome: string; enderecoObra: string };
  vendedor: { nome: string; telefone: string } | null;
  ambientes: AmbienteProposta[];
  /** Preço da instalação (C3), ou null sem instalação. */
  instalacaoCentavos: number | null;
  /** Bruto (soma dos ambientes + instalação). */
  subtotalCentavos: number;
  /** null quando não há desconto. */
  desconto: AjusteProposta | null;
  totalCentavos: number;
  /** null quando o sinal é zero (Spec 07 D11: só "Total a pagar"). */
  sinal: AjusteProposta | null;
  saldoCentavos: number;
  prazoEntregaDias: number;
  /** Observações da proposta, com as quebras de linha digitadas. */
  observacoes: string;
}

/** Opções que não vêm do detalhe. */
export interface OpcoesProposta {
  /** Número da versão que substituiu esta (faixa "VERSÃO SUBSTITUÍDA pela v3"). */
  versaoSubstituta?: number | null;
}

/** "L 700 × A 2200 × P 600 mm"; medida vazia fica de fora; nenhuma medida = "". */
export function formatarMedidasProposta(l: number | null, a: number | null, p: number | null): string {
  const partes = [
    l != null ? `L ${l}` : null,
    a != null ? `A ${a}` : null,
    p != null ? `P ${p}` : null,
  ].filter((parte): parte is string => parte !== null);
  return partes.length ? `${partes.join(' × ')} mm` : '';
}

/** Percentual em bp → "5%" / "12,5%" / "12,35%" (até 2 casas, sem zeros sobrando). */
function textoPercentual(bp: number): string {
  return `${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`;
}

/** Desconto/sinal da tela da proposta: null quando é zero. */
function ajuste(ajusteInformado: AjusteOrcamento, centavos: number): AjusteProposta | null {
  if (centavos <= 0) return null;
  return {
    centavos,
    // Só o modo percentual mostra o "%": no modo VALOR, o número é o que foi combinado em R$.
    percentualTexto: ajusteInformado.modo === 'PERCENTUAL' ? textoPercentual(ajusteInformado.valor) : null,
  };
}

/** A faixa do topo conforme o status (Spec 07 D6). Enviado e aprovado saem sem faixa. */
function faixaDoStatus(detalhe: OrcamentoDetalhe, opcoes: OpcoesProposta): string | null {
  switch (detalhe.status) {
    case 'RASCUNHO':
      return 'PRÉVIA — proposta ainda não enviada';
    case 'VENCIDO':
      return `PROPOSTA VENCIDA em ${formatDataPura(detalhe.datas.validade, '')}`.trim();
    case 'RECUSADO':
      return 'PROPOSTA RECUSADA';
    case 'SUBSTITUIDO':
      return opcoes.versaoSubstituta ? `VERSÃO SUBSTITUÍDA pela v${opcoes.versaoSubstituta}` : 'VERSÃO SUBSTITUÍDA';
    default:
      return null;
  }
}

/**
 * Copia do detalhe só o que pode chegar ao cliente. Sem rede, sem store:
 * o mesmo detalhe e a mesma data dão sempre o mesmo resultado.
 */
export function montarDadosProposta(detalhe: OrcamentoDetalhe, hoje: Date, opcoes: OpcoesProposta = {}): DadosProposta {
  const { calculo } = detalhe;
  return {
    codigo: detalhe.codigo,
    versao: detalhe.versao,
    status: detalhe.status,
    emitidaEm: hoje.toLocaleDateString('pt-BR'),
    validadeTexto: detalhe.datas.validade
      ? `até ${formatDataPura(detalhe.datas.validade)}`                     // já enviado: a data gravada
      : `${detalhe.parametros.validade_dias} dias a partir do envio`,        // prévia: ainda não conta
    faixa: faixaDoStatus(detalhe, opcoes),
    // Cliente, projeto e vendedor campo a campo (nunca com spread).
    cliente: {
      nome: detalhe.cliente?.nome ?? '',
      documento: formatPrintDoc(detalhe.cliente?.documento ?? undefined),
      telefone: formatPrintPhone(detalhe.cliente?.telefone ?? undefined),
      email: detalhe.cliente?.email ?? '',
      endereco: detalhe.cliente?.endereco ?? '',
    },
    projeto: {
      nome: detalhe.projeto.nome ?? '',
      enderecoObra: detalhe.projeto.endereco_obra ?? '',
    },
    vendedor: detalhe.vendedor
      ? { nome: detalhe.vendedor.nome, telefone: formatPrintPhone(detalhe.vendedor.telefone ?? undefined) }
      : null,
    ambientes: detalhe.ambientes
      .filter((ambiente) => ambiente.moveis.length > 0)                     // ambiente vazio não sai (Spec 07 D9)
      .map((ambiente) => ({
        nome: ambiente.nome,
        totalCentavos: ambiente.subtotal_centavos,                           // bruto, como a 06A devolve
        moveis: ambiente.moveis.map((movel) => ({
          nome: movel.nome,
          descricao: movel.descricao ?? '',
          medidas: formatarMedidasProposta(movel.largura_mm, movel.altura_mm, movel.profundidade_mm),
          quantidade: movel.quantidade,                                      // o preço do móvel NÃO entra (T5)
        })),
      })),
    instalacaoCentavos: calculo.instalacao?.preco_centavos ?? null,
    subtotalCentavos: calculo.bruto_centavos,
    desconto: ajuste(detalhe.desconto, calculo.desconto_centavos),
    totalCentavos: calculo.total_centavos,
    sinal: ajuste(detalhe.sinal, calculo.sinal_centavos),
    saldoCentavos: calculo.saldo_centavos,
    prazoEntregaDias: detalhe.parametros.prazo_entrega_dias,
    observacoes: detalhe.observacoes_proposta ?? '',
  };
}
