/**
 * Spec 02 (marcenaria) — consulta do CNPJ no cadastro de cliente PJ.
 *
 * A busca de clientes (duplicidade) e a Receita (BrasilAPI) são SIMULADAS:
 * cada teste decide o que elas respondem. O formulário é um objeto simples
 * que guarda os valores, como o vee-validate faria.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { reactive } from 'vue';

import type { DadosCnpj } from '@/shared/services/cnpj.service';

// A busca de clientes vira uma função controlada pelo teste.
vi.mock('@/modules/customers/services/customerGet.service', () => ({
  getAllCustomers: vi.fn(),
}));
// Da Receita, só a chamada é simulada; o erro tipado continua o de verdade.
vi.mock('@/shared/services/cnpj.service', async (importOriginal) => {
  const real = await importOriginal<typeof import('@/shared/services/cnpj.service')>();
  return { ...real, buscarDadosCNPJ: vi.fn() };
});

// Importa DEPOIS dos mocks: estes já são as versões simuladas.
const { getAllCustomers } = await import('@/modules/customers/services/customerGet.service');
const { buscarDadosCNPJ, ConsultaCnpjErro } = await import('@/shared/services/cnpj.service');
const { criarConsultaReceita } = await import('../consultaReceita');
const { DEFAULT_PJ_VALUES } = await import('../../constants/modal.constant');

const buscarClientes = vi.mocked(getAllCustomers);
const buscarReceita = vi.mocked(buscarDadosCNPJ);

/** CNPJ válido de exemplo (dígitos verificadores corretos). */
const CNPJ = '11222333000181';

/** O que a Receita devolve neste cenário (já convertido pelo serviço). */
const DADOS: DadosCnpj = {
  razao_social: 'MARCENARIA EXEMPLO LTDA',
  nome_fantasia: '',
  cnae_principal: '3101-2/00',
  cnaes_secundarios: '',
  natureza_juridica: 'LTDA',
  data_abertura: '2015-03-02',
  email: 'contato@exemplo.com',
  telefone: '1133334444',
  logradouro: 'AVENIDA PAULISTA',
  numero: '1000',
  complemento: 'SALA 1',
  bairro: 'BELA VISTA',
  cidade: 'SAO PAULO',
  estado: 'SP',
  cep: '01310100',
  codigo_ibge: '3550308',
  regime_tributario: 'Simples Nacional',
};

/** Monta a consulta com um formulário novo e toasts espiões. */
function montar({ idEmEdicao }: { idEmEdicao?: number } = {}) {
  // Formulário PJ em branco, com o CNPJ já digitado.
  const values = reactive({
    ...DEFAULT_PJ_VALUES,
    enderecos: DEFAULT_PJ_VALUES.enderecos.map((e) => ({ ...e })),
    cnpj: CNPJ,
  });
  const setValues = vi.fn((novos: Record<string, unknown>) => Object.assign(values, novos));
  const toast = { success: vi.fn(), error: vi.fn() };
  const consulta = criarConsultaReceita({
    pjForm: { values, setValues } as never,     // só `values` e `setValues` são usados
    idEmEdicao: () => idEmEdicao,
    toast,
  });
  return { consulta, values, setValues, toast };
}

/** Página de clientes devolvida pela busca de duplicidade. */
function paginaCom(...clientes: Array<Record<string, unknown>>) {
  return { items: clientes, total: clientes.length, page: 1, limit: 5, total_pages: 1 } as never;
}

beforeEach(() => {
  buscarClientes.mockReset();
  buscarReceita.mockReset();
  buscarClientes.mockResolvedValue(paginaCom());   // padrão: nenhum cliente com o CNPJ
  buscarReceita.mockResolvedValue(DADOS);          // padrão: a Receita responde
});

describe('duplicidade (antes de consultar a Receita)', () => {
  it('08 — outro cliente com o mesmo CNPJ: aviso com o nome, sem Receita e sem preencher', async () => {
    buscarClientes.mockResolvedValue(paginaCom({ id: 7, tipo: 'PJ', cnpj: CNPJ, razao_social: 'MOVEIS SILVA LTDA' }));
    const { consulta, setValues } = montar();

    await consulta.consultarReceita(CNPJ);

    expect(consulta.avisoCnpj.value).toEqual({ tipo: 'duplicado', nomeCliente: 'MOVEIS SILVA LTDA' });
    expect(buscarReceita).not.toHaveBeenCalled();
    expect(setValues).not.toHaveBeenCalled();
  });

  it('09 — o próprio cliente em edição não é duplicado', async () => {
    buscarClientes.mockResolvedValue(paginaCom({ id: 7, tipo: 'PJ', cnpj: CNPJ, razao_social: 'ELE MESMO' }));
    const { consulta } = montar({ idEmEdicao: 7 });

    await consulta.consultarReceita(CNPJ);

    expect(consulta.avisoCnpj.value).toBeNull();
    expect(buscarReceita).toHaveBeenCalledOnce();
  });

  it('10 — CNPJ que só CONTÉM o termo não é duplicado', async () => {
    buscarClientes.mockResolvedValue(paginaCom({ id: 8, tipo: 'PJ', cnpj: `99${CNPJ}`, razao_social: 'OUTRA' }));
    const { consulta } = montar();

    await consulta.consultarReceita(CNPJ);

    expect(consulta.avisoCnpj.value).toBeNull();
    expect(buscarReceita).toHaveBeenCalledOnce();
  });

  it('11 — busca de duplicidade falhou: segue para a Receita (o 409 continua no salvar)', async () => {
    buscarClientes.mockRejectedValue(new Error('sem rede'));
    const { consulta } = montar();

    await consulta.consultarReceita(CNPJ);

    expect(buscarReceita).toHaveBeenCalledOnce();
  });
});

