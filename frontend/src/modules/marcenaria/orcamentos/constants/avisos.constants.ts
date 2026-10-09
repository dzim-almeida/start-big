/**
 * @fileoverview Texto de cada aviso do motor de cálculo (Spec 06B §6.6, D17).
 *
 * O backend devolve só o CÓDIGO do aviso; a frase depende de quem está vendo:
 * quem não vê custos não pode receber números de margem.
 */
import type { OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';

/** Uma linha de aviso pronta para a tela. */
export interface AvisoTexto {
  codigo: string;
  texto: string;
  /** 'neutro' = informação (ex.: orçamento vazio); 'atencao' = âmbar. */
  tom: 'neutro' | 'atencao';
}

/**
 * Frase do aviso conforme a permissão de custos.
 * Código desconhecido (de uma spec futura) devolve null e simplesmente não aparece.
 */
export function textoDoAviso(codigo: string, incluiCustos: boolean): AvisoTexto | null {
  switch (codigo) {
    case 'INSUMO_SEM_CUSTO':
      return {
        codigo,
        tom: 'atencao',
        texto: 'Há insumos sem custo cadastrado (R$ 0,00). Confira os itens marcados com "sem custo".',
      };
    case 'HORAS_SEM_CUSTO_HORA':
      // O vendedor sem custos não vê nem edita a mão de obra: o aviso não é para ele.
      if (!incluiCustos) return null;
      return {
        codigo,
        tom: 'atencao',
        texto: 'Há móveis com mão de obra por horas, mas o custo/hora deste orçamento é R$ 0,00.',
      };
    case 'MARGEM_NEGATIVA':
      // Aparece para todos (vender no prejuízo sem saber é pior), mas sem números.
      return {
        codigo,
        tom: 'atencao',
        texto: incluiCustos
          ? 'A margem líquida está negativa: o orçamento sai abaixo do custo.'
          : 'O desconto deixou o orçamento abaixo do custo. Fale com o responsável antes de enviar.',
      };
    case 'ORCAMENTO_VAZIO':
      return { codigo, tom: 'neutro', texto: 'Adicione um ambiente e um móvel para começar.' };
    default:
      return null;
  }
}

/** Todos os avisos de uma lista de códigos, já sem os desconhecidos. */
export function textosDosAvisos(codigos: string[], incluiCustos: boolean): AvisoTexto[] {
  return codigos
    .map((codigo) => textoDoAviso(codigo, incluiCustos))
    .filter((aviso): aviso is AvisoTexto => aviso !== null);
}

/**
 * Spec 09B D12: arquiteto escolhido com 0% de RT (o padrão da configuração
 * nasce em 0%). Sem o aviso, o RT é esquecido até o arquiteto cobrar.
 * Só para quem vê custos (o % é custo); null quando não há o que avisar.
 * Usado no bloco Arquiteto e no modal de envio (a mesma frase nos dois).
 */
export function avisoRtZero(detalhe: OrcamentoDetalhe | undefined): AvisoTexto | null {
  if (!detalhe?.inclui_custos) return null;
  const arquiteto = detalhe.arquitetos[0];                 // um arquiteto por orçamento na tela (C5a)
  if (!arquiteto || arquiteto.rt_bp !== 0) return null;
  return {
    codigo: 'RT_ZERO',
    tom: 'atencao',
    texto: `${arquiteto.nome} está sem percentual de RT. Informe o % ou defina um padrão em Configurações › Marcenaria.`,
  };
}
