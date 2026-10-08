import { describe, expect, it } from 'vitest';
import { defineComponent, h, ref } from 'vue';
import { mount } from '@vue/test-utils';

import { encaixar, mover, novoElemento, problemasDosElementos, redimensionar, NOVOS_ELEMENTOS } from '../editor/operacoes';
import { useHistorico } from '../editor/useHistorico';
import EditorEtiqueta from '../editor/EditorEtiqueta.vue';
import type { ElementoEtiqueta, PaginaEtiqueta } from '../modelo';
import { VALORES_EXEMPLO } from '../campos';

const pagina: PaginaEtiqueta = {
  tipo: 'bobina', largura_mm: 50, altura_mm: 30, colunas: 1,
  espaco_colunas_mm: 0, espaco_linhas_mm: 0, margem_esq_mm: 0, margem_topo_mm: 0, folha: null,
};

const caixaTexto: ElementoEtiqueta = { tipo: 'texto', x: 2, y: 2, w: 20, h: 6, campo: 'produto.nome', fonte_pt: 8 };

describe('operações do editor', () => {
  it('mover encaixa no passo de 0,5 mm e não deixa sair da etiqueta', () => {
    expect(mover(caixaTexto, pagina, 10.26, 3.1)).toMatchObject({ x: 10.5, y: 3 });
    expect(mover(caixaTexto, pagina, 45, -4)).toMatchObject({ x: 30, y: 0 });
  });

  it('com o passo fino (Alt), o arraste fica livre em décimos', () => {
    expect(mover(caixaTexto, pagina, 10.26, 3.14, 0.1)).toMatchObject({ x: 10.3, y: 3.1 });
  });

  it('redimensionar respeita o mínimo e a borda', () => {
    expect(redimensionar(caixaTexto, pagina, 0.2, 100)).toMatchObject({ w: 2, h: 28 });
  });

  it('linha só muda de largura', () => {
    const linha: ElementoEtiqueta = { tipo: 'linha', x: 0, y: 10, w: 20, h: 0, espessura_mm: 0.3 };
    expect(redimensionar(linha, pagina, 30, 15)).toMatchObject({ w: 30, h: 0 });
  });

  it('encaixar traz para dentro o que sobrou fora quando a etiqueta diminui', () => {
    const grande: ElementoEtiqueta = { ...caixaTexto, x: 30, y: 20, w: 60, h: 8 };
    const dentro = encaixar(grande, pagina);
    expect(dentro).toMatchObject({ x: 0, y: 20, w: 50, h: 8 });
    expect(problemasDosElementos([dentro], pagina)).toEqual([]);
    expect(problemasDosElementos([grande], pagina)[0]).toContain('elemento 1');
  });

  it.each(NOVOS_ELEMENTOS.map((n) => n.tipo))('elemento novo "%s" nasce dentro de uma etiqueta pequena', (tipo) => {
    const pequena = { ...pagina, largura_mm: 20, altura_mm: 10 };
    expect(problemasDosElementos([novoElemento(tipo, pequena)], pequena)).toEqual([]);
  });
});

describe('histórico', () => {
  it('desfaz e refaz por gesto registrado', () => {
    const lista = ref([1]);
    const h = useHistorico(lista);
    lista.value = [1, 2];
    h.registrar();
    lista.value = [1, 2, 3];
    h.registrar();

    h.desfazer();
    expect(lista.value).toEqual([1, 2]);
    h.desfazer();
    expect(lista.value).toEqual([1]);
    expect(h.podeDesfazer.value).toBe(false);
    h.refazer();
    expect(lista.value).toEqual([1, 2]);
  });

  it('registrar sem mudança não cria passo vazio', () => {
    const lista = ref([1]);
    const h = useHistorico(lista);
    h.registrar();
    expect(h.podeDesfazer.value).toBe(false);
  });
});

describe('EditorEtiqueta', () => {
  // Pai de verdade com v-model: o editor escreve na lista e relê dela.
  function montar(inicial: ElementoEtiqueta[]) {
    const lista = ref<ElementoEtiqueta[]>(inicial);
    const Pai = defineComponent(() => () =>
      h(EditorEtiqueta, {
        pagina,
        valores: VALORES_EXEMPLO,
        elementos: lista.value,
        'onUpdate:elementos': (novos: ElementoEtiqueta[]) => (lista.value = novos),
      }),
    );
    return { wrapper: mount(Pai, { attachTo: document.body }), lista };
  }

  it('seleciona, move com a seta, apaga com Delete e desfaz com Ctrl+Z', async () => {
    const { wrapper, lista } = montar([caixaTexto]);
    const canvas = wrapper.find('[tabindex="0"]');

    await wrapper.find('.alca').trigger('pointerdown');
    await canvas.trigger('pointerup');
    expect(wrapper.text()).toContain('Conteúdo');

    await canvas.trigger('keydown', { key: 'ArrowRight' });
    expect(lista.value[0].x).toBe(2.5);

    await canvas.trigger('keydown', { key: 'Delete' });
    expect(lista.value).toHaveLength(0);

    await canvas.trigger('keydown', { key: 'z', ctrlKey: true });
    expect(lista.value).toHaveLength(1);
    expect(lista.value[0].x).toBe(2.5);
    wrapper.unmount();
  });

  it('adicionar um código de barras pelo menu', async () => {
    const { wrapper, lista } = montar([]);
    await wrapper.find('.ferramenta--primaria').trigger('click');
    const opcao = wrapper.findAll('button').find((b) => b.text() === 'Código de barras')!;
    await opcao.trigger('click');
    expect(lista.value).toHaveLength(1);
    expect(lista.value[0].tipo).toBe('barras');
    wrapper.unmount();
  });
});
