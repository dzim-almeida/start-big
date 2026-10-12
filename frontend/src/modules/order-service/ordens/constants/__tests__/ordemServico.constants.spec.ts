/**
 * Spec 01B (marcenaria) — montadores das opções de status e do filtro.
 *
 * O que não pode regredir: as constantes de sempre (select do modal e menu de
 * filtro da lista) continuam com EXATAMENTE o mesmo conteúdo para informática,
 * oficina e serigrafia. O "retrato" abaixo foi gerado do código ANTES da
 * mudança (09/10/2026): se um teste daqui falhar, alguma loja em produção
 * passou a ver outra coisa.
 */
import { describe, expect, it } from 'vitest';

import {
  OS_STATUS_FILTER_CONFIG,
  OS_STATUS_OPTIONS,
  montarFiltroStatus,
  montarOpcoesStatus,
} from '../ordemServico.constants';

/** Retrato de OS_STATUS_OPTIONS antes da Spec 01B (valores, textos e ordem). */
const OPCOES_ANTES = [
  { value: 'ABERTA', label: 'Aberta' },
  { value: 'EM_ANDAMENTO', label: 'Em Andamento' },
  { value: 'AGUARDANDO_PECAS', label: 'Aguardando Peças' },
  { value: 'AGUARDANDO_APROVACAO', label: 'Aguardando Aprovação' },
  { value: 'AGUARDANDO_RETIRADA', label: 'Aguardando Retirada' },
  { value: 'FINALIZADA', label: 'Finalizada' },
  { value: 'CANCELADA', label: 'Cancelada' },
];

/** Retrato de OS_STATUS_FILTER_CONFIG antes da Spec 01B (sem CANCELADA). */
const FILTRO_ANTES = {
  ABERTA: { label: 'Aberta', class: 'bg-blue-50 text-blue-600', color: 'bg-blue-500' },
  EM_ANDAMENTO: { label: 'Em Andamento', class: 'bg-amber-50 text-amber-700', color: 'bg-amber-500' },
  AGUARDANDO_PECAS: { label: 'Aguardando Peças', class: 'bg-orange-50 text-orange-700', color: 'bg-orange-500' },
  AGUARDANDO_APROVACAO: { label: 'Aguardando Aprovação', class: 'bg-purple-50 text-purple-700', color: 'bg-purple-500' },
  AGUARDANDO_RETIRADA: { label: 'Aguardando Retirada', class: 'bg-indigo-50 text-indigo-700', color: 'bg-indigo-500' },
  FINALIZADA: { label: 'Finalizada', class: 'bg-emerald-50 text-emerald-700', color: 'bg-emerald-500' },
  SEM_REPARO: { label: 'Sem Reparo', class: 'bg-amber-50 text-amber-700', color: 'bg-amber-400' },
  CONDENADO: { label: 'Condenado', class: 'bg-red-50 text-red-700', color: 'bg-red-600' },
};

describe('constantes de sempre (GUARDIÃO dos outros segmentos)', () => {
  it('01 — OS_STATUS_OPTIONS igual ao retrato de antes', () => {
    expect(OS_STATUS_OPTIONS).toEqual(OPCOES_ANTES);
  });

  it('02 — OS_STATUS_FILTER_CONFIG igual ao retrato de antes, na mesma ordem', () => {
    expect(OS_STATUS_FILTER_CONFIG).toEqual(FILTRO_ANTES);
    // A ordem das chaves é a ordem do menu: primeiro o fluxo, depois os desfechos.
    expect(Object.keys(OS_STATUS_FILTER_CONFIG)).toEqual(Object.keys(FILTRO_ANTES));
  });
});

describe('montadores', () => {
  it('03 — montarOpcoesStatus troca só o texto; o valor continua o código do enum', () => {
    const opcoes = montarOpcoesStatus(() => 'X');      // um "segmento" que renomeia tudo
    expect(opcoes.map((o) => o.label)).toEqual(Array(7).fill('X'));
    expect(opcoes.map((o) => o.value)).toEqual(OPCOES_ANTES.map((o) => o.value));
  });

  it('04 — montarFiltroStatus mantém as chaves (o filtro salvo continua valendo)', () => {
    const filtro = montarFiltroStatus(() => 'X');
    expect(Object.keys(filtro)).toEqual(Object.keys(FILTRO_ANTES));
    // As cores não dependem do segmento.
    expect(filtro.AGUARDANDO_RETIRADA.class).toBe(FILTRO_ANTES.AGUARDANDO_RETIRADA.class);
    expect(filtro.AGUARDANDO_RETIRADA.color).toBe(FILTRO_ANTES.AGUARDANDO_RETIRADA.color);
  });
});
