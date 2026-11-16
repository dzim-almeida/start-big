/**
 * Spec 03B (marcenaria, D11–D14) — as portas de entrada da fábrica saíram das
 * telas (SPEC-00, FB1). A pasta `order-service/fabrica/` continua no projeto,
 * inerte, até a limpeza depois do piloto: estes testes provam que nenhuma tela
 * a abre mais e que nada mudou para os outros segmentos.
 */
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { RouteRecordRaw } from 'vue-router';

// A tela de Configurações › OS busca a configuração no backend; aqui não há
// backend, então a busca vira uma função que não faz nada.
vi.mock('@/modules/configuracoes/composables/queries/useConfiguracoesOSQuery', () => ({
  useConfiguracoesOSQuery: () => ({}),
}));

const { default: OrdensDeServico } = await import(
  '@/modules/configuracoes/components/sections/ordens-de-servico/components/OrdensDeServico.vue'
);
const { useConfiguracoesStore } = await import('@/shared/stores/configuracoes.store');
const { default: rotas } = await import('@/modules/mainLayout/routes');
const { default: fonteProductModal } = await import('@/modules/products/inventory/components/ProductModal.vue?raw');

/** Todos os nomes de rota, inclusive os das rotas filhas. */
function nomesDasRotas(lista: readonly RouteRecordRaw[]): string[] {
  return lista.flatMap((rota) => [String(rota.name ?? ''), ...nomesDasRotas(rota.children ?? [])]);
}

beforeEach(() => setActivePinia(createPinia()));

describe('Configurações › OS', () => {
  /** Monta a tela com a configuração que "veio do backend" (modo fábrica ligado). */
  function montar() {
    const store = useConfiguracoesStore();
    // Uma loja que tinha ligado o modo fábrica antes da aposentadoria.
    store.configOS = { modo_fabrica: true, fabrica_travar_etapas: true } as never;
    return mount(OrdensDeServico);
  }

  it('19 — sem as caixas "Modo fábrica" e "Travar etapas"', () => {
    const texto = montar().text();
    expect(texto).not.toContain('Modo fábrica');
    expect(texto).not.toContain('Travar etapas');
    expect(texto).not.toContain('Fábrica de planejados');
  });

  it('23 — o corpo do PUT leva os dois campos com o valor que veio do backend', () => {
    const wrapper = montar();
    // `form` é o que o modal de Configurações envia ao salvar (defineExpose).
    const corpo = (wrapper.vm as unknown as { form: Record<string, unknown> }).form;
    expect(corpo.modo_fabrica).toBe(true);
    expect(corpo.fabrica_travar_etapas).toBe(true);
  });
});

describe('outras portas de entrada', () => {
  it('21 — o produto não abre mais a seção "Insumo da fábrica"', () => {
    // Confere o código do modal (montá-lo exigiria todas as abas do produto):
    // nem o componente da seção nem nada da pasta da fábrica é importado.
    expect(fonteProductModal).not.toContain('InsumoProdutoSection');
    expect(fonteProductModal).not.toContain('order-service/fabrica/');
  });

  it('22 — a rota da separação da fábrica não existe mais', () => {
    expect(nomesDasRotas(rotas)).not.toContain('fabrica-separacao');
  });
});
