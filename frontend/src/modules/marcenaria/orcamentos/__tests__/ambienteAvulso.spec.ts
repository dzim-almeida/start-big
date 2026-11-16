/**
 * Remodelação item 3: "Móvel avulso" usa (ou cria) o ambiente "Avulso" e abre
 * o cadastro do móvel nele.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { computed, defineComponent, h, ref } from 'vue';

import BlocoAmbientes from '../components/editor/BlocoAmbientes.vue';
import { proverEditor, type EditorContexto } from '../composables/useEditorContexto';
import type { OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import { detalheFixture } from './apoio';

/** O detalhe da fixture com os ambientes trocados pelos nomes pedidos (ids 101, 102...). */
function comAmbientes(nomes: string[]): OrcamentoDetalhe {
  const d = detalheFixture();
  const modelo = d.ambientes[0];
  return { ...d, ambientes: nomes.map((nome, i) => ({ ...modelo, id: 101 + i, nome, moveis: [] })) } as OrcamentoDetalhe;
}

/** Monta o bloco com um editor de mentira: só o que o bloco usa. */
function montar(detalheInicial: OrcamentoDetalhe) {
  const detalhe = ref<OrcamentoDetalhe | undefined>(detalheInicial);
  const abrirMovel = vi.fn();
  // criarAmbiente responde como a API: o orçamento inteiro, já com o ambiente novo no fim.
  const criarAmbiente = vi.fn(async (nome: string) => {
    const novo = comAmbientes([...detalhe.value!.ambientes.map((a) => a.nome), nome]);
    detalhe.value = novo;
    return novo;
  });
  const Pai = defineComponent({
    setup() {
      proverEditor({
        id: ref(1),
        detalhe,
        editavel: computed(() => true),
        incluiCustos: computed(() => false),
        acoesOrcamento: { criarAmbiente } as unknown as EditorContexto['acoesOrcamento'],
        garantirOrcamento: async () => 1,
        abrirMovel,
      } as unknown as EditorContexto);
      return () => h(BlocoAmbientes);
    },
  });
  return { wrapper: mount(Pai), abrirMovel, criarAmbiente };
}

describe('Móvel avulso (remodelação item 3)', () => {
  it('sem ambiente "Avulso": cria e abre o móvel nele', async () => {
    const { wrapper, abrirMovel, criarAmbiente } = montar(comAmbientes(['Cozinha']));
    await wrapper.find('[data-testid="movel-avulso"]').trigger('click');
    await flushPromises();
    expect(criarAmbiente).toHaveBeenCalledWith('Avulso');
    expect(abrirMovel).toHaveBeenCalledWith(102);           // o 2º ambiente, o recém-criado
  });

  it('com "avulso" já existente (qualquer maiúscula): não cria outro, só abre', async () => {
    const { wrapper, abrirMovel, criarAmbiente } = montar(comAmbientes(['Cozinha', ' avulso ']));
    await wrapper.find('[data-testid="movel-avulso"]').trigger('click');
    await flushPromises();
    expect(criarAmbiente).not.toHaveBeenCalled();
    expect(abrirMovel).toHaveBeenCalledWith(102);
  });
});
