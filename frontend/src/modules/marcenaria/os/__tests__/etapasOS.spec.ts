/**
 * Etapas e "Avançar" da OS da marcenaria (redesign das telas, 10/2026).
 */
import { describe, expect, it } from 'vitest';

import { etapasDaOS, proximoStatus } from '../utils/etapasOS';

const rotulo = (s: string) => s;
const estados = (status: string | null) => etapasDaOS(status, rotulo).map((e) => e.estado);

describe('etapas da OS da marcenaria', () => {
  it('Em Produção: as duas primeiras concluídas, a terceira atual', () => {
    expect(estados('EM_ANDAMENTO')).toEqual(['concluida', 'concluida', 'atual', 'pendente', 'pendente']);
  });

  it('Aberta: a primeira é a atual', () => {
    expect(estados('ABERTA')).toEqual(['atual', 'pendente', 'pendente', 'pendente', 'pendente']);
  });

  it('Finalizada: tudo concluído (nada fica "atual")', () => {
    expect(estados('FINALIZADA')).toEqual(['concluida', 'concluida', 'concluida', 'concluida', 'concluida']);
  });

  it('fora do fluxo (Cancelada) ou sem status: tudo pendente', () => {
    expect(estados('CANCELADA')).toEqual(Array(5).fill('pendente'));
    expect(estados(null)).toEqual(Array(5).fill('pendente'));
  });

  it('os rótulos vêm de quem chama (contrato do segmento)', () => {
    const r = etapasDaOS('ABERTA', (s) => (s === 'EM_ANDAMENTO' ? 'Em Produção' : s));
    expect(r[2].rotulo).toBe('Em Produção');
  });
});

describe('próximo status do botão "Avançar"', () => {
  it('Aberta e Aguardando Material vão para Em Produção', () => {
    expect(proximoStatus('ABERTA')).toBe('EM_ANDAMENTO');
    expect(proximoStatus('AGUARDANDO_PECAS')).toBe('EM_ANDAMENTO');
  });

  it('Em Produção vai para Aguardando Entrega', () => {
    expect(proximoStatus('EM_ANDAMENTO')).toBe('AGUARDANDO_RETIRADA');
  });

  it('Aguardando Entrega não avança por aqui: finalizar tem o próprio botão', () => {
    expect(proximoStatus('AGUARDANDO_RETIRADA')).toBeNull();
    expect(proximoStatus('FINALIZADA')).toBeNull();
    expect(proximoStatus('CANCELADA')).toBeNull();
  });
});
