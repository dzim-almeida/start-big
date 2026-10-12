/**
 * Spec 03B (marcenaria, D6) — o tipo de trabalho na aba do objeto.
 *
 * Numa OS de Móveis planejados (que nasce do orçamento), o tipo aparece como
 * informação, com o motivo, e não como seletor. Na serigrafia, o seletor
 * Camisa/Sacola continua como sempre. O contrato do segmento é SIMULADO.
 */
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

import type { SegmentDefinitionResponse } from '@/modules/order-service/shared/segmento/segmentDefinition.type';

const contrato = ref<SegmentDefinitionResponse | undefined>();   // resposta do backend
const segmentoAtual = ref<string | null>(null);                  // segmento da empresa logada

vi.mock('@/modules/order-service/shared/segmento/useOSFieldDefinition.queries', () => ({
  useOSFieldDefinition: () => ({ data: contrato, isPending: ref(false) }),
}));
vi.mock('@/shared/composables/useSegmento', () => ({
  useSegmento: () => ({ segmento: segmentoAtual }),
}));

const { default: OSObjetoDinamicoTab } = await import('../OSObjetoDinamicoTab.vue');
const { default: BaseSelect } = await import('@/shared/components/ui/BaseSelect/BaseSelect.vue');

/** Contrato carregado com os tipos dados (sem campos: aqui só importa o tipo). */
function contratoCom(segmento: string, tipos: Array<{ id: string; label: string; criacao_manual?: boolean }>) {
  return {
    segmento,
    tem_definicao: true,
    definicao: { segmento, rotulo_objeto_singular: 'Objeto', tipos: tipos.map((t) => ({ ...t, campos: [] })) },
  } as unknown as SegmentDefinitionResponse;
}

/** Formulário do objeto vazio (o que o modal de OS passa para a aba). */
const OBJETO_VAZIO = {
  objeto: '', marca: '', modelo: '', numero_serie: '', imei: '', cor: '',
  senha_aparelho: '', acessorios: '', defeito_relatado: '', condicoes_aparelho: '',
};

/** Monta a aba com os dados da OS dados (onde fica o tipo gravado). */
function montar(osDados: Record<string, unknown>) {
  return mount(OSObjetoDinamicoTab, { props: { modelValue: OBJETO_VAZIO, osDados } });
}

describe('tipo de trabalho na aba do objeto', () => {
  it('14 — OS de Planejados: texto do tipo travado e nenhum seletor de tipo', () => {
    segmentoAtual.value = 'marcenaria';
    contrato.value = contratoCom('marcenaria', [{ id: 'planejados', label: 'Móveis planejados', criacao_manual: false }]);

    const wrapper = montar({ tipo_trabalho: 'planejados' });

    const travado = wrapper.find('[data-testid="tipo-travado"]');
    expect(travado.exists()).toBe(true);
    expect(travado.text()).toContain('Móveis planejados');
    expect(travado.text()).toContain('criada a partir de um orçamento');
    // Nenhum seletor na aba (o de histórico só aparece na abertura da OS).
    expect(wrapper.findAllComponents(BaseSelect)).toHaveLength(0);
  });

  it('15 — serigrafia: o seletor Camisa/Sacola como sempre, sem o texto de travado', () => {
    segmentoAtual.value = 'serigrafia';
    contrato.value = contratoCom('serigrafia', [
      { id: 'camisa', label: 'Camisa', criacao_manual: true },
      { id: 'sacola_plastica', label: 'Sacola plástica', criacao_manual: true },
    ]);

    const wrapper = montar({ tipo_trabalho: 'camisa' });

    expect(wrapper.find('[data-testid="tipo-travado"]').exists()).toBe(false);
    const seletores = wrapper.findAllComponents(BaseSelect);
    expect(seletores).toHaveLength(1);                             // o seletor de tipo
    expect(seletores[0].props('modelValue')).toBe('camisa');
  });
});
