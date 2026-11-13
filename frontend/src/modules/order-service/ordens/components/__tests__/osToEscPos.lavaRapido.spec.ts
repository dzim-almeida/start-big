/**
 * Via térmica (ESC/POS) do lava-rápido: avarias na entrada e recibo sem a
 * "Declaração sem reparo" na saída. Os outros segmentos não declaram esses
 * campos no pacote e continuam imprimindo o de sempre.
 */
import { describe, expect, it } from 'vitest';

import { PACOTES } from '@/modules/order-service/shared/segmento/textosImpressaoOS';
import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';
import { osToEscPos } from '../osToEscPos';

function os(dados: Record<string, unknown>, extra: Record<string, unknown> = {}): OrderServiceReadDataType {
  return {
    numero_os: 'OS-1',
    data_criacao: '2026-11-13T10:00:00',
    data_finalizacao: null,
    cliente: null,
    objeto: { tipo_equipamento: 'carro', marca: null, modelo: 'Strada', numero_serie: 'OCR0075', cor: 'Vermelha' },
    defeito_relatado: 'LAVAGEM SIMPLES - CARRO',
    observacoes: null,
    dados_adicionais: dados,
    itens: [],
    pagamentos: [],
    situacao_equipamento: null,
    garantia: null,
    ...extra,
  } as unknown as OrderServiceReadDataType;
}

const texto = (bytes: Uint8Array) => new TextDecoder('latin1').decode(bytes);
const empresa = { nome: 'Lava Jato' } as never;

describe('osToEscPos — lava-rápido', () => {
  const textos = PACOTES.lava_rapido.cupom;

  it('entrada lista as avarias marcadas', () => {
    const via = texto(osToEscPos(os({ avarias: ['Riscos na pintura', 'Amassados'] }), 'ENTRADA', { bobina: '80', empresa, textos }));
    expect(via).toContain('AVARIAS NA CHEGADA');
    expect(via).toContain('Riscos na pintura, Amassados');
    expect(via).toContain('PEDIDO DO CLIENTE');
  });

  it('entrada sem avaria diz que não houve', () => {
    const via = texto(osToEscPos(os({}), 'ENTRADA', { bobina: '80', empresa, textos }));
    expect(via).toContain('Nenhuma avaria registrada.');
  });

  it('saída concluída é recibo, sem "sem reparo" nem garantia', () => {
    const via = texto(osToEscPos(os({}, { situacao_equipamento: 'REPARADO' }), 'SAIDA', { bobina: '80', empresa, textos }));
    expect(via).toContain('RECIBO DE SERVICO');
    expect(via).not.toContain('RECIBO E GARANTIA');
    expect(via).not.toContain(textos.semReparo);
  });

  it('assistência técnica (sem os campos novos) não muda', () => {
    const via = texto(osToEscPos(os({ avarias: ['x'] }), 'ENTRADA', { bobina: '80', empresa }));
    expect(via).not.toContain('AVARIAS');
    const saida = texto(osToEscPos(os({}), 'SAIDA', { bobina: '80', empresa }));
    expect(saida).toContain('RECIBO E GARANTIA');
  });
});
