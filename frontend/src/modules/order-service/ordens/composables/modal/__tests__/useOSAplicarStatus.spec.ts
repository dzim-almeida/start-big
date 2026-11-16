/**
 * Spec 12B ⚠️ código compartilhado da OS — casos 08 e 14.
 *
 * - 08: "Mover" (a pergunta de status da produção) grava SÓ o status; uma
 *   observação digitada e não salva continua no formulário e não vai junto.
 * - 14: `openExistingOS(os)` sem o parâmetro novo abre na aba de sempre.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { computed, ref } from 'vue';

import type { OrderServiceReadDataType } from '../../../schemas/orderServiceQuery.schema';

const updateOrderService = vi.fn();
vi.mock('../../../services/orderServiceUpdate.service', () => ({
  updateOrderService: (...a: unknown[]) => updateOrderService(...a),
}));

const { useOSAplicarStatus } = await import('../useOSAplicarStatus');
const { useOSCreateFlow } = await import('../../useOSCreateFlow');
const { montarComposable } = await import('@/modules/marcenaria/orcamentos/__tests__/apoio');

/** A OS persistida (o que o modal abriu) — só o que importa aqui. */
const persistida = () =>
  ({ numero_os: 'OS-2026-000001', status: 'ABERTA', observacoes: 'antiga' }) as unknown as OrderServiceReadDataType;

afterEach(() => { updateOrderService.mockReset(); });

describe('08 — aplicar só o status', () => {
  it('o PUT vai só com o status; a observação não salva fica no formulário', async () => {
    const localOSData = ref<OrderServiceReadDataType | null>(persistida());
    const currentOSData = computed(() => localOSData.value);
    const campoStatus = ref<string | null | undefined>('ABERTA');
    const observacaoNaTela = ref('digitada e não salva');                    // outro campo do formulário
    updateOrderService.mockResolvedValue({ numero_os: 'OS-2026-000001', status: 'EM_ANDAMENTO', observacoes: 'antiga' });

    const { resultado, wrapper } = montarComposable(() =>
      useOSAplicarStatus({ osNumber: computed(() => 'OS-2026-000001'), currentOSData, localOSData, campoStatus }));
    await resultado.aplicarStatusSalvo('EM_ANDAMENTO');

    expect(updateOrderService).toHaveBeenCalledWith({ osNumber: 'OS-2026-000001', updatedOS: { status: 'EM_ANDAMENTO' } });
    expect(campoStatus.value).toBe('EM_ANDAMENTO');                          // o campo da tela
    expect(localOSData.value?.status).toBe('EM_ANDAMENTO');                   // e o persistido
    expect(observacaoNaTela.value).toBe('digitada e não salva');              // intocada
    wrapper.unmount();
  });

  it('erro no PUT: sobe para quem chamou e nada muda na tela', async () => {
    const localOSData = ref<OrderServiceReadDataType | null>(persistida());
    const campoStatus = ref<string | null | undefined>('ABERTA');
    updateOrderService.mockRejectedValue(new Error('rede'));
    const { resultado, wrapper } = montarComposable(() => useOSAplicarStatus({
      osNumber: computed(() => 'OS-2026-000001'), currentOSData: computed(() => localOSData.value), localOSData, campoStatus,
    }));
    await expect(resultado.aplicarStatusSalvo('EM_ANDAMENTO')).rejects.toThrow('rede');
    expect(campoStatus.value).toBe('ABERTA');
    wrapper.unmount();
  });
});

describe('14 — openExistingOS sem aba inicial', () => {
  it('sem o parâmetro novo, a aba pedida fica vazia (abre em "objeto")', () => {
    const fluxo = useOSCreateFlow();
    fluxo.openExistingOS(persistida(), false, { abaInicial: 'producao' });
    expect(fluxo.abaInicial.value).toBe('producao');
    fluxo.openExistingOS(persistida());                                       // como o sino e a lista chamam
    expect(fluxo.abaInicial.value).toBeNull();
    fluxo.closeFormModal();
  });
});
