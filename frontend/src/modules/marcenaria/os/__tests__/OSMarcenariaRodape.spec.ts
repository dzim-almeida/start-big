/**
 * Remodelação item 21: "Avançar para Aguardando Entrega" salvava o status,
 * mas a tela dizia "Não foi possível mudar a situação da OS". O aviso era
 * montado DEPOIS de gravar, quando o "próximo status" já tinha mudado (e na
 * última etapa não existe próximo: o rótulo de `null` quebrava).
 */
import { flushPromises, mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';

const toast = { success: vi.fn(), error: vi.fn() };
vi.mock('@/shared/composables/useToast', () => ({ useToast: () => toast }));
vi.mock('@/modules/marcenaria/orcamentos/composables/useOrcamentoDaOS', () => ({ useOrcamentoDaOS: () => ({ data: ref(null) }) }));

const { default: OSMarcenariaRodape } = await import('../components/OSMarcenariaRodape.vue');

/** Como o rótulo de verdade: status desconhecido (ou nenhum) quebra. */
const ROTULOS: Record<string, { label: string }> = {
  ABERTA: { label: 'Aberta' }, EM_ANDAMENTO: { label: 'Em Produção' }, AGUARDANDO_RETIRADA: { label: 'Aguardando Entrega' },
};
const rotulo = (status: string) => ROTULOS[status].label;

/** Monta o rodapé dentro de um "pai" que troca o status depois de gravar, como o modal da OS. */
function montar(statusInicial: string) {
  const status = ref(statusInicial);
  const avancar = vi.fn(async (novo: string) => { status.value = novo; });
  const Pai = defineComponent({
    setup: () => () => h(OSMarcenariaRodape, {
      numeroOs: 'OS-2026-000001', totalCentavos: 100, status: status.value, rotulo, travada: false, avancar,
    }),
  });
  return { wrapper: mount(Pai), avancar };
}

describe('OSMarcenariaRodape — avançar status (remodelação item 21)', () => {
  it('Em Produção → Aguardando Entrega (a última etapa): sucesso, sem o aviso de erro', async () => {
    toast.success.mockReset(); toast.error.mockReset();
    const { wrapper, avancar } = montar('EM_ANDAMENTO');
    await wrapper.find('[data-testid="avancar-status"]').trigger('click');
    await flushPromises();
    expect(avancar).toHaveBeenCalledWith('AGUARDANDO_RETIRADA');
    expect(toast.error).not.toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalledWith('OS movida para Aguardando Entrega.');
  });

  it('Aberta → Em Produção: o aviso diz o status para onde foi (não o seguinte)', async () => {
    toast.success.mockReset(); toast.error.mockReset();
    const { wrapper } = montar('ABERTA');
    await wrapper.find('[data-testid="avancar-status"]').trigger('click');
    await flushPromises();
    expect(toast.success).toHaveBeenCalledWith('OS movida para Em Produção.');
  });

  it('erro de verdade ao gravar: continua avisando', async () => {
    toast.success.mockReset(); toast.error.mockReset();
    const { wrapper, avancar } = montar('EM_ANDAMENTO');
    avancar.mockRejectedValueOnce(new Error('rede'));
    await wrapper.find('[data-testid="avancar-status"]').trigger('click');
    await flushPromises();
    expect(toast.error).toHaveBeenCalledWith('Não foi possível mudar a situação da OS. Tente de novo.');
    expect(toast.success).not.toHaveBeenCalled();
  });
});
