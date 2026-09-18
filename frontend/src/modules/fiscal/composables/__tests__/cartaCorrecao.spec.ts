import { describe, expect, it } from 'vitest';

import { resolverDesfechoCarta } from '../useFiscalCartaCorrecaoMutation';
import { podeTerCartaCorrecao } from '../useFiscalCartasCorrecaoQuery';
import type { CartaCorrecaoRead } from '../../types/fiscal.types';

function carta(sobrescrita: Partial<CartaCorrecaoRead> = {}): CartaCorrecaoRead {
  return {
    id: 1,
    documento_id: 10,
    sequencia: 1,
    correcao: 'Corrigido o complemento do endereço do destinatário.',
    status: 'AUTORIZADA',
    protocolo: '135260000000001',
    codigo_status_sefaz: 135,
    mensagem_sefaz: 'Evento registrado e vinculado a NF-e',
    url_xml: null,
    url_pdf: null,
    xml_local: false,
    pdf_local: false,
    data_evento: '2026-09-17T21:00:00Z',
    data_criacao: '2026-09-17T21:00:00Z',
    ...sobrescrita,
  };
}

describe('resolverDesfechoCarta', () => {
  it('autorizada vira sucesso com a sequência da SEFAZ', () => {
    const d = resolverDesfechoCarta(carta({ sequencia: 3 }));
    expect(d.tipo).toBe('sucesso');
    expect(d.titulo).toContain('nº 3');
  });

  it('rejeitada pela SEFAZ é aviso com a mensagem dela, não erro do sistema', () => {
    const d = resolverDesfechoCarta(
      carta({ status: 'REJEITADA', sequencia: null, mensagem_sefaz: 'Rejeição: Duplicidade de Evento' }),
    );
    expect(d.tipo).toBe('rejeitada');
    expect(d.descricao).toBe('Rejeição: Duplicidade de Evento');
  });

  it('erro da plataforma vira erro', () => {
    const d = resolverDesfechoCarta(carta({ status: 'ERRO', sequencia: null, mensagem_sefaz: null }));
    expect(d.tipo).toBe('erro');
    expect(d.descricao).toBeTruthy();
  });
});

describe('podeTerCartaCorrecao', () => {
  it('só NF-e autorizada', () => {
    expect(podeTerCartaCorrecao({ tipo_documento: 'NFE', status: 'AUTORIZADA' })).toBe(true);
    expect(podeTerCartaCorrecao({ tipo_documento: 'NFCE', status: 'AUTORIZADA' })).toBe(false);
    expect(podeTerCartaCorrecao({ tipo_documento: 'NFE', status: 'CANCELADA' })).toBe(false);
    expect(podeTerCartaCorrecao(null)).toBe(false);
  });
});
