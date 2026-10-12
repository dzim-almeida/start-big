/**
 * Spec 06B §11 — casos 09 a 13: o salvamento automático do cabeçalho
 * (D5, D8-D12). O relógio é falso: o teste anda os 800 ms na mão.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { nextTick, ref } from 'vue';
import { flushPromises } from '@vue/test-utils';

const patch = vi.fn();                                     // o PATCH /orcamentos/{id}
vi.mock('../services/orcamento.service', () => ({
  patchOrcamento: (...args: unknown[]) => patch(...args),
}));

const { chaveDetalhe } = await import('../constants/orcamento.constants');
const { useFilaOrcamento } = await import('../composables/useFilaOrcamento');
const { useSalvamentoAutomatico, ESPERAS_NOVA_TENTATIVA_MS } = await import('../composables/useSalvamentoAutomatico');
const { detalheFixture, erroApi, erroRede, montarComposable } = await import('./apoio');
type Detalhe = ReturnType<typeof detalheFixture>;

/** Monta fila + salvamento com o detalhe real no cache (revisão 6). */
function preparar(opcoes: { criar?: (corpo: unknown) => Promise<Detalhe>; semDetalhe?: boolean } = {}) {
  const inicial = opcoes.semDetalhe ? undefined : detalheFixture();
  const detalhe = ref<Detalhe | undefined>(inicial);
  const id = ref<number | null>(inicial?.id ?? null);
  const { resultado, queryClient } = montarComposable(() => {
    const fila = useFilaOrcamento(id);
    return { fila, salvamento: useSalvamentoAutomatico(detalhe, fila, { criar: opcoes.criar as never }) };
  });
  if (inicial) queryClient.setQueryData(chaveDetalhe(inicial.id), inicial);
  return { ...resultado, detalhe, queryClient };
}

/** Anda o relógio e deixa as promessas e os watchers terminarem. */
async function andar(ms: number) {
  await vi.advanceTimersByTimeAsync(ms);
  await flushPromises();
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'Date'] });
  patch.mockReset();
  patch.mockImplementation(async (_id: number, revisao: number, mudancas: Record<string, unknown>) => ({
    ...detalheFixture(),
    ...mudancas,
    revisao: revisao + 1,
  }));
});
afterEach(() => { vi.useRealTimers(); });

