/**
 * Spec 06B §11 — casos 07 e 08: a fila única de escrita (D7, D12).
 */
import { describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

import { chaveDetalhe } from '../constants/orcamento.constants';
import { ConflitoRevisao, useFilaOrcamento } from '../composables/useFilaOrcamento';
import { detalheFixture, erroApi, montarComposable } from './apoio';

function preparar() {
  const id = ref<number | null>(1);
  const { resultado: fila, queryClient } = montarComposable(() => useFilaOrcamento(id));
  queryClient.setQueryData(chaveDetalhe(1), detalheFixture());   // revisão 6 no cache
  return { fila, queryClient };
}

describe('useFilaOrcamento', () => {
  it('07 — duas escritas seguidas: a segunda sai com a revisão devolvida pela primeira', async () => {
    const { fila, queryClient } = preparar();
    const revisoesEnviadas: number[] = [];
    const escrever = async (revisao: number) => {
      revisoesEnviadas.push(revisao);
      return { ...detalheFixture(), revisao: revisao + 1 };         // o servidor sobe a revisão
    };
    // As duas entram juntas, sem esperar: a fila põe uma depois da outra.
    const primeira = fila.enfileirar(escrever);
    const segunda = fila.enfileirar(escrever);
    expect(fila.pendentes.value).toBe(2);
    await Promise.all([primeira, segunda]);
    expect(revisoesEnviadas).toEqual([6, 7]);
    expect(queryClient.getQueryData<{ revisao: number }>(chaveDetalhe(1))?.revisao).toBe(8);
    expect(fila.pendentes.value).toBe(0);
  });

  it('08 — 409 REVISAO_DESATUALIZADA: conflito, e a escrita seguinte nem é enviada', async () => {
    const { fila } = preparar();
    const segundaEscrita = vi.fn();
    const primeira = fila.enfileirar(async () => {
      throw erroApi(409, { codigo: 'REVISAO_DESATUALIZADA', mensagem: 'Outro computador salvou antes.' });
    });
    const segunda = fila.enfileirar(segundaEscrita);
    await expect(primeira).rejects.toBeTruthy();
    await expect(segunda).rejects.toBeInstanceOf(ConflitoRevisao);
    expect(fila.conflito.value).toBe(true);
    expect(segundaEscrita).not.toHaveBeenCalled();
  });

  it('um erro comum não trava as próximas escritas', async () => {
    const { fila } = preparar();
    const primeira = fila.enfileirar(async () => { throw erroApi(422, 'inválido'); });
    const segunda = fila.enfileirar(async (revisao) => ({ ...detalheFixture(), revisao: revisao + 1 }));
    await expect(primeira).rejects.toBeTruthy();
    await expect(segunda).resolves.toMatchObject({ revisao: 7 });
    expect(fila.conflito.value).toBe(false);
  });
});
