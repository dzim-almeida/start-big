/**
 * @fileoverview O cabeçalho editável do orçamento e "o que mudou desde o último
 * salvamento" (Spec 06B D8): o PATCH leva SÓ os campos que mudaram, para nunca
 * sobrescrever um campo que o usuário nem tocou.
 */
import type { AjusteOrcamento, OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';

/** Os campos do cabeçalho que salvam sozinhos (06B §7.5). Ambientes e móveis ficam de fora. */
export interface CabecalhoForm {
  cliente_id: number | null;
  funcionario_id: number | null;
  objeto_id: number | null;
  projeto_nome: string | null;
  endereco_obra: string | null;
  medicao_observacoes: string | null;
  observacoes_proposta: string | null;
  validade_dias: number;
  prazo_entrega_dias: number;
  desconto: AjusteOrcamento;
  sinal: AjusteOrcamento;
  // Só existem para quem vê custos (06A D23): ausentes no formulário do vendedor.
  markup_bp?: number;
  perda_bp?: number;
  custo_hora_centavos?: number;
  rt_padrao_bp?: number;
  instalacao_custo_centavos?: number | null;
  /**
   * RT do arquiteto escolhido, em bp (Spec 09B §6.2). Só existe com custos E
   * com arquiteto. Não vai no PATCH: o salvamento manda esta chave no PUT /rt.
   */
  rt_arquiteto_bp?: number;
}

/** Copia do detalhe os campos editáveis do cabeçalho (cópia nova, nada compartilhado). */
export function cabecalhoDoDetalhe(detalhe: OrcamentoDetalhe): CabecalhoForm {
  const form: CabecalhoForm = {
    cliente_id: detalhe.cliente?.id ?? null,
    funcionario_id: detalhe.vendedor?.id ?? null,
    objeto_id: detalhe.projeto.objeto_id,
    projeto_nome: detalhe.projeto.nome,
    endereco_obra: detalhe.projeto.endereco_obra,
    medicao_observacoes: detalhe.medicao_observacoes,
    observacoes_proposta: detalhe.observacoes_proposta,
    validade_dias: detalhe.parametros.validade_dias,
    prazo_entrega_dias: detalhe.parametros.prazo_entrega_dias,
    desconto: { ...detalhe.desconto },
    sinal: { ...detalhe.sinal },
  };
  if (detalhe.inclui_custos) {                    // o TypeScript sabe: aqui os campos de custo existem
    form.markup_bp = detalhe.parametros.markup_bp;
    form.perda_bp = detalhe.parametros.perda_bp;
    form.custo_hora_centavos = detalhe.parametros.custo_hora_centavos;
    form.rt_padrao_bp = detalhe.parametros.rt_padrao_bp;
    form.instalacao_custo_centavos = detalhe.instalacao_custo_centavos;
    // Um arquiteto por orçamento na tela (C5a): o primeiro da lista.
    if (detalhe.arquitetos[0]) form.rt_arquiteto_bp = detalhe.arquitetos[0].rt_bp;
  }
  return form;
}

/** Igualdade de valor simples (números, textos, null e o objeto de desconto/sinal). */
function iguais(a: unknown, b: unknown): boolean {
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    return JSON.stringify(a) === JSON.stringify(b);
  }
  return a === b;
}

/**
 * Os campos de `atual` diferentes de `salvo`: é o corpo do PATCH.
 *
 * Objetos (desconto, sinal) saem COPIADOS: se a resposta guardasse o mesmo
 * objeto que a tela edita, uma mudança feita depois apareceria também no
 * "último salvo" e nunca seria percebida como mudança (não salvaria).
 */
export function diferencaCabecalho(salvo: CabecalhoForm, atual: CabecalhoForm): Partial<CabecalhoForm> {
  const mudancas: Record<string, unknown> = {};
  for (const chave of Object.keys(atual) as (keyof CabecalhoForm)[]) {
    if (!iguais(salvo[chave], atual[chave])) {
      const valor = atual[chave];
      mudancas[chave] = valor && typeof valor === 'object' ? { ...valor } : valor;
    }
  }
  return mudancas as Partial<CabecalhoForm>;
}
