/**
 * usePrintFlow — remodelação da marcenaria, itens 15 e 18: nenhum formato
 * escolhido antes de imprimir. Começar em 'A4' deixava o recibo da OS montado
 * desde a abertura, e ele saía junto com as faltas e as etiquetas.
 */
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/shared/composables/usePerfilComprovante', () => ({ usePerfilComprovante: () => ({ opcoesPaginaDe: () => ({}) }) }));
vi.mock('@/shared/utils/print.utils', () => ({ imprimirComPagina: vi.fn(), aguardarImagensDaImpressao: async () => {} }));

const { usePrintFlow } = await import('../usePrintFlow');

describe('usePrintFlow', () => {
  it('começa sem formato: nenhum modelo de impressão montado à toa', () => {
    expect(usePrintFlow().printFormat.value).toBe('');
  });

  it('imprimir escolhe o formato na hora (e limpa depois)', async () => {
    vi.useFakeTimers();
    const fluxo = usePrintFlow();
    fluxo.printDirect('ENTRADA', 'A4');
    expect(fluxo.printFormat.value).toBe('A4');               // o modelo A4 aparece para imprimir
    await vi.runAllTimersAsync();
    expect(fluxo.printFormat.value).toBe('');                 // e sai depois
    vi.useRealTimers();
  });
});
