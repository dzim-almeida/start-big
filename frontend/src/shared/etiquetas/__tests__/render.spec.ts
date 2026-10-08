import { describe, expect, it, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';

import EtiquetaView from '../components/EtiquetaView.vue';
import EtiquetasImpressao from '../components/EtiquetasImpressao.vue';
import { PRESETS } from '../presets';
import { valoresDoProduto } from '../campos';

const rolo50x30 = PRESETS.find((p) => p.chave === 'preset:rolo-50x30')!.definicao;
const pimaco6180 = PRESETS.find((p) => p.chave === 'preset:pimaco-6180')!.definicao;

const produto = valoresDoProduto({
  nome: 'Parafuso Sextavado',
  codigo_produto: 'PRF-10',
  codigo_barras: '7891000100103',
  estoque: { valor_varejo: 1290 },
});

afterEach(() => {
  document.body.innerHTML = '';
});

describe('EtiquetaView', () => {
  it('desenha nome, preço e as barras do EAN com a legenda', () => {
    const wrapper = mount(EtiquetaView, { props: { definicao: rolo50x30, valores: produto } });
    const texto = wrapper.text();
    expect(texto).toContain('Parafuso Sextavado');
    expect(texto).toMatch(/12,90/);
    expect(texto).toContain('7891000100103');

    const svg = wrapper.find('svg');
    expect(svg.exists()).toBe(true);
    // JsBarcode desenhou barras, e o SVG ficou esticável (viewBox, sem largura fixa).
    expect(svg.findAll('rect').length).toBeGreaterThan(10);
    expect(svg.attributes('viewBox')).toBeTruthy();
    expect(svg.attributes('preserveAspectRatio')).toBe('none');
    expect(svg.attributes('width')).toBeUndefined();

    expect(wrapper.attributes('style')).toContain('width: 50mm');
  });

  it('produto sem código nenhum mostra o aviso em vez de barras', () => {
    const semCodigo = valoresDoProduto({ nome: 'Avulso' });
    const wrapper = mount(EtiquetaView, { props: { definicao: rolo50x30, valores: semCodigo } });
    expect(wrapper.find('svg').exists()).toBe(false);
    expect(wrapper.text()).toContain('sem código');
  });
});

describe('EtiquetasImpressao', () => {
  it('bobina: uma página por etiqueta, com o tamanho do rolo', () => {
    mount(EtiquetasImpressao, {
      props: { definicao: rolo50x30, etiquetas: [produto, produto, produto], pular: 0, deslocamentoX: 0, deslocamentoY: 0 },
    });
    const container = document.body.querySelector('.print-container.etiquetas-print')!;
    const paginas = container.querySelectorAll<HTMLElement>('.etiquetas-pagina');
    expect(paginas).toHaveLength(3);
    expect(paginas[0].style.width).toBe('50mm');
    expect(paginas[0].style.height).toBe('29.5mm');
  });

  it('folha: pula as posições usadas e aplica a calibração do terminal', () => {
    mount(EtiquetasImpressao, {
      props: { definicao: pimaco6180, etiquetas: [produto, produto], pular: 3, deslocamentoX: 1, deslocamentoY: -0.5 },
    });
    const paginas = document.body.querySelectorAll('.etiquetas-pagina');
    expect(paginas).toHaveLength(1);
    const posicoes = paginas[0].querySelectorAll<HTMLElement>('.etiquetas-posicao');
    // Posição 3 = primeira coluna da SEGUNDA linha: x = margem (4,8) + 1; y = 12,7 + 25,4 − 0,5.
    expect(posicoes[0].style.left).toBe('5.8mm');
    expect(parseFloat(posicoes[0].style.top)).toBeCloseTo(37.6, 5);
  });
});