describe('useSalvamentoAutomatico', () => {
  it('09 — 3 mudanças em 500 ms viram UM PATCH com as 3', async () => {
    const { salvamento } = preparar();
    salvamento.form.desconto = { modo: 'VALOR', valor: 10000 };
    await andar(200);
    salvamento.form.validade_dias = 20;
    await andar(200);
    salvamento.form.observacoes_proposta = 'Saldo em 3x';
    await nextTick();
    expect(salvamento.estado.value).toBe('esperando');           // "Alterações não salvas"
    await andar(799);
    expect(patch).not.toHaveBeenCalled();                        // ainda dentro dos 800 ms
    await andar(10);
    expect(patch).toHaveBeenCalledTimes(1);
    expect(patch.mock.calls[0][1]).toBe(6);                      // a revisão do cache
    expect(patch.mock.calls[0][2]).toEqual({
      desconto: { modo: 'VALOR', valor: 10000 },
      validade_dias: 20,
      observacoes_proposta: 'Saldo em 3x',
    });
    expect(salvamento.estado.value).toBe('salvo');
    expect(salvamento.salvoEm.value).not.toBeNull();             // "Salvo às hh:mm"
  });

  it('10 — detalhe novo chega com campo esperando: o que foi digitado fica', async () => {
    const { salvamento, detalhe } = preparar();
    salvamento.form.observacoes_proposta = 'digitando…';
    await nextTick();
    // Polling (ou outra ação) trouxe outra versão do campo.
    detalhe.value = { ...detalheFixture(), observacoes_proposta: 'do servidor', revisao: 7 };
    await nextTick();
    expect(salvamento.form.observacoes_proposta).toBe('digitando…');
    await andar(800);
    expect(patch.mock.calls[0][2]).toEqual({ observacoes_proposta: 'digitando…' }); // nada se perdeu
  });

  it('campo NÃO mexido segue o servidor (ex.: vendedor padrão)', async () => {
    const { salvamento, detalhe } = preparar();
    detalhe.value = { ...detalheFixture(), vendedor: { id: 9, nome: 'Alan', telefone: null }, revisao: 7 };
    await nextTick();
    expect(salvamento.form.funcionario_id).toBe(9);
    await andar(2000);
    expect(patch).not.toHaveBeenCalled();                        // não manda de volta o valor velho
  });

  it('11 — 422 com campo "desconto": erro no campo, valor mantido, sem nova tentativa', async () => {
    const { salvamento } = preparar();
    patch.mockRejectedValue(erroApi(422, {
      codigo: 'CALCULO_INVALIDO', campo: 'desconto', mensagem: 'O desconto não pode passar do total.',
    }));
    salvamento.form.desconto = { modo: 'VALOR', valor: 99999999 };
    await andar(800);
    expect(salvamento.estado.value).toBe('invalido');
    expect(salvamento.errosPorCampo.value.desconto).toBe('O desconto não pode passar do total.');
    expect(salvamento.form.desconto.valor).toBe(99999999);
    await andar(30000);
    expect(patch).toHaveBeenCalledTimes(1);                      // 422 não melhora repetindo
  });

  it('12 — erro de rede: tenta de novo em 2, 5 e 10 s; depois "Tentar agora"', async () => {
    const { salvamento } = preparar();
    patch.mockRejectedValue(erroRede());
    salvamento.form.prazo_entrega_dias = 45;
    await andar(800);
    expect(patch).toHaveBeenCalledTimes(1);
    expect(salvamento.tentandoDeNovo.value).toBe(true);          // "tentando de novo"
    for (const [indice, espera] of ESPERAS_NOVA_TENTATIVA_MS.entries()) {
      await andar(espera - 1);
      expect(patch).toHaveBeenCalledTimes(indice + 1);
      await andar(1);
      expect(patch).toHaveBeenCalledTimes(indice + 2);
    }
    await andar(60000);
    expect(patch).toHaveBeenCalledTimes(4);                      // 1 + 3 novas tentativas
    expect(salvamento.estado.value).toBe('erro');
    expect(salvamento.tentandoDeNovo.value).toBe(false);         // aparece o "Tentar agora"
    patch.mockImplementation(async (_id: number, revisao: number) => ({ ...detalheFixture(), revisao: revisao + 1 }));
    await salvamento.salvarAgora();
    expect(salvamento.estado.value).toBe('salvo');
  });

  it('13 — tela "novo": o primeiro campo real faz POST (não PATCH)', async () => {
    const criar = vi.fn(async (_corpo: unknown) => detalheFixture());
    const { salvamento } = preparar({ semDetalhe: true, criar });
    salvamento.form.validade_dias = 20;                           // não é "informação real" (D5)
    await andar(800);
    expect(criar).not.toHaveBeenCalled();
    salvamento.form.cliente_id = 5;
    await andar(800);
    expect(criar).toHaveBeenCalledTimes(1);
    expect(criar.mock.calls[0][0]).toMatchObject({ cliente_id: 5 });
    expect(patch).not.toHaveBeenCalled();
  });

  it('conflito: lista os campos não salvos; "Recarregar" descarta e volta ao servidor', async () => {
    const { salvamento, fila, detalhe } = preparar();
    patch.mockRejectedValue(erroApi(409, { codigo: 'REVISAO_DESATUALIZADA', mensagem: 'Alterado em outro computador.' }));
    salvamento.form.desconto = { modo: 'PERCENTUAL', valor: 1000 };
    salvamento.form.observacoes_proposta = 'nova';
    await andar(800);
    expect(fila.conflito.value).toBe(true);
    expect([...salvamento.camposPendentes.value].sort()).toEqual(['Desconto', 'Observações da proposta']);
    await salvamento.recarregarDescartando();
    expect(fila.conflito.value).toBe(false);
    // A versão atual chega (no editor, a query recarrega sozinha): o formulário vira ela.
    detalhe.value = { ...detalheFixture(), revisao: 9 };
    await nextTick();
    expect(salvamento.form.desconto).toEqual({ modo: 'PERCENTUAL', valor: 500 });
    expect(salvamento.form.observacoes_proposta).toBeNull();
    expect(salvamento.estado.value).toBe('salvo');
    expect(salvamento.camposPendentes.value).toEqual([]);
  });
});
