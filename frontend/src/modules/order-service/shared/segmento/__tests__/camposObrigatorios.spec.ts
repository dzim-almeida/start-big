/**
 * Spec 01B do lava-rápido — exigência na tela dos campos obrigatórios do tipo.
 *
 * O contrato do segmento e o segmento logado são SIMULADOS: os testes decidem
 * se o identificador é `gerado_se_vazio` (lava) ou não (serigrafia etc.).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

import type { SegmentDefinitionResponse, SegmentField } from '../segmentDefinition.type';

const contrato = ref<SegmentDefinitionResponse | undefined>();
vi.mock('../useOSFieldDefinition.queries', () => ({
  useOSFieldDefinition: () => ({ data: contrato, isPending: ref(false) }),
}));
vi.mock('@/shared/composables/useSegmento', () => ({
  useSegmento: () => ({ segmento: ref('qualquer') }),
}));

// Importa DEPOIS dos mocks: o composable usa as versões simuladas.
const { camposObrigatoriosVazios, valorVazio, useCamposObrigatoriosDoTipo } = await import(
  '../camposObrigatorios'
);

/** Campo mínimo do contrato. */
function campo(nome: string, label: string, extra: Partial<SegmentField> = {}): SegmentField {
  return { nome, label, tipo: 'texto', obrigatorio: true, escopo: 'objeto', ...extra };
}

// Como o lava-rápido declara (Spec 01A): placa na coluna, porte no JSON.
const PLACA = campo('placa', 'Placa', { origem: 'coluna', coluna: 'numero_serie' });
const PORTE = campo('porte', 'Porte', { tipo: 'opcao', opcoes: ['Hatch', 'SUV'] });
const PERTENCES = campo('pertences', 'Pertences', { obrigatorio: false, escopo: 'os' });

const TIPOS = [
  { id: 'carro', label: 'Carro', campos: [PLACA, PORTE, PERTENCES] },
  { id: 'outros', label: 'Outros', campos: [{ ...PLACA, obrigatorio: false }, PORTE] },
];

function contratoCom(geradoSeVazio: boolean): SegmentDefinitionResponse {
  return {
    segmento: 'qualquer',
    tem_definicao: true,
    definicao: {
      identificador: { nome: 'placa', label: 'Placa', regex: null, gerado_se_vazio: geradoSeVazio },
      tipos: TIPOS,
    },
  } as unknown as SegmentDefinitionResponse;
}

beforeEach(() => {
  contrato.value = contratoCom(true);
});

describe('valorVazio', () => {
  it('C1 — branco, nulo e lista vazia são vazios; 0 e false são respostas', () => {
    for (const v of ['', '   ', null, undefined, []]) expect(valorVazio(v)).toBe(true);
    for (const v of [0, false, 'ABC1D23', ['x']]) expect(valorVazio(v)).toBe(false);
  });
});

describe('camposObrigatoriosVazios (função pura)', () => {
  it('C2 — carro sem placa e sem porte: os dois, na ordem declarada', () => {
    const faltando = camposObrigatoriosVazios(TIPOS[0].campos, {
      coluna: { numero_serie: '' }, objeto: {}, os: {},
    });
    expect(faltando).toEqual(['Placa', 'Porte']);
  });

  it('C2 — lê a placa da COLUNA (numero_serie), não do nome do campo', () => {
    const faltando = camposObrigatoriosVazios(TIPOS[0].campos, {
      coluna: { numero_serie: 'ABC1D23' }, objeto: { porte: 'SUV' }, os: {},
    });
    expect(faltando).toEqual([]);
  });
});

describe('useCamposObrigatoriosDoTipo', () => {
  it('C2 — tipo ausente na OS = tipo padrão (o primeiro, Carro)', () => {
    const { faltando } = useCamposObrigatoriosDoTipo();
    expect(faltando({ numero_serie: '' }, {}, {})).toEqual(['Placa', 'Porte']);
  });

  it('C3 — Outros sem placa: só o porte é exigido', () => {
    const { faltando } = useCamposObrigatoriosDoTipo();
    expect(faltando({ numero_serie: '' }, {}, { tipo_trabalho: 'outros' })).toEqual(['Porte']);
  });

  it('C4 — segmento sem gerado_se_vazio: nunca exige nada (PR1)', () => {
    contrato.value = contratoCom(false);
    const { faltando } = useCamposObrigatoriosDoTipo();
    expect(faltando({ numero_serie: '' }, {}, {})).toEqual([]);
  });

  it('C4 — contrato ainda não chegou: não trava o salvar', () => {
    contrato.value = undefined;
    const { faltando } = useCamposObrigatoriosDoTipo();
    expect(faltando({}, {}, {})).toEqual([]);
  });
});
