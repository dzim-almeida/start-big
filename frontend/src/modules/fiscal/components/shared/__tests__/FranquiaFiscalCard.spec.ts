/**
 * Saldo da franquia fiscal (docs/nfse-fase2-plano.md, G1). Só informa; some
 * quando a plataforma não respondeu ou a franquia ainda não vale.
 */
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const dados = ref<any>(null);
vi.mock('@tanstack/vue-query', () => ({ useQuery: () => ({ data: dados }) }));

const { default: FranquiaFiscalCard } = await import('../FranquiaFiscalCard.vue');

const BASE = {
  consultou: true, competencia: '2026-11', vigente: true, franquia: 70, precoExcedente: 1,
  formaCobranca: 'CARTAO', limite: 300,
};

describe('Franquia do mês', () => {
  it('cartão acima da franquia: mostra os extras e o valor do dia 1º', () => {
    dados.value = { ...BASE, emitidas: 74, restantesNaFranquia: 0, excedentes: 4, valorExcedente: 4, restantes: 226 };
    const texto = mount(FranquiaFiscalCard).text();
    expect(texto).toContain('74 de 70 notas no mês');
    expect(texto).toContain('4 extras');
    expect(texto).toContain('4,00 no dia 1º');
  });

  it('PIX perto do fim: alerta em âmbar', () => {
    dados.value = { ...BASE, formaCobranca: 'PIX', limite: 70, emitidas: 67, restantesNaFranquia: 3, excedentes: 0, valorExcedente: 0, restantes: 3 };
    const wrapper = mount(FranquiaFiscalCard);
    expect(wrapper.text()).toContain('restam 3');
    expect(wrapper.find('[data-franquia-fiscal]').classes()).toContain('border-amber-300');
  });

  it('sem resposta da plataforma ou antes de valer: não aparece', () => {
    dados.value = { consultou: false };
    expect(mount(FranquiaFiscalCard).find('[data-franquia-fiscal]').exists()).toBe(false);
    dados.value = { ...BASE, vigente: false, emitidas: 10, restantesNaFranquia: 60, excedentes: 0, valorExcedente: 0, restantes: 60 };
    expect(mount(FranquiaFiscalCard).find('[data-franquia-fiscal]').exists()).toBe(false);
  });
});
