import { describe, expect, it } from 'vitest';

import {
  JANELA_CANCELAMENTO_MS,
  destinatarioAvulsoValido,
  montarItensLocais,
  prazoCancelamentoExpirado,
  totalmenteDevolvida,
  validarQuantidade,
  valorTotalEstimado,
} from '../useDevolucaoItens';
import type {
  DestinatarioAvulsoPayload,
  DocumentoFiscalRead,
  DocumentoItemResumo,
} from '../../types/fiscal.types';

const HORA = 60 * 60 * 1000;

function documento(sobrescrita: Partial<DocumentoFiscalRead> = {}): DocumentoFiscalRead {
  return {
    id: 1,
    tipo_documento: 'NFE',
    origem_tipo: 'VENDA',
    origem_id: 1,
    origem_numero_os: null,
    status: 'AUTORIZADA',
    chave_acesso: '35260911222333000181550010000000421000000429',
    numero_documento: 42,
    serie: 1,
    protocolo_autorizacao: '135',
    data_autorizacao: '2026-09-17T10:00:00Z',
    url_pdf: null,
    url_xml: null,
    mensagem_sefaz: null,
    codigo_status_sefaz: null,
    motivo_rejeicao: null,
    valor_total: 30000,
    qrcode: null,
    url_consulta: null,
    valor_tributos: null,
    ref_api: 'venda-1',
    ambiente_emissao: 2,
    tentativa_anterior_id: null,
    data_emissao: '2026-09-17T09:59:00Z',
    data_criacao: '2026-09-17T09:59:00Z',
    data_atualizacao: '2026-09-17T10:00:00Z',
    ...sobrescrita,
  };
}

function item(sobrescrita: Partial<DocumentoItemResumo> = {}): DocumentoItemResumo {
  return {
    id: 10,
    produto_id: 1,
    nome: 'Teclado',
    quantidade: 2,
    valor_unitario: 10000,
    subtotal: 20000,
    quantidade_milesimos: 2000,
    quantidade_devolvida_acumulada: 0,
    ...sobrescrita,
  };
}

describe('prazoCancelamentoExpirado', () => {
  const autorizada = Date.parse('2026-09-17T10:00:00Z');

  it('NF-e: 24 h a partir da autorização', () => {
    const doc = documento({ tipo_documento: 'NFE' });
    expect(prazoCancelamentoExpirado(doc, autorizada + 23 * HORA)).toBe(false);
    expect(prazoCancelamentoExpirado(doc, autorizada + 25 * HORA)).toBe(true);
    expect(JANELA_CANCELAMENTO_MS.NFE).toBe(24 * HORA);
  });

  it('NFC-e: 30 minutos', () => {
    const doc = documento({ tipo_documento: 'NFCE' });
    expect(prazoCancelamentoExpirado(doc, autorizada + 29 * 60 * 1000)).toBe(false);
    expect(prazoCancelamentoExpirado(doc, autorizada + 31 * 60 * 1000)).toBe(true);
  });

  it('sem data de autorização usa a de emissão; sem nenhuma, não expira', () => {
    const emitida = Date.parse('2026-09-17T09:59:00Z');
    expect(
      prazoCancelamentoExpirado(documento({ data_autorizacao: null }), emitida + 25 * HORA),
    ).toBe(true);
    expect(
      prazoCancelamentoExpirado(
        documento({ data_autorizacao: null, data_emissao: null }),
        emitida + 99 * HORA,
      ),
    ).toBe(false);
  });
});

describe('montarItensLocais / saldo', () => {
  it('saldo é quantidade menos devolvido, nunca negativo, e a linha nasce selecionada com o saldo', () => {
    const [a, b, c] = montarItensLocais([
      item({ id: 1 }),
      item({ id: 2, quantidade_devolvida_acumulada: 1500 }),
      item({ id: 3, quantidade_devolvida_acumulada: 5000 }),
    ]);
    expect(a.saldoDisponivelMil).toBe(2000);
    expect(b.saldoDisponivelMil).toBe(500);
    expect(c.saldoDisponivelMil).toBe(0);
    expect(a.qtdDevolverMil).toBe(2000);
    expect(a.selecionado).toBe(true);
    expect(c.selecionado).toBe(false);
  });

  it('item sem snapshot (sem milésimos) usa a quantidade inteira', () => {
    const [x] = montarItensLocais([
      item({ quantidade_milesimos: null, quantidade_devolvida_acumulada: null, quantidade: 3 }),
    ]);
    expect(x.saldoDisponivelMil).toBe(3000);
  });

  it('totalmenteDevolvida quando nenhum item tem saldo', () => {
    expect(totalmenteDevolvida([item({ quantidade_devolvida_acumulada: 2000 })])).toBe(true);
    expect(totalmenteDevolvida([item()])).toBe(false);
    expect(totalmenteDevolvida([])).toBe(false);
  });
});

describe('validarQuantidade', () => {
  it('aceita 1..saldo e recusa zero, negativo e excedente', () => {
    expect(validarQuantidade(1, 2000)).toBeNull();
    expect(validarQuantidade(2000, 2000)).toBeNull();
    expect(validarQuantidade(0, 2000)).toMatch(/maior que zero/);
    expect(validarQuantidade(-5, 2000)).toMatch(/maior que zero/);
    expect(validarQuantidade(2001, 2000)).toMatch(/saldo/);
  });
});

describe('valorTotalEstimado', () => {
  it('soma proporcional só dos selecionados, em centavos', () => {
    const itens = montarItensLocais([
      item({ id: 1 }),
      item({ id: 2, valor_unitario: 5000, quantidade_milesimos: 1000 }),
    ]);
    itens[0].qtdDevolverMil = 500; // meia unidade de R$ 100
    itens[1].selecionado = false;
    expect(valorTotalEstimado(itens)).toBe(5000);
  });
});

describe('destinatarioAvulsoValido', () => {
  const ok: DestinatarioAvulsoPayload = {
    cpf_ou_cnpj: '12345678909',
    nome_razao_social: 'Maria',
    indicador_inscricao_estadual: 9,
    logradouro: 'Rua B',
    numero: '20',
    bairro: 'Centro',
    codigo_municipio: '3550308',
    municipio: 'Sao Paulo',
    uf: 'SP',
    cep: '01001000',
  };

  it('exige documento com 11/14 dígitos, CEP 8, IBGE 7 e endereço completo', () => {
    expect(destinatarioAvulsoValido(ok)).toBe(true);
    expect(destinatarioAvulsoValido({ ...ok, cpf_ou_cnpj: '123.456.789-09' })).toBe(true); // sanitiza
    expect(destinatarioAvulsoValido({ ...ok, cpf_ou_cnpj: '123' })).toBe(false);
    expect(destinatarioAvulsoValido({ ...ok, cep: '0100100' })).toBe(false);
    expect(destinatarioAvulsoValido({ ...ok, codigo_municipio: '355030' })).toBe(false);
    expect(destinatarioAvulsoValido({ ...ok, logradouro: '' })).toBe(false);
  });

  it('contribuinte (1) precisa de IE', () => {
    expect(destinatarioAvulsoValido({ ...ok, indicador_inscricao_estadual: 1 })).toBe(false);
    expect(
      destinatarioAvulsoValido({
        ...ok,
        indicador_inscricao_estadual: 1,
        inscricao_estadual: '123',
      }),
    ).toBe(true);
  });
});
