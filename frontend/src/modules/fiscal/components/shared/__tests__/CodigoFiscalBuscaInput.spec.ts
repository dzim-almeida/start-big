/**
 * Campo de código da NFS-e (docs/nfse-plano.md, F1).
 *
 * O que não pode errar: o banco recebe só os dígitos, a tela mostra o código
 * como o portal escreve, e o NBS sugerido aparece ao focar — é o que responde
 * ao "não sei qual é o meu NBS".
 */
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

import CodigoFiscalBuscaInput from '../CodigoFiscalBuscaInput.vue';
import { formatarCodigoNacional, formatarNbs } from '../../../utils/nfse.utils';

/** O último evento emitido (sem `.at()`: o lib do tsconfig é anterior ao ES2022). */
const ultimo = <T>(lista: T[]) => lista[lista.length - 1];

const SUPORTE_TI = { codigo: '115013000', descricao: 'Serviços de suporte em TI', descricao_completa: null };

function montar(props: Record<string, unknown> = {}) {
  return mount(CodigoFiscalBuscaInput, {
    props: {
      modelValue: '',
      label: 'NBS',
      digitos: 9,
      formatar: formatarNbs,
      buscar: vi.fn().mockResolvedValue([]),
      ...props,
    },
  });
}

describe('formatação', () => {
  it('escreve como o portal da NFS-e', () => {
    expect(formatarCodigoNacional('010701')).toBe('01.07.01');
    expect(formatarNbs('115013000')).toBe('1.1501.30.00');
    expect(formatarNbs('1150')).toBe('1150'); // incompleto fica como está
  });
});

describe('CodigoFiscalBuscaInput', () => {
  it('código completo digitado com pontos grava só os dígitos, sem buscar', async () => {
    const buscar = vi.fn();
    const wrapper = montar({ buscar });
    await wrapper.find('input').setValue('1.1501.30.00');

    expect(ultimo(wrapper.emitted('update:modelValue')!)).toEqual(['115013000']);
    expect(buscar).not.toHaveBeenCalled();
  });

  // Espera de verdade (os 300 ms do campo), e não relógio falso: o Vue descarta
  // evento com horário anterior ao do listener, e o relógio falso faz o clique
  // da lista parecer "do passado".
  it('texto busca no servidor e escolher grava o código', async () => {
    const buscar = vi.fn().mockResolvedValue([SUPORTE_TI]);
    const wrapper = montar({ buscar });

    await wrapper.find('input').setValue('suporte');
    await vi.waitFor(() => expect(wrapper.findAll('li').length).toBe(1));

    await wrapper.find('li').trigger('mousedown');
    expect(buscar).toHaveBeenCalledWith('suporte');
    expect(ultimo(wrapper.emitted('update:modelValue')!)).toEqual(['115013000']);
    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('1.1501.30.00');
  });

  it('ao focar, mostra os sugeridos sem precisar digitar', async () => {
    const wrapper = montar({ sugeridos: [SUPORTE_TI] });
    await wrapper.find('input').trigger('focusin');

    expect(wrapper.text()).toContain('Sugeridos para este serviço');
    expect(wrapper.text()).toContain('1.1501.30.00 · Serviços de suporte em TI');
  });

  it('código que chega da edição aparece formatado, com a descrição do sugerido', () => {
    const wrapper = montar({ modelValue: '115013000', sugeridos: [SUPORTE_TI] });

    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('1.1501.30.00');
    expect(wrapper.text()).toContain('Serviços de suporte em TI');
  });

  it('falha da busca (sem módulo) não vira erro: o campo segue aceitando digitação', async () => {
    const buscar = vi.fn().mockRejectedValue(new Error('403'));
    const wrapper = montar({ buscar });

    await wrapper.find('input').setValue('suporte');
    await vi.waitFor(() => expect(buscar).toHaveBeenCalled());

    expect(wrapper.findAll('li')).toHaveLength(0);
    await wrapper.find('input').setValue('115013000');
    expect(ultimo(wrapper.emitted('update:modelValue')!)).toEqual(['115013000']);
  });
});
