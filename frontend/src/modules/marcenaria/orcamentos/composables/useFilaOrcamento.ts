/**
 * @fileoverview Fila única de escrita de UM orçamento (Spec 06B D7, D12, §7.4).
 *
 * Por que uma fila: a trava otimista do backend (06A D20) exige a revisão
 * certa em toda escrita. Duas escritas em paralelo do MESMO computador
 * mandariam a mesma revisão, e a segunda levaria 409 sem motivo. Na fila, uma
 * sai depois da outra, sempre com a revisão que o cache tem NAQUELE momento.
 */
import { ref, type Ref } from 'vue';
import { useQueryClient } from '@tanstack/vue-query';

import { CHAVE_RAIZ, chaveDetalhe } from '../constants/orcamento.constants';
import type { OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import { codigoDoErro } from '../utils/erros';

/** Erro de quem tenta escrever depois de um conflito: nada mais sai até recarregar. */
export class ConflitoRevisao extends Error {
  constructor() {
    super('Este orçamento foi alterado em outro computador. Recarregue para ver a versão atual.');
    this.name = 'ConflitoRevisao';
  }
}

export type FilaOrcamento = ReturnType<typeof useFilaOrcamento>;

export function useFilaOrcamento(id: Ref<number | null>) {
  const queryClient = useQueryClient();          // cache do TanStack Query
  let fila: Promise<unknown> = Promise.resolve(); // a "corrente" de escritas, uma após a outra
  const pendentes = ref(0);                       // quantas escritas ainda não terminaram
  const conflito = ref(false);                    // true depois de um 409 de revisão (abre o ConflitoModal)

  /** Depois de gravar, a lista e as contagens ficam velhas: recarregam quando forem vistas. */
  function invalidarLista() {
    queryClient.invalidateQueries({ queryKey: [CHAVE_RAIZ, 'lista'] });
    queryClient.invalidateQueries({ queryKey: [CHAVE_RAIZ, 'contagens'] });
  }

  /**
   * Enfileira uma escrita. `executar` recebe a revisão atual e devolve o detalhe novo,
   * que substitui o do cache (a resposta já traz o cálculo novo, 06A D21).
   */
  function enfileirar(executar: (revisao: number) => Promise<OrcamentoDetalhe>): Promise<OrcamentoDetalhe> {
    pendentes.value++;                                       // a tela mostra "Salvando…"
    const tarefa = fila.then(async () => {
      if (conflito.value) throw new ConflitoRevisao();       // depois de um conflito, nada mais sai
      const atual = id.value != null
        ? queryClient.getQueryData<OrcamentoDetalhe>(chaveDetalhe(id.value))
        : undefined;
      if (!atual) throw new Error('Orçamento ainda não carregado.');
      try {
        const novo = await executar(atual.revisao);          // manda a revisão que o cache tem AGORA
        queryClient.setQueryData(chaveDetalhe(novo.id), novo);
        invalidarLista();
        return novo;
      } catch (erro) {
        if (codigoDoErro(erro) === 'REVISAO_DESATUALIZADA') conflito.value = true;
        throw erro;                                          // quem chamou decide a mensagem
      } finally {
        pendentes.value--;
      }
    });
    fila = tarefa.catch(() => undefined);                    // um erro não trava as próximas da fila
    return tarefa;
  }

  /** Espera tudo o que está na fila (ao sair da tela, D10, e antes de imprimir, Spec 07 D4). */
  const esvaziar = () => fila;

  /** Depois de "Recarregar orçamento" no ConflitoModal: busca o atual e libera a fila. */
  async function recarregar() {
    conflito.value = false;
    if (id.value != null) await queryClient.invalidateQueries({ queryKey: chaveDetalhe(id.value) });
  }

  return { enfileirar, esvaziar, recarregar, invalidarLista, pendentes, conflito };
}
