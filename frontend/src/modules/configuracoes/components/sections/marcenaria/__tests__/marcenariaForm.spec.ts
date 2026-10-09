/**
 * Spec 04B (marcenaria) — conversões e regras do formulário de
 * Configurações › Marcenaria (casos 01 a 06, mais as regras das listas).
 *
 * A tela mostra % e R$; a API guarda basis points e centavos (PR4). Um
 * centavo perdido aqui vira preço errado em todo orçamento novo.
 */
import { describe, expect, it } from 'vitest';

import { configuracaoMarcenariaSchema } from '../../../../schemas/configuracaoMarcenaria.schema';
import { errosDoFormulario, errosDosItens, paraApi, paraTela, type FormMarcenaria } from '../marcenariaForm';

/** Resposta completa da API com os padrões da Spec 04A. */
const COMPLETA = {
  inclui_custos: true as const,
  markup_padrao_bp: 9000,
  perda_padrao_bp: 1000,
  custo_hora_centavos: 0,
  rt_padrao_bp: 0,
  rt_modo: 'MARGEM' as const,
  validade_dias: 15,
  prazo_entrega_dias: 30,
  etapas_producao: ['Corte', 'Borda'],
  checklist_vistoria: ['Limpeza final do ambiente'],
};

/** A mesma resposta para quem NÃO vê custo (as chaves de custo nem vêm). */
const PUBLICA = {
  inclui_custos: false as const,
  validade_dias: 15,
  prazo_entrega_dias: 30,
  etapas_producao: ['Corte', 'Borda'],
  checklist_vistoria: ['Limpeza final do ambiente'],
};

const CAMPOS_DE_CUSTO_API = ['markup_padrao_bp', 'perda_padrao_bp', 'custo_hora_centavos', 'rt_padrao_bp', 'rt_modo'];

describe('conversões', () => {
  it('01 — paraTela: 9000 bp → 90%, 1000 bp → 10%, 0 centavos → R$ 0', () => {
    const form = paraTela(COMPLETA);
    expect(form.markup_percentual).toBe(90);
    expect(form.perda_percentual).toBe(10);
    expect(form.custo_hora_reais).toBe(0);
  });

  it('02 — paraApi: 12,35% → 1235 bp e R$ 45,50 → 4550 centavos (e volta igual)', () => {
    const form: FormMarcenaria = { ...paraTela(COMPLETA), markup_percentual: 12.35, custo_hora_reais: 45.5 };
    const corpo = paraApi(form);
    expect(corpo.markup_padrao_bp).toBe(1235);
    expect(corpo.custo_hora_centavos).toBe(4550);
    // Ida e volta sem perder centavo.
    expect(paraTela({ ...COMPLETA, markup_padrao_bp: 1235 }).markup_percentual).toBe(12.35);
  });

  it('03 — meio basis point arredonda (não trunca)', () => {
    const corpo = paraApi({ ...paraTela(COMPLETA), markup_percentual: 0.005 });
    expect(corpo.markup_padrao_bp).toBe(1);
  });

  it('04 — paraTela sem custos: nenhum campo de custo no formulário', () => {
    const form = paraTela(PUBLICA);
    expect(form.markup_percentual).toBeUndefined();
    expect(form.perda_percentual).toBeUndefined();
    expect(form.custo_hora_reais).toBeUndefined();
    expect(form.rt_percentual).toBeUndefined();
    expect(form.rt_modo).toBeUndefined();
  });

  it('05 — paraApi de um formulário sem custos: corpo sem nenhuma chave de custo', () => {
    const corpo = paraApi(paraTela(PUBLICA));
    for (const campo of CAMPOS_DE_CUSTO_API) expect(corpo).not.toHaveProperty(campo);
  });

  it('paraApi tira os espaços das pontas dos itens (como o backend)', () => {
    const corpo = paraApi({ ...paraTela(PUBLICA), etapas_producao: ['  Corte  ', 'Borda'] });
    expect(corpo.etapas_producao).toEqual(['Corte', 'Borda']);
  });

  it('paraTela devolve cópias das listas (editar não mexe no cache da query)', () => {
    const form = paraTela(COMPLETA);
    form.etapas_producao.push('Nova');
    expect(COMPLETA.etapas_producao).toEqual(['Corte', 'Borda']);
  });
});

describe('schema da resposta (06)', () => {
  it('aceita os dois formatos', () => {
    expect(configuracaoMarcenariaSchema.safeParse(COMPLETA).success).toBe(true);
    expect(configuracaoMarcenariaSchema.safeParse(PUBLICA).success).toBe(true);
  });

  it('recusa "inclui_custos: true" sem o markup', () => {
    const { markup_padrao_bp: _semMarkup, ...incompleta } = COMPLETA;
    expect(configuracaoMarcenariaSchema.safeParse(incompleta).success).toBe(false);
  });
});

describe('regras das listas e dos limites (iguais às do backend)', () => {
  it('erro por item: vazio, longo demais e repetido (sem diferenciar maiúsculas)', () => {
    expect(errosDosItens(['Corte', ' ', 'x'.repeat(61), 'corte'], 60)).toEqual([
      '',
      'Preencha ou remova este item.',
      'Até 60 caracteres.',
      'Item repetido.',
    ]);
  });

  it('formulário com limites estourados recebe as mensagens do backend', () => {
    const erros = errosDoFormulario({ ...paraTela(COMPLETA), markup_percentual: 1000.01, validade_dias: 0, etapas_producao: [] });
    expect(erros.markup_percentual).toBe('O markup deve ficar entre 0% e 1000%.');
    expect(erros.validade_dias).toBe('A validade deve ficar entre 1 e 365 dias.');
    expect(erros.etapas_producao).toBe('Etapas de produção: informe de 1 a 20 itens.');
  });

  it('formulário certo não tem erro', () => {
    expect(errosDoFormulario(paraTela(COMPLETA))).toEqual({});
  });
});
