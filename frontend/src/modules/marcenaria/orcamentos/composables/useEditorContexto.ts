/**
 * @fileoverview O que o editor reparte com os blocos (Spec 06B §6.2).
 *
 * Em vez de passar o formulário e as ações de bloco em bloco por props
 * ("prop drilling"), o editor PROVÊ um contexto e cada bloco o INJETA. Assim
 * nenhum bloco altera props do pai (o Vue proíbe) e todos falam com a mesma
 * fila de escrita (D7).
 */
import { inject, provide, type ComputedRef, type InjectionKey, type Ref } from 'vue';

import type { OpcoesConfirmacao } from '@/shared/composables/useConfirmacao';

import type { AcoesOrcamento, MovelDetalhe, OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import type { CabecalhoForm } from '../utils/diferencaCabecalho';
import type { useAcoesOrcamento } from './useAcoesOrcamento';

export interface EditorContexto {
  /** id do orçamento (null na tela "novo" antes do primeiro salvamento, D5). */
  id: Ref<number | null>;
  /** Detalhe da API (undefined enquanto carrega ou na tela "novo"). */
  detalhe: Ref<OrcamentoDetalhe | undefined>;
  /** Cabeçalho editável (salvamento automático, D8). */
  form: CabecalhoForm;
  /** Erro do backend embaixo do campo certo (422 com `campo`). */
  errosPorCampo: Ref<Record<string, string>>;
  /** Pode editar? Vem de `acoes.editar` (D13); a tela "novo" sempre pode. */
  editavel: ComputedRef<boolean>;
  /** Vê custos? Vem de `inclui_custos` da resposta (06A D23). */
  incluiCustos: ComputedRef<boolean>;
  /** O que pode ser feito agora (D13). Na tela "novo", tudo falso menos editar. */
  acoes: ComputedRef<AcoesOrcamento>;
  /** Ações que gravam na hora (ambientes, móveis, transições). */
  acoesOrcamento: ReturnType<typeof useAcoesOrcamento>;
  /**
   * Tela "novo": cria o orçamento agora (ex.: ao adicionar o primeiro
   * ambiente, D5) e devolve o id. Com orçamento já criado, só devolve o id.
   */
  garantirOrcamento: () => Promise<number | null>;
  /**
   * Pergunta de confirmação (um modal só, desenhado pelo editor). A descrição
   * aceita HTML: texto digitado pelo usuário passa antes por `escaparHtml`.
   */
  confirmar: (opcoes: OpcoesConfirmacao) => Promise<boolean>;
  /** Abre o modal do móvel: novo (só o ambiente) ou editando um gravado. */
  abrirMovel: (ambienteId: number, movel?: MovelDetalhe) => void;
}

const CHAVE: InjectionKey<EditorContexto> = Symbol('editor-orcamento');

/** Chamado UMA vez, pelo editor. */
export function proverEditor(contexto: EditorContexto): void {
  provide(CHAVE, contexto);
}

/** Chamado pelos blocos. Falha alto se usado fora do editor (erro de programação). */
export function useEditor(): EditorContexto {
  const contexto = inject(CHAVE, null);
  if (!contexto) throw new Error('useEditor() só funciona dentro do editor de orçamento.');
  return contexto;
}
