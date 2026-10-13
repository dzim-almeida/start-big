/**
 * BaseInput `sufixo` (remodelação item 4 da marcenaria): a unidade aparece no
 * fim do campo e não entra no valor; sem `sufixo`, nada muda.
 */
import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import BaseInput from '../BaseInput.vue';

describe('BaseInput — sufixo', () => {
  it('mostra a unidade e reserva espaço para ela', () => {
    const w = mount(BaseInput, { props: { modelValue: 2000, type: 'number', sufixo: 'mm' } });
    expect(w.find('[data-testid="input-sufixo"]').text()).toBe('mm');
    expect(w.find('input').classes()).toContain('pr-10');
  });

  it('a unidade não entra no valor digitado', async () => {
    const w = mount(BaseInput, { props: { modelValue: '', sufixo: 'mm', 'onUpdate:modelValue': () => {} } });
    await w.find('input').setValue('2000');
    const emitidos = w.emitted('update:modelValue') ?? [];
    expect(emitidos[emitidos.length - 1]).toEqual(['2000']);   // o último valor emitido
  });

  it('sem sufixo: campo como sempre foi', () => {
    const w = mount(BaseInput, { props: { modelValue: '' } });
    expect(w.find('[data-testid="input-sufixo"]').exists()).toBe(false);
    expect(w.find('input').classes()).not.toContain('pr-10');
  });
});
