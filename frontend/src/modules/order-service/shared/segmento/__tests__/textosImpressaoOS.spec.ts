/**
 * Spec 03B (marcenaria) — textos das vias impressas.
 *
 * A Spec 03B muda SÓ o pacote `planejados` (os campos que ele citava saíram da
 * OS). Os pacotes de oficina, informática, serigrafia e o pacote BASE da
 * marcenaria (textos da Reforma, guardados para a volta dela) não podem mudar:
 * o retrato em __snapshots__ foi gerado com o código de ANTES da mudança.
 */
import { describe, expect, it } from 'vitest';

import { PACOTES, aplicarTipoTrabalho } from '../textosImpressaoOS';

/**
 * Transforma um pacote em dado comparável: textos ficam como estão e cada
 * função (as cláusulas de prazo) é chamada com um marcador no lugar do prazo.
 */
function retrato(valor: unknown): unknown {
  if (typeof valor === 'function') return (valor as (p: string) => string)('<PRAZO>');
  if (Array.isArray(valor)) return valor.map(retrato);
  if (valor && typeof valor === 'object') {
    return Object.fromEntries(Object.entries(valor).map(([chave, v]) => [chave, retrato(v)]));
  }
  return valor;
}

/** Todos os textos de um pacote, numa string só (para procurar palavras). */
const textoCorrido = (valor: unknown) => JSON.stringify(retrato(valor));

describe('pacotes que não mudam (GUARDIÃO)', () => {
  it.each(['oficina_mecanica', 'assistencia_tecnica', 'serigrafia'])(
    '18 — pacote de %s igual ao de antes',
    (segmento) => {
      expect(retrato(PACOTES[segmento])).toMatchSnapshot();
    },
  );

  it('17 — pacote BASE da marcenaria (Reforma) igual ao de antes', () => {
    const { porTipoTrabalho: _sobrescritas, ...base } = PACOTES.marcenaria;  // só o base
    expect(retrato(base)).toMatchSnapshot();
  });
});

describe('Planejados (Spec 03B, D8)', () => {
  // O pacote que a via de uma OS de Móveis planejados usa de fato.
  const planejados = aplicarTipoTrabalho(PACOTES.marcenaria, 'planejados');

  it('16 — não cita campos que saíram da OS nem a "montagem externa"', () => {
    const tudo = textoCorrido(planejados).toLowerCase();
    expect(tudo).not.toContain('nesta os');            // projeto e materiais estão no orçamento
    expect(tudo).not.toContain('montagem externa');    // virou instalação
    expect(planejados.tituloPrazoRetirada).toBe('Entrega e Instalação');
  });

  it('16 — fala do orçamento aprovado e da instalação, na A4 e no cupom', () => {
    expect(planejados.condicoesEntrada).toContain('do orçamento aprovado');
    expect(planejados.cupom.condicoesEntrada).toContain('aprovado o orcamento');
    expect(planejados.prazoRetiradaEntradaA4?.('30 dias')).toContain('entrega e instalação');
    expect(planejados.cupom.prazoRetirada(30)).toMatch(/^ENTREGA E INSTALACAO:/);
  });

  it('sem tipo de trabalho, a mescla devolve o próprio pacote (como antes)', () => {
    expect(aplicarTipoTrabalho(PACOTES.marcenaria, null)).toBe(PACOTES.marcenaria);
  });
});
