/**
 * Spec 03B (marcenaria) — "posso criar OS à mão?" e "este tipo pode ser trocado?".
 *
 * O contrato do segmento e o segmento da empresa logada são SIMULADOS: os
 * testes controlam se o contrato ainda carrega e quais tipos ele trouxe.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

import type { SegmentDefinitionResponse, SegmentWorkType } from '../segmentDefinition.type';

const carregando = ref(true);                                     // contrato ainda carregando?
const contrato = ref<SegmentDefinitionResponse | undefined>();    // resposta do backend
const segmentoAtual = ref<string | null>(null);                   // segmento da empresa logada

vi.mock('../useOSFieldDefinition.queries', () => ({
  useOSFieldDefinition: () => ({ data: contrato, isPending: carregando }),
}));
vi.mock('@/shared/composables/useSegmento', () => ({
  useSegmento: () => ({ segmento: segmentoAtual }),
}));

const { useTiposDeTrabalho } = await import('../useTiposDeTrabalho');

/** Contrato carregado com os tipos dados (só os campos que importam aqui). */
function contratoComTipos(tipos: SegmentWorkType[]): SegmentDefinitionResponse {
  return { segmento: 'x', tem_definicao: true, definicao: { tipos } } as unknown as SegmentDefinitionResponse;
}

const PLANEJADOS: SegmentWorkType = {
  id: 'planejados', label: 'Móveis planejados', criacao_manual: false,
  campos: [{ nome: 'nome_projeto', label: 'Nome do projeto', tipo: 'texto', escopo: 'objeto', grupo: 'Dados do Projeto' } as never],
};
const CAMISA: SegmentWorkType = {
  id: 'camisa', label: 'Camisa', criacao_manual: true,
  campos: [
    { nome: 'cores', label: 'Cores', tipo: 'inteiro', escopo: 'os', grupo: 'Arte' } as never,
    { nome: 'local', label: 'Local', tipo: 'texto', escopo: 'os', grupo: 'Arte' } as never,
    { nome: 'obs', label: 'Obs', tipo: 'texto', escopo: 'os' } as never,
  ],
};
const SACOLA: SegmentWorkType = { id: 'sacola_plastica', label: 'Sacola plástica', criacao_manual: true, campos: [] };

beforeEach(() => {
  carregando.value = false;
  contrato.value = undefined;
  segmentoAtual.value = null;
});

describe('podeCriarOSManual', () => {
  it('01 — marcenaria carregada (Planejados não se cria à mão): false', () => {
    contrato.value = contratoComTipos([PLANEJADOS]);
    expect(useTiposDeTrabalho().podeCriarOSManual.value).toBe(false);
  });

  it('02 — serigrafia carregada (os dois tipos criáveis): true', () => {
    contrato.value = contratoComTipos([CAMISA, SACOLA]);
    expect(useTiposDeTrabalho().podeCriarOSManual.value).toBe(true);
  });

  it('03 — informática (sem tipos): true', () => {
    contrato.value = contratoComTipos([]);
    expect(useTiposDeTrabalho().podeCriarOSManual.value).toBe(true);
  });

  it('04 — contrato antigo, sem `criacao_manual`: true (D1)', () => {
    const { criacao_manual: _semMarcacao, ...antigo } = PLANEJADOS;
    contrato.value = contratoComTipos([antigo]);
    expect(useTiposDeTrabalho().podeCriarOSManual.value).toBe(true);
  });

  it('05 — carregando, marcenaria: false (fallback, o botão não pisca)', () => {
    carregando.value = true;
    segmentoAtual.value = 'marcenaria';
    expect(useTiposDeTrabalho().podeCriarOSManual.value).toBe(false);
  });

  it('06 — carregando, serigrafia: true', () => {
    carregando.value = true;
    segmentoAtual.value = 'serigrafia';
    expect(useTiposDeTrabalho().podeCriarOSManual.value).toBe(true);
  });
});

describe('tipoPodeSerTrocado (07)', () => {
  it.each([
    ['planejados', false],    // nasce do orçamento: trava
    ['camisa', true],         // criável à mão: troca como sempre
    [undefined, true],        // OS sem tipo gravado
    ['inexistente', true],    // tipo que saiu do registry (ex.: Reforma em banco de dev)
  ] as const)('%s -> %s', (id, esperado) => {
    contrato.value = contratoComTipos([PLANEJADOS, CAMISA]);
    expect(useTiposDeTrabalho().tipoPodeSerTrocado(id)).toBe(esperado);
  });
});

describe('o que já existia continua igual (08)', () => {
  it('opcoes, tipoPadrao e gruposDoTipo', () => {
    contrato.value = contratoComTipos([CAMISA, SACOLA]);
    const { opcoes, tipoPadrao, gruposDoTipo } = useTiposDeTrabalho();
    expect(opcoes.value).toEqual([
      { value: 'camisa', label: 'Camisa' },
      { value: 'sacola_plastica', label: 'Sacola plástica' },
    ]);
    expect(tipoPadrao.value).toBe('camisa');                 // o primeiro declarado
    // Campos seguidos do mesmo grupo ficam juntos; campo sem grupo vira bloco sem título.
    expect(gruposDoTipo('camisa').map((g) => [g.titulo, g.campos.length])).toEqual([['Arte', 2], [null, 1]]);
  });
});
