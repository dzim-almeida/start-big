/**
 * Spec 04B (marcenaria, D14) — editor das listas de etapas e checklist
 * (casos 11 a 16).
 */
import { flushPromises, mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { defineComponent, h, ref } from 'vue';

import ListaTextosEditavel from '../ListaTextosEditavel.vue';

/** Monta o editor com a lista dada (e os limites da lista de etapas). */
function montar(lista: string[], extra: Record<string, unknown> = {}) {
  return mount(ListaTextosEditavel, {
    props: { modelValue: lista, maxItens: 3, maxCaracteres: 60, rotuloItem: 'etapa', ...extra },
    attachTo: document.body,           // para conferir o foco
  });
}

/** A última lista emitida pelo v-model. */
const ultimaLista = (wrapper: ReturnType<typeof montar>) => {
  const emissoes = wrapper.emitted('update:modelValue') ?? [];
  return emissoes[emissoes.length - 1]?.[0] as string[] | undefined;   // a mais recente
};

/** Botão pelo aria-label (ex.: "Subir etapa Borda"). */
const botao = (wrapper: ReturnType<typeof montar>, rotulo: string) => wrapper.find(`button[aria-label="${rotulo}"]`);

describe('ListaTextosEditavel', () => {
  it('11 — adicionar: item vazio no fim, com foco', async () => {
    // Um pai de verdade com v-model, como a seção Marcenaria usa o editor.
    const lista = ref(['Corte']);
    const Pai = defineComponent({
      setup: () => () => h(ListaTextosEditavel, {
        modelValue: lista.value,
        'onUpdate:modelValue': (nova: string[]) => { lista.value = nova; },
        maxItens: 3, maxCaracteres: 60, rotuloItem: 'etapa',
      }),
    });
    const wrapper = mount(Pai, { attachTo: document.body });   // foco só existe no documento

    await wrapper.findAll('button').find((b) => b.text().includes('Adicionar etapa'))!.trigger('click');
    await flushPromises();

    expect(lista.value).toEqual(['Corte', '']);                   // item vazio no fim
    const campos = wrapper.findAll('input');
    expect(document.activeElement).toBe(campos[1].element);      // o campo novo tem o foco
    wrapper.unmount();
  });

  it('12 — subir o 2º item troca com o 1º', async () => {
    const wrapper = montar(['Corte', 'Borda']);
    await botao(wrapper, 'Subir etapa Borda').trigger('click');
    expect(ultimaLista(wrapper)).toEqual(['Borda', 'Corte']);
    wrapper.unmount();
  });

  it('13 — com 1 item, "Remover" fica desabilitado (a lista nunca fica vazia)', () => {
    const wrapper = montar(['Corte']);
    expect(botao(wrapper, 'Remover etapa Corte').attributes('disabled')).toBeDefined();
    wrapper.unmount();
  });

  it('14 — "corte" com "Corte" já na lista mostra o erro de repetido no item', () => {
    const wrapper = montar(['Corte', 'corte']);
    const erros = wrapper.findAll('[data-testid="erro-item"]').map((e) => e.text());
    expect(erros).toEqual(['Item repetido.']);
    wrapper.unmount();
  });

  it('15 — no máximo de itens, "Adicionar" fica desabilitado', () => {
    const wrapper = montar(['A', 'B', 'C']);                     // maxItens = 3
    const adicionar = wrapper.findAll('button').find((b) => b.text().includes('Adicionar etapa'));
    expect(adicionar?.attributes('disabled')).toBeDefined();
    wrapper.unmount();
  });

  it('16 — desabilitado: nenhum campo editável nem botão ativo', () => {
    const wrapper = montar(['Corte', 'Borda'], { disabled: true });
    expect(wrapper.findAll('input').every((i) => i.attributes('disabled') !== undefined)).toBe(true);
    expect(wrapper.findAll('button').every((b) => b.attributes('disabled') !== undefined)).toBe(true);
    expect(wrapper.text()).not.toContain('Adicionar etapa');
    wrapper.unmount();
  });

  it('editar um item emite a lista com o texto novo', async () => {
    const wrapper = montar(['Corte', 'Borda']);
    await wrapper.findAll('input')[1].setValue('Fita de borda');
    expect(ultimaLista(wrapper)).toEqual(['Corte', 'Fita de borda']);
    wrapper.unmount();
  });
});

describe('ListaTextosEditavel — identidade e itens travados (Spec 12B)', () => {
  /** A última lista de identidades emitida. */
  const ultimosIds = (wrapper: ReturnType<typeof montar>) => {
    const emissoes = wrapper.emitted('update:ids') ?? [];
    return emissoes[emissoes.length - 1]?.[0] as (number | null)[] | undefined;
  };

  it('sem `ids`, nada de `update:ids` (Configurações › Marcenaria fica igual)', async () => {
    const wrapper = montar(['Corte', 'Borda']);
    await botao(wrapper, 'Descer etapa Corte').trigger('click');
    expect(ultimaLista(wrapper)).toEqual(['Borda', 'Corte']);
    expect(wrapper.emitted('update:ids')).toBeUndefined();
    wrapper.unmount();
  });

  it('a identidade anda com o item: descer, remover e adicionar (novo = null)', async () => {
    const wrapper = montar(['Corte', 'Borda', 'Montagem'], { ids: [1, 2, 3], maxItens: 5 });
    await botao(wrapper, 'Descer etapa Corte').trigger('click');
    expect(ultimaLista(wrapper)).toEqual(['Borda', 'Corte', 'Montagem']);
    expect(ultimosIds(wrapper)).toEqual([2, 1, 3]);
    await botao(wrapper, 'Remover etapa Borda').trigger('click');
    expect(ultimosIds(wrapper)).toEqual([1, 3]);
    await wrapper.find('button:not([aria-label])').trigger('click');          // "Adicionar etapa"
    expect(ultimosIds(wrapper)).toEqual([1, 2, 3, null]);
    wrapper.unmount();
  });

  it('item travado: não renomeia nem remove (com o motivo), mas sobe e desce', async () => {
    const motivo = 'Etapa concluída: reabra antes de remover ou renomear.';
    const wrapper = montar(['Corte', 'Borda'], { ids: [1, 2], travados: [true, false], motivoTravado: motivo });
    const campo = wrapper.find('input[aria-label="etapa 1"]');
    expect((campo.element as HTMLInputElement).readOnly).toBe(true);
    expect(campo.attributes('title')).toBe(motivo);
    const remover = botao(wrapper, 'Remover etapa Corte');
    expect(remover.attributes('disabled')).toBeDefined();
    expect(remover.attributes('title')).toBe(motivo);
    await campo.setValue('Corte novo');
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();            // não renomeou
    await botao(wrapper, 'Descer etapa Corte').trigger('click');
    expect(ultimaLista(wrapper)).toEqual(['Borda', 'Corte']);                 // mover vale
    wrapper.unmount();
  });
});
