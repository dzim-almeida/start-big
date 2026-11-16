/**
 * Spec 01B (marcenaria) — `getEstadoOS` com rótulos opcionais do segmento.
 *
 * Regra que protege as lojas em produção: SEM rótulos, a função devolve o
 * MESMO objeto de OS_ESTADO_CONFIG de sempre (comparação por identidade, não
 * só por valor). Com rótulos, troca só o texto; as cores ficam.
 */
import { describe, expect, it } from 'vitest';

import { OS_ESTADO_CONFIG } from '../../../ordens/constants/ordemServico.constants';
import type { OsStatusEnumDataType } from '../../../ordens/schemas/enums/osEnums.schema';
import { getEstadoOS, type RotulosEstadoOS } from '../formatters';

/** O que a marcenaria declara no backend (Spec 01A). */
const MARCENARIA: RotulosEstadoOS['status'] = {
  EM_ANDAMENTO: { rotulo: 'Em Produção', curto: 'Em produção' },
  AGUARDANDO_PECAS: { rotulo: 'Aguardando Material', curto: 'Aguard. material' },
  AGUARDANDO_RETIRADA: { rotulo: 'Aguardando Entrega', curto: 'Aguard. entrega' },
};

const TODOS_OS_STATUS: OsStatusEnumDataType[] = [
  'ABERTA', 'EM_ANDAMENTO', 'AGUARDANDO_PECAS', 'AGUARDANDO_APROVACAO',
  'AGUARDANDO_RETIRADA', 'FINALIZADA', 'CANCELADA',
];

describe('getEstadoOS sem rótulos (outros segmentos)', () => {
  it.each(TODOS_OS_STATUS)('05 — %s devolve o mesmo objeto de sempre', (status) => {
    expect(getEstadoOS(status)).toBe(OS_ESTADO_CONFIG[status]);
  });

  it('08a — desfecho CONDENADO sem rótulos é o objeto de sempre', () => {
    expect(getEstadoOS('FINALIZADA', 'CONDENADO')).toBe(OS_ESTADO_CONFIG.CONDENADO);
  });

  it('09 — OS sem status aparece como Aberta, como hoje', () => {
    expect(getEstadoOS(null)).toBe(OS_ESTADO_CONFIG.ABERTA);
  });

  it('10 — rótulos vazios = texto padrão', () => {
    expect(getEstadoOS('EM_ANDAMENTO', null, {}).label).toBe('Em Andamento');
  });
});

describe('getEstadoOS com os rótulos da marcenaria', () => {
  it('06 — troca o texto e mantém as cores', () => {
    const estado = getEstadoOS('AGUARDANDO_RETIRADA', null, { status: MARCENARIA });
    expect(estado.label).toBe('Aguardando Entrega');
    expect(estado.badge).toBe(OS_ESTADO_CONFIG.AGUARDANDO_RETIRADA.badge);
    expect(estado.dot).toBe(OS_ESTADO_CONFIG.AGUARDANDO_RETIRADA.dot);
    expect(estado.border).toBe(OS_ESTADO_CONFIG.AGUARDANDO_RETIRADA.border);
    // Não altera a constante compartilhada (copia antes de trocar o texto).
    expect(OS_ESTADO_CONFIG.AGUARDANDO_RETIRADA.label).toBe('Aguardando Retirada');
  });

  it('07 — status que o segmento não renomeia continua com o texto padrão', () => {
    expect(getEstadoOS('ABERTA', null, { status: MARCENARIA }).label).toBe('Aberta');
  });

  it('08 — desfecho usa o rótulo do segmento, com as cores do desfecho', () => {
    const estado = getEstadoOS('FINALIZADA', 'SEM_REPARO', {
      status: MARCENARIA,
      situacao: { SEM_REPARO: 'Não produzido' },
    });
    expect(estado.label).toBe('Não produzido');
    expect(estado.badge).toBe(OS_ESTADO_CONFIG.SEM_REPARO.badge);
  });

  it('08b — OS reaberta não mostra o desfecho antigo', () => {
    const estado = getEstadoOS('ABERTA', 'SEM_REPARO', { situacao: { SEM_REPARO: 'Não produzido' } });
    expect(estado.label).toBe('Aberta');
  });
});
