import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  ConsultaCnpjErro,
  TEMPO_LIMITE_CNPJ_MS,
  buscarDadosCNPJ,
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

// ---------------------------------------------------------------------------
// Spec 02 (marcenaria): a chamada à BrasilAPI diz POR QUE falhou e não fica
// pendurada sem rede. O `fetch` é simulado: nenhum teste vai à internet.
// ---------------------------------------------------------------------------

/** Resposta falsa do `fetch` com o status dado. */
function respostaCom(status: number, corpo: unknown = {}) {
  return { status, ok: status >= 200 && status < 300, json: async () => corpo } as Response;
}

/** Roda a consulta e devolve o erro lançado (falha o teste se não lançar). */
async function erroDe(promessa: Promise<unknown>): Promise<ConsultaCnpjErro> {
  try {
    await promessa;
  } catch (erro) {
    return erro as ConsultaCnpjErro;
  }
  throw new Error('a consulta deveria ter falhado');
}

describe('buscarDadosCNPJ — motivo da falha e tempo limite', () => {
  afterEach(() => {
    vi.unstubAllGlobals();                                    // devolve o fetch de verdade
    vi.useRealTimers();                                       // e o relógio de verdade
  });

  it('01 — 200 devolve o mesmo mapeamento de converterRespostaBrasilApi', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => respostaCom(200, RESPOSTA_MEI)));
    await expect(buscarDadosCNPJ('58.348.941/0001-60')).resolves.toEqual(converterRespostaBrasilApi(RESPOSTA_MEI));
  });

  it('02 — 404 é NAO_ENCONTRADO', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => respostaCom(404)));
    const erro = await erroDe(buscarDadosCNPJ('00000000000000'));
    expect(erro).toBeInstanceOf(ConsultaCnpjErro);
    expect(erro.motivo).toBe('NAO_ENCONTRADO');
  });

  it.each([429, 503])('03 — %s é INDISPONIVEL (limite de uso ou servidor fora)', async (status) => {
    vi.stubGlobal('fetch', vi.fn(async () => respostaCom(status)));
    expect((await erroDe(buscarDadosCNPJ('00000000000000'))).motivo).toBe('INDISPONIVEL');
  });

  it('04 — sem rede (fetch rejeita) é INDISPONIVEL', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('Failed to fetch'); }));
    expect((await erroDe(buscarDadosCNPJ('00000000000000'))).motivo).toBe('INDISPONIVEL');
  });

  it('05 — sem resposta em 8 s: aborta o fetch e é INDISPONIVEL', async () => {
    vi.useFakeTimers();                                       // controla o relógio
    let sinal: AbortSignal | undefined;
    // fetch que só termina quando é abortado (como uma rede que não responde).
    vi.stubGlobal('fetch', vi.fn((_url: string, opcoes?: RequestInit) => {
      sinal = opcoes?.signal ?? undefined;
      return new Promise((_ok, falha) => sinal?.addEventListener('abort', () => falha(new DOMException('abortado', 'AbortError'))));
    }));
    const consulta = erroDe(buscarDadosCNPJ('00000000000000'));
    await vi.advanceTimersByTimeAsync(TEMPO_LIMITE_CNPJ_MS);  // passam os 8 segundos
    expect((await consulta).motivo).toBe('INDISPONIVEL');
    expect(sinal?.aborted).toBe(true);
  });

  it('06 — a mensagem é a de sempre (o cadastro de empresa mostra só ela)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => respostaCom(503)));
    expect((await erroDe(buscarDadosCNPJ('00000000000000'))).message).toBe('CNPJ não encontrado na Receita Federal');
  });

  it('07 — o caminho da empresa reexporta a mesma função', async () => {
    const daEmpresa = await import('@/modules/enterprise/composables/useConsultaCNPJ');
    expect(daEmpresa.buscarDadosCNPJ).toBe(buscarDadosCNPJ);
  });
});
