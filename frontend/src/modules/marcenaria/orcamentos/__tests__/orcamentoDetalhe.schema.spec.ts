/**
 * Spec 06B §11 — casos 05 e 06, e a prova de que os schemas aceitam o que o
 * backend DE VERDADE devolve: os JSON de `fixtures/` foram gerados pela API
 * da 06A com o cenário B da Spec 05 (Cozinha Gourmet + instalação).
 */
import { describe, expect, it } from 'vitest';

import {
  contagensSchema,
  eventoSchema,
  listaSchema,
  orcamentoDetalheSchema,
  precosDesatualizadosSchema,
  simulacaoSchema,
} from '../schemas/orcamentoDetalhe.schema';
import comCustos from './fixtures/detalhe-com-custos.json';
import semCustos from './fixtures/detalhe-sem-custos.json';
import contagens from './fixtures/contagens.json';
import historico from './fixtures/historico.json';
import lista from './fixtures/lista.json';
import listaSemCustos from './fixtures/lista-sem-custos.json';
import precos from './fixtures/precos-desatualizados.json';
import simulacaoComCustos from './fixtures/simulacao-com-custos.json';
import simulacaoSemCustos from './fixtures/simulacao-sem-custos.json';

describe('orcamentoDetalheSchema', () => {
  it('aceita o detalhe real com custos (cenário B: total R$ 9.238,89)', () => {
    const d = orcamentoDetalheSchema.parse(comCustos);
    expect(d.inclui_custos).toBe(true);
    expect(d.calculo.total_centavos).toBe(923889);
    if (d.inclui_custos) expect(d.calculo.margem_liquida_bp).toBe(3660);
  });

  it('aceita o detalhe real sem custos, e nele não há custo nenhum', () => {
    const d = orcamentoDetalheSchema.parse(semCustos);
    expect(d.inclui_custos).toBe(false);
    // A única "custo" permitida é a própria chave que diz que não há custos.
    expect(JSON.stringify(d).replace('"inclui_custos"', '')).not.toMatch(/custo|margem|markup|perda_bp|rt_/);
  });

  it('05 — sem custos com custo_unit_centavos a mais: aceita e REMOVE a chave', () => {
    const sujo = structuredClone(semCustos) as Record<string, unknown> & { ambientes: { moveis: { calculo: Record<string, unknown> }[] }[] };
    sujo.ambientes[0].moveis[0].calculo.custo_unit_centavos = 222250;
    const d = orcamentoDetalheSchema.parse(sujo);
    expect('custo_unit_centavos' in (d.ambientes[0].moveis[0].calculo ?? {})).toBe(false);
  });

  it('06 — com custos sem margem_liquida_bp: rejeita', () => {
    const incompleto = structuredClone(comCustos) as { calculo: Record<string, unknown> };
    delete incompleto.calculo.margem_liquida_bp;
    expect(orcamentoDetalheSchema.safeParse(incompleto).success).toBe(false);
  });
});

describe('demais respostas da API (JSON reais)', () => {
  it('lista com e sem margem, contagens e histórico', () => {
    expect(listaSchema.parse(lista).items[0].resumo_margem_bp).toBe(3660);
    expect(listaSchema.parse(listaSemCustos).items[0].resumo_margem_bp).toBeUndefined();
    expect(contagensSchema.parse(contagens).RASCUNHO).toBe(1);
    expect(eventoSchema.array().parse(historico)[0].tipo).toBe('ORCAMENTO_CRIADO');
  });

  it('simulação com e sem custos; preços desatualizados', () => {
    expect(simulacaoSchema.parse(simulacaoComCustos).calculo.custo_unit_centavos).toBe(107300);
    expect(simulacaoSchema.parse(simulacaoSemCustos).calculo.custo_unit_centavos).toBeUndefined();
    const p = precosDesatualizadosSchema.parse(precos);
    expect(p.itens).toHaveLength(2);
    expect(p.diferenca_centavos).toBe(p.total_com_precos_novos_centavos - p.total_atual_centavos);
  });
});
