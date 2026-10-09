/**
 * Spec 06B §11 — caso 04: o PATCH leva SÓ o que mudou (D8).
 */
import { describe, expect, it } from 'vitest';

import { cabecalhoVazio } from '../composables/useSalvamentoAutomatico';
import { cabecalhoDoDetalhe, diferencaCabecalho } from '../utils/diferencaCabecalho';
import { orcamentoDetalheSchema } from '../schemas/orcamentoDetalhe.schema';
import comCustos from './fixtures/detalhe-com-custos.json';
import semCustos from './fixtures/detalhe-sem-custos.json';

describe('diferencaCabecalho', () => {
  it('04 — só o desconto mudou: só ele vai', () => {
    const salvo = cabecalhoVazio();
    const atual = { ...salvo, desconto: { modo: 'VALOR' as const, valor: 10000 } };
    expect(diferencaCabecalho(salvo, atual)).toEqual({ desconto: { modo: 'VALOR', valor: 10000 } });
  });

  it('nada mudou: corpo vazio', () => {
    expect(diferencaCabecalho(cabecalhoVazio(), cabecalhoVazio())).toEqual({});
  });

  it('objetos saem COPIADOS (editar depois não muda o que foi enviado)', () => {
    const salvo = cabecalhoVazio();
    const atual = { ...salvo, sinal: { modo: 'PERCENTUAL' as const, valor: 4000 } };
    const mudancas = diferencaCabecalho(salvo, atual);
    atual.sinal.valor = 5000;                             // o usuário continua digitando
    expect(mudancas.sinal).toEqual({ modo: 'PERCENTUAL', valor: 4000 });
  });

  it('cabeçalho com custos tem os parâmetros; sem custos, nem as chaves', () => {
    const dono = cabecalhoDoDetalhe(orcamentoDetalheSchema.parse(comCustos));
    expect(dono.markup_bp).toBe(9000);
    expect(dono.instalacao_custo_centavos).toBe(75000);
    const vendedor = cabecalhoDoDetalhe(orcamentoDetalheSchema.parse(semCustos));
    expect('markup_bp' in vendedor).toBe(false);
    expect('instalacao_custo_centavos' in vendedor).toBe(false);
  });
});