describe('falhas da Receita', () => {
  it('12 — NAO_ENCONTRADO: toast de sempre e formulário intacto', async () => {
    buscarReceita.mockRejectedValue(new ConsultaCnpjErro('NAO_ENCONTRADO'));
    const { consulta, setValues, toast } = montar();

    await consulta.consultarReceita(CNPJ);

    expect(toast.error).toHaveBeenCalledWith('CNPJ não encontrado na Receita Federal.');
    expect(setValues).not.toHaveBeenCalled();
    expect(consulta.isConsultingCNPJ.value).toBe(false);
  });

  it('13 — INDISPONIVEL: diz que não deu para consultar (não que o CNPJ não existe)', async () => {
    buscarReceita.mockRejectedValue(new ConsultaCnpjErro('INDISPONIVEL'));
    const { consulta, setValues, toast } = montar();

    await consulta.consultarReceita(CNPJ);

    expect(toast.error).toHaveBeenCalledWith(
      'Não foi possível consultar a Receita agora.',
      'Preencha manualmente ou tente de novo.',
    );
    expect(setValues).not.toHaveBeenCalled();
  });

  it('14 — CNPJ trocado durante a consulta: resposta descartada, nada preenchido, nenhum toast', async () => {
    let responder: (dados: DadosCnpj) => void = () => {};
    buscarReceita.mockReturnValue(new Promise((ok) => { responder = ok; }));   // Receita "demorando"
    const { consulta, values, setValues, toast } = montar();

    const emAndamento = consulta.consultarReceita(CNPJ);
    await vi.waitFor(() => expect(buscarReceita).toHaveBeenCalled());       // chegou na Receita
    values.cnpj = '99888777000166';                                          // o usuário trocou
    responder(DADOS);                                                        // a resposta velha chega
    await emAndamento;

    expect(setValues).not.toHaveBeenCalled();
    expect(toast.success).not.toHaveBeenCalled();
    expect(toast.error).not.toHaveBeenCalled();
  });
});

describe('sucesso', () => {
  it('15 — preenche exatamente como o código de antes (retrato)', async () => {
    const { consulta, values, setValues, toast } = montar();

    await consulta.consultarReceita(CNPJ);

    // Gravado sem validar o formulário (segundo argumento false), como antes.
    expect(setValues).toHaveBeenCalledWith(expect.any(Object), false);
    expect({ ...values }).toEqual({
      ...DEFAULT_PJ_VALUES,
      cnpj: CNPJ,
      razao_social: 'MARCENARIA EXEMPLO LTDA',
      nome_fantasia: 'MARCENARIA EXEMPLO LTDA',    // sem fantasia na Receita: usa a razão social
      regime_tributario: 'Simples Nacional',
      email: 'contato@exemplo.com',                // contato vazio: vem da Receita
      telefone: '(11) 3333-4444',
      enderecos: [{
        cep: '01310-100',
        logradouro: 'AVENIDA PAULISTA',
        numero: '1000',
        complemento: 'SALA 1',
        bairro: 'BELA VISTA',
        cidade: 'SAO PAULO',
        estado: 'SP',
      }],
    });
    expect(toast.success).toHaveBeenCalledWith(
      'Dados da Receita Federal preenchidos. Confira e informe a Inscrição Estadual, se o cliente tiver.',
    );
    expect(buscarClientes).toHaveBeenCalledWith({ search: CNPJ, limit: 5 });
  });

  it('contato já preenchido não é sobrescrito (regra de antes)', async () => {
    const { consulta, values } = montar();
    values.email = 'meu@cliente.com';
    values.telefone = '(11) 99999-0000';

    await consulta.consultarReceita(CNPJ);

    expect(values.email).toBe('meu@cliente.com');
    expect(values.telefone).toBe('(11) 99999-0000');
  });
});
