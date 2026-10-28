/**
 * Nota repetida na venda e no PDV (docs/nfse-fase2-plano.md, G2).
 *
 * A plataforma recusa com 409 NOTA_DUPLICADA_SUSPEITA quando a mesma nota foi
 * autorizada há menos de 1 h. Nada saiu: o operador vê o aviso e só com
 * "Emitir mesmo assim" a nota é reenviada, com a confirmação.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

const warning = vi.fn();
const success = vi.fn();
vi.mock('@/shared/composables/useToast', () => ({
  useToast: () => ({ warning, success, info: vi.fn(), error: vi.fn() }),
}));
vi.mock('@/modules/fiscal/composables/useNumeracaoConfirmada', () => ({
  useNumeracaoConfirmada: () => ({ garantirNumeracaoConfirmada: () => true }),
}));
vi.mock('@/modules/sales/api.service', () => ({
  saleService: { verificarFiscal: vi.fn().mockResolvedValue({ completo: true, pendencias: [] }), upsertVendaNotaFiscal: vi.fn() },
}));

const emitirNfe = vi.fn();
const emitirNfce = vi.fn();
vi.mock('@/modules/fiscal/services/fiscal.service', () => ({
  fiscalService: {
    emitirNfe: (...a: unknown[]) => emitirNfe(...a),
    emitirNfce: (...a: unknown[]) => emitirNfce(...a),
    obterDocumento: vi.fn(),
  },
}));

const { useEmitirFiscal } = await import('../useEmitirFiscal');

const REPETIDA = {
  response: { status: 409, data: { detail: { codigo: 'NOTA_DUPLICADA_SUSPEITA', mensagem: 'Igual à ref venda-7, autorizada há 3 min.' } } },
};

afterEach(() => vi.clearAllMocks());

describe('Nota repetida', () => {
  it('NF-e da venda: avisa, não emite sozinha, e "Emitir mesmo assim" confirma', async () => {
    emitirNfe.mockRejectedValueOnce(REPETIDA).mockResolvedValueOnce({ status: 'AUTORIZADA', documento_id: 9 });
    const { emitirVenda } = useEmitirFiscal();

    expect(await emitirVenda(5)).toBeNull();
    expect(emitirNfe).toHaveBeenCalledTimes(1);
    const [titulo, descricao, opcoes] = warning.mock.calls[0];
    expect(titulo).toContain('igual a outra');
    expect(descricao).toContain('autorizada há 3 min');

    await opcoes.action.onClick();
    expect(emitirNfe).toHaveBeenLastCalledWith({ venda_id: 5 }, true);
    expect(success).toHaveBeenCalledWith('NF-e autorizada!');
  });

  it('NFC-e do PDV: mesmo aviso, reenvio com a confirmação', async () => {
    emitirNfce.mockRejectedValueOnce(REPETIDA).mockResolvedValueOnce({ status: 'AUTORIZADA', documento_id: 3 });
    const { emitirNFCeVenda } = useEmitirFiscal();

    expect(await emitirNFCeVenda(8, '52998224725')).toBeNull();
    await warning.mock.calls[0][2].action.onClick();
    expect(emitirNfce).toHaveBeenLastCalledWith({ venda_id: 8 }, true);
  });
});
