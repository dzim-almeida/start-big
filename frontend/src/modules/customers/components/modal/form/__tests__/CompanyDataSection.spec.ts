/**
 * Spec 02 (marcenaria) — tela de dados da empresa no cadastro de cliente PJ.
 *
 * O componente é montado com um CONTEXTO FALSO no lugar do formulário de
 * verdade: o teste controla o CNPJ digitado, o modo (novo × edição) e o aviso,
 * e espia se a consulta foi chamada.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { describe, expect, it, vi } from 'vitest';
import { nextTick, ref } from 'vue';

import { CUSTOMER_FORM_KEY } from '@/modules/customers/composables/modal/context/useCustomerForm.context';
import type { AvisoCnpj } from '@/modules/customers/composables/modal/context/consultaReceita';
import CompanyDataSection from '../CompanyDataSection.vue';

const CNPJ_VALIDO = '11.222.333/0001-81';       // dígitos verificadores corretos
const CNPJ_DV_ERRADO = '11.222.333/0001-80';    // mesmo número com o último dígito trocado

/** Monta o componente com um contexto falso; devolve o contexto para o teste mexer. */
function montar({ criando = true, cnpjInicial = '' } = {}) {
  const avisoCnpj = ref<AvisoCnpj>(null);
  const contexto = {
    razao_social: ref(''), nome_fantasia: ref(''), cnpj: ref(cnpjInicial),
    ie: ref(''), im: ref(''), regime_tributario: ref(''), responsavel: ref(''),
    errors: ref({}), submitCount: ref(0),
    isConsultingCNPJ: ref(false),
    consultarReceita: vi.fn(async () => {}),                 // espião: a consulta foi pedida?
    avisoCnpj,
    limparAvisoCnpj: vi.fn(() => { avisoCnpj.value = null; }),
    isCreateMode: ref(criando),
  };
  const wrapper = mount(CompanyDataSection, {
    global: {
      plugins: [createPinia()],                              // a tela lê a configuração de clientes
      provide: { [CUSTOMER_FORM_KEY as symbol]: contexto },
    },
  });
  return { wrapper, contexto };
}

/** O botão "Buscar dados na Receita". */
const botaoConsultar = (wrapper: ReturnType<typeof montar>['wrapper']) =>
  wrapper.findAll('button').find((b) => b.text().includes('Buscar dados na Receita'));

describe('consulta automática e botão', () => {
  it('16 — cadastro novo, dígito verificador errado: não consulta e o botão fica desabilitado', async () => {
    const { wrapper, contexto } = montar();
    contexto.cnpj.value = CNPJ_DV_ERRADO;
    await nextTick();

    expect(contexto.consultarReceita).not.toHaveBeenCalled();
    expect(botaoConsultar(wrapper)?.attributes('disabled')).toBeDefined();
  });

  it('17 — cadastro novo, CNPJ válido: consulta uma vez, com os dígitos', async () => {
    const { wrapper, contexto } = montar();
    contexto.cnpj.value = CNPJ_VALIDO;
    await nextTick();

    expect(contexto.consultarReceita).toHaveBeenCalledTimes(1);
    expect(contexto.consultarReceita).toHaveBeenCalledWith('11222333000181');
    expect(botaoConsultar(wrapper)?.attributes('disabled')).toBeUndefined();
  });

  it('18 — edição com CNPJ salvo: nenhuma consulta automática (regra de sempre)', async () => {
    const { contexto } = montar({ criando: false, cnpjInicial: CNPJ_VALIDO });
    await flushPromises();

    expect(contexto.consultarReceita).not.toHaveBeenCalled();
  });
});

describe('aviso de duplicidade', () => {
  it('19 — aparece com o nome e some quando um dígito muda', async () => {
    const { wrapper, contexto } = montar({ criando: false, cnpjInicial: CNPJ_VALIDO });
    contexto.avisoCnpj.value = { tipo: 'duplicado', nomeCliente: 'MOVEIS SILVA LTDA' };
    await nextTick();
    expect(wrapper.text()).toContain('Já existe um cliente com este CNPJ');
    expect(wrapper.text()).toContain('MOVEIS SILVA LTDA');

    contexto.cnpj.value = '11.222.333/0001-8';                // apagou um dígito
    await nextTick();
    await nextTick();                                          // o aviso some no ciclo seguinte

    expect(contexto.limparAvisoCnpj).toHaveBeenCalled();
    expect(wrapper.text()).not.toContain('Já existe um cliente com este CNPJ');
  });
});
