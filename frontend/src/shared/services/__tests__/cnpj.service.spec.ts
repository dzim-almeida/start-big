import { describe, expect, it } from 'vitest';
import {
  converterRespostaBrasilApi,
  mapNaturezaJuridica,
  mapRegimeTributario,
} from '../cnpj.service';

/** Campos que a BrasilAPI devolveu para o primeiro cliente em produção (MEI). */
const RESPOSTA_MEI = {
  razao_social: '58.348.941 CELSO PEREZ RIBEIRA',
  nome_fantasia: '',
  natureza_juridica: 'Empresário (Individual)',
  porte: 'MICRO EMPRESA',
  opcao_pelo_simples: true,
  opcao_pelo_mei: true,
  descricao_tipo_logradouro: 'RUA',
  logradouro: 'JOSE GOMES DE GOUVEIA',
  numero: '10',
  bairro: 'VILA NOVA GALVAO',
  municipio: 'SAO PAULO',
  uf: 'SP',
  cep: '02280120',
  codigo_municipio_ibge: 3550308,
  cnae_fiscal: 1412601,
};

describe('converterRespostaBrasilApi', () => {
  it('o MEI sai com regime MEI e natureza MEI (o caso da Rejeição 481)', () => {
    const dados = converterRespostaBrasilApi(RESPOSTA_MEI);
    expect(dados.regime_tributario).toBe('MEI');
    // Sem o opcao_pelo_mei, "Empresário (Individual)" virava EI.
    expect(dados.natureza_juridica).toBe('MEI');
  });

  it('lê o código IBGE pelo nome que a BrasilAPI usa', () => {
    expect(converterRespostaBrasilApi(RESPOSTA_MEI).codigo_ibge).toBe('3550308');
  });

  it('monta o logradouro com o tipo e formata o CNAE', () => {
    const dados = converterRespostaBrasilApi(RESPOSTA_MEI);
    expect(dados.logradouro).toBe('RUA JOSE GOMES DE GOUVEIA');
    expect(dados.cnae_principal).toBe('1412-6/01');
  });

  it('empresa do Simples que não é MEI sai como Simples Nacional', () => {
    const dados = converterRespostaBrasilApi({ ...RESPOSTA_MEI, opcao_pelo_mei: false, natureza_juridica: 'Sociedade Empresária Limitada' });
    expect(dados.regime_tributario).toBe('Simples Nacional');
    expect(dados.natureza_juridica).toBe('LTDA');
  });

  it('fora do Simples, o regime fica para o contador (vazio)', () => {
    const dados = converterRespostaBrasilApi({ ...RESPOSTA_MEI, opcao_pelo_mei: false, opcao_pelo_simples: false });
    expect(dados.regime_tributario).toBe('');
  });
});

describe('mapRegimeTributario', () => {
  it.each([
    [true, true, 'MEI'],
    [true, null, 'MEI'],
    [false, true, 'Simples Nacional'],
    [null, true, 'Simples Nacional'],
    [false, false, ''],
    [null, null, ''],
    [undefined, undefined, ''],
  ] as const)('mei=%s simples=%s → "%s"', (mei, simples, esperado) => {
    expect(mapRegimeTributario(mei, simples)).toBe(esperado);
  });
});

describe('mapNaturezaJuridica', () => {
  it('sem SIMEI, empresário individual continua EI', () => {
    expect(mapNaturezaJuridica('Empresário (Individual)', 'MICRO EMPRESA', false)).toBe('EI');
  });
});
