/**
 * "CFOP desta nota" (C2 de docs/nfe-cfop-e-notas-da-os-plano.md).
 *
 * O que não pode errar: um campo por grupo (nunca por item), a troca é dita
 * pelo CFOP SUGERIDO, voltar ao sugerido desfaz a troca, e o CFOP decidido
 * pela operação aparece travado.
 */
import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import CfopDaNotaCampo from '../CfopDaNotaCampo.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { GrupoCfop } from '../../../types/fiscal.types';

const INTERNA = ['5101', '5102', '5103', '5104', '5405'].map((cfop) => ({ cfop, descricao: `desc ${cfop}` }));

const grupo = (sugerido: string, cfop = sugerido, itens = [1], opcoes = INTERNA): GrupoCfop => ({
  cfop_sugerido: sugerido, cfop, descricao: '', itens, opcoes,
});

describe('CfopDaNotaCampo', () => {
  it('um grupo: um campo "CFOP desta nota"; escolher grava a troca pelo sugerido', async () => {
    const wrapper = mount(CfopDaNotaCampo, { props: { grupos: [grupo('5102')], trocas: {} } });

    expect(wrapper.text()).toContain('CFOP desta nota');
    expect(wrapper.findAllComponents(BaseSelect)).toHaveLength(1);

    wrapper.findComponent(BaseSelect).vm.$emit('update:modelValue', '5101');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:trocas')![0]).toEqual([{ '5102': '5101' }]);
    expect(wrapper.emitted('alterou')).toHaveLength(1);
  });

  it('nota mista: um campo por grupo, cada um com os seus itens', () => {
    const wrapper = mount(CfopDaNotaCampo, {
      props: { grupos: [grupo('5102', '5102', [1, 3]), grupo('5405', '5405', [2])], trocas: {} },
    });

    expect(wrapper.findAllComponents(BaseSelect)).toHaveLength(2);
    expect(wrapper.text()).toContain('Itens 1, 3 (sugerido 5102)');
    expect(wrapper.text()).toContain('Item 2 (sugerido 5405)');
  });

  it('voltar ao sugerido desfaz a troca e some com o aviso', async () => {
    const wrapper = mount(CfopDaNotaCampo, {
      props: { grupos: [grupo('5102', '5101')], trocas: { '5102': '5101' }, comoPadrao: true },
    });
    expect(wrapper.find('[data-aviso-troca]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Diferente do cadastro do produto');

    wrapper.findComponent(BaseSelect).vm.$emit('update:modelValue', '5102');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:trocas')![0]).toEqual([{}]);
    expect(wrapper.emitted('update:comoPadrao')![0]).toEqual([false]);
  });

  it('CFOP decidido pela operação aparece travado, sem campo', () => {
    const wrapper = mount(CfopDaNotaCampo, {
      props: { grupos: [{ ...grupo('5922'), descricao: 'Simples faturamento', opcoes: [] }], trocas: {} },
    });

    expect(wrapper.findAllComponents(BaseSelect)).toHaveLength(0);
    expect(wrapper.text()).toContain('5922');
    expect(wrapper.text()).toContain('definido pela operação');
  });

  it('sem grupos (backend antigo): não mostra nada', () => {
    const wrapper = mount(CfopDaNotaCampo, { props: { grupos: [], trocas: {} } });
    expect(wrapper.find('[data-cfop-da-nota]').exists()).toBe(false);
  });
});
