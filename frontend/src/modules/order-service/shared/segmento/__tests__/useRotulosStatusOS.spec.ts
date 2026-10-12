/**
 * Spec 01B (marcenaria) — composable `useRotulosStatusOS`.
 *
 * O contrato do segmento (GET /ordens-servico/definicao-campos) e o segmento
 * da empresa logada são SIMULADOS aqui: os testes controlam se o contrato
 * ainda está carregando e o que ele trouxe.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

import { OS_STATUS_FILTER_CONFIG, OS_STATUS_OPTIONS } from '../../../ordens/constants/ordemServico.constants';
import type { SegmentDefinitionResponse } from '../segmentDefinition.type';

// Estado controlado pelos testes (o que as funções simuladas devolvem).
const carregando = ref(true);                                     // contrato ainda carregando?
const contrato = ref<SegmentDefinitionResponse | undefined>();    // resposta do backend
const segmentoAtual = ref<string | null>(null);                   // segmento da empresa logada

// Troca a query real (TanStack) por uma que lê os refs acima.
vi.mock('../useOSFieldDefinition.queries', () => ({
  useOSFieldDefinition: () => ({ data: contrato, isPending: carregando }),
}));
// Troca o segmento real (store de autenticação) pelo ref acima.
vi.mock('@/shared/composables/useSegmento', () => ({
  useSegmento: () => ({ segmento: segmentoAtual }),
}));

// Importa DEPOIS dos mocks: o composable usa as versões simuladas.
const { useRotulosStatusOS } = await import('../useRotulosStatusOS');

/** Monta um contrato carregado com a definição dada (só os campos que importam aqui). */
function contratoCom(definicao: Record<string, unknown>): SegmentDefinitionResponse {
  return { segmento: 'qualquer', tem_definicao: true, definicao } as unknown as SegmentDefinitionResponse;
}

/** O que a marcenaria declara no backend (Spec 01A). */
const DEFINICAO_MARCENARIA = {
  rotulos_status: {
    EM_ANDAMENTO: { rotulo: 'Em Produção', curto: 'Em produção' },
    AGUARDANDO_PECAS: { rotulo: 'Aguardando Material', curto: 'Aguard. material' },
    AGUARDANDO_RETIRADA: { rotulo: 'Aguardando Entrega', curto: 'Aguard. entrega' },
  },
  rotulos_situacao: { REPARADO: 'Entregue', SEM_REPARO: 'Não produzido', CONDENADO: 'Perda na produção' },
};

beforeEach(() => {
  // Cada teste começa com o contrato carregando e sem segmento.
  carregando.value = true;
  contrato.value = undefined;
  segmentoAtual.value = null;
});

describe('enquanto o contrato carrega (fallback, sem piscar)', () => {
  it('11 — marcenaria já mostra "Aguardando Entrega"', () => {
    segmentoAtual.value = 'marcenaria';
    expect(useRotulosStatusOS().rotuloStatus('AGUARDANDO_RETIRADA')).toBe('Aguardando Entrega');
  });

  it('12 — informática mostra o texto de sempre', () => {
    segmentoAtual.value = 'assistencia_tecnica';
    expect(useRotulosStatusOS().rotuloStatus('AGUARDANDO_RETIRADA')).toBe('Aguardando Retirada');
  });
});

describe('com o contrato carregado', () => {
  beforeEach(() => {
    carregando.value = false;
  });

  it('13 — o contrato manda, mesmo que o fallback diga outra coisa', () => {
    segmentoAtual.value = 'marcenaria';
    contrato.value = contratoCom({
      rotulos_status: { AGUARDANDO_RETIRADA: { rotulo: 'Pronto para Instalar', curto: 'P/ instalar' } },
    });
    expect(useRotulosStatusOS().rotuloStatus('AGUARDANDO_RETIRADA')).toBe('Pronto para Instalar');
  });

  it('14 — contrato sem a chave: todos os textos padrão', () => {
    segmentoAtual.value = 'assistencia_tecnica';
    contrato.value = contratoCom({});
    const { rotuloStatus } = useRotulosStatusOS();
    expect(rotuloStatus('EM_ANDAMENTO')).toBe('Em Andamento');
    expect(rotuloStatus('AGUARDANDO_PECAS')).toBe('Aguardando Peças');
    expect(rotuloStatus('AGUARDANDO_RETIRADA')).toBe('Aguardando Retirada');
  });

  it('15 — rotuloStatusProprio devolve undefined no status que a marcenaria não renomeia', () => {
    contrato.value = contratoCom(DEFINICAO_MARCENARIA);
    expect(useRotulosStatusOS().rotuloStatusProprio('ABERTA')).toBeUndefined();
  });

  it('16 — rotuloStatusProprio curto, para o dashboard', () => {
    contrato.value = contratoCom(DEFINICAO_MARCENARIA);
    expect(useRotulosStatusOS().rotuloStatusProprio('AGUARDANDO_PECAS', true)).toBe('Aguard. material');
  });

  it('17 — statusOptions da marcenaria: mesmos valores e ordem; texto trocado só nos três', () => {
    contrato.value = contratoCom(DEFINICAO_MARCENARIA);
    const opcoes = useRotulosStatusOS().statusOptions.value;
    expect(opcoes.map((o) => o.value)).toEqual(OS_STATUS_OPTIONS.map((o) => o.value));
    const renomeados = { EM_ANDAMENTO: 'Em Produção', AGUARDANDO_PECAS: 'Aguardando Material', AGUARDANDO_RETIRADA: 'Aguardando Entrega' };
    for (const [i, opcao] of opcoes.entries()) {
      const esperado = renomeados[opcao.value as keyof typeof renomeados] ?? OS_STATUS_OPTIONS[i].label;
      expect(opcao.label).toBe(esperado);
    }
  });

  it('18 — statusFilterConfig da marcenaria: mesmas chaves; desfecho com o texto do segmento', () => {
    contrato.value = contratoCom(DEFINICAO_MARCENARIA);
    const filtro = useRotulosStatusOS().statusFilterConfig.value;
    expect(Object.keys(filtro)).toEqual(Object.keys(OS_STATUS_FILTER_CONFIG));
    expect(filtro.SEM_REPARO.label).toBe('Não produzido');
    expect(filtro.CONDENADO.label).toBe('Perda na produção');
    expect(filtro.AGUARDANDO_RETIRADA.label).toBe('Aguardando Entrega');
    // Cores de sempre.
    expect(filtro.SEM_REPARO.class).toBe(OS_STATUS_FILTER_CONFIG.SEM_REPARO.class);
  });

  it('18a — informática (sem rotulos_situacao): desfechos com o texto de sempre', () => {
    segmentoAtual.value = 'assistencia_tecnica';
    contrato.value = contratoCom({});
    const filtro = useRotulosStatusOS().statusFilterConfig.value;
    expect(filtro).toEqual(OS_STATUS_FILTER_CONFIG);
    expect(filtro.SEM_REPARO.label).toBe('Sem Reparo');
    expect(filtro.CONDENADO.label).toBe('Condenado');
  });

  it('estadoOS junta status e desfecho do segmento, com as cores de sempre', () => {
    contrato.value = contratoCom(DEFINICAO_MARCENARIA);
    const { estadoOS } = useRotulosStatusOS();
    expect(estadoOS('EM_ANDAMENTO').label).toBe('Em Produção');
    expect(estadoOS('FINALIZADA', 'CONDENADO').label).toBe('Perda na produção');
  });
});
