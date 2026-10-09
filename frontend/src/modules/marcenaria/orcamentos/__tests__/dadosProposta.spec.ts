/**
 * Spec 06B §11 — caso 28 (e a base dos casos da Spec 07): o que o CLIENTE
 * pode ver. A saída é varrida inteira, recursivamente: nenhuma chave de custo,
 * margem, insumo, parâmetro ou preço por móvel, nem com o detalhe COM custos.
 */
import { describe, expect, it } from 'vitest';

import { orcamentoDetalheSchema, type OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import { formatarMedidasProposta, montarDadosProposta } from '../utils/dadosProposta';
import comCustos from './fixtures/detalhe-com-custos.json';

const HOJE = new Date(2026, 9, 9);
const detalhe = (): OrcamentoDetalhe => orcamentoDetalheSchema.parse(structuredClone(comCustos));

/** Todas as chaves e todos os números de um objeto, em qualquer profundidade. */
function varrer(valor: unknown, chaves: string[] = [], numeros: number[] = []) {
  if (Array.isArray(valor)) valor.forEach((item) => varrer(item, chaves, numeros));
  else if (valor && typeof valor === 'object') {
    for (const [chave, item] of Object.entries(valor)) {
      chaves.push(chave);
      varrer(item, chaves, numeros);
    }
  } else if (typeof valor === 'number') numeros.push(valor);
  return { chaves, numeros };
}

describe('montarDadosProposta', () => {
  it('28 — com custos na entrada, nada de custo na saída (chaves e valores)', () => {
    const entrada = detalhe();
    const { chaves, numeros } = varrer(montarDadosProposta(entrada, HOJE));
    for (const chave of chaves) {
      expect(chave).not.toMatch(/custo|margem|insumo|markup|perda|hora|rt|preco|parametro/i);
    }
    // Nenhum preço de móvel nem custo aparece como número.
    const proibidos = entrada.ambientes.flatMap((a) => a.moveis.flatMap((m) => [
      m.calculo?.preco_unit_centavos, m.calculo?.preco_total_centavos,
      ...(m.calculo && 'custo_unit_centavos' in m.calculo ? [m.calculo.custo_unit_centavos, m.calculo.material_centavos] : []),
    ]));
    if (entrada.inclui_custos) proibidos.push(entrada.calculo.custo_total_centavos, entrada.calculo.margem_liquida_centavos);
    for (const numero of proibidos) expect(numeros).not.toContain(numero);
  });

  it('cenário B: ambientes + instalação = subtotal (Spec 07 D10)', () => {
    const dados = montarDadosProposta(detalhe(), HOJE);
    const somaAmbientes = dados.ambientes.reduce((soma, a) => soma + a.totalCentavos, 0);
    expect(somaAmbientes + (dados.instalacaoCentavos ?? 0)).toBe(dados.subtotalCentavos);
    expect(dados.totalCentavos).toBe(923889);
    expect(dados.desconto).toEqual({ centavos: 48626, percentualTexto: '5%' });
    expect(dados.sinal).toEqual({ centavos: 369556, percentualTexto: '40%' });
  });

  it('rascunho: faixa de prévia e validade "a partir do envio"', () => {
    const dados = montarDadosProposta(detalhe(), HOJE);
    expect(dados.faixa).toBe('PRÉVIA — proposta ainda não enviada');
    expect(dados.validadeTexto).toBe('15 dias a partir do envio');
    expect(dados.emitidaEm).toBe('09/10/2026');
  });

  it('medidas do jeito da proposta (Spec 07 D14)', () => {
    expect(formatarMedidasProposta(700, 2200, 600)).toBe('L 700 × A 2200 × P 600 mm');
    expect(formatarMedidasProposta(700, null, 600)).toBe('L 700 × P 600 mm');
    expect(formatarMedidasProposta(null, null, null)).toBe('');
  });
});
