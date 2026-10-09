/**
 * Spec 03B (marcenaria, D3/D5) — onde aparecem os botões de criar OS.
 * As telas (OrdemServicoView e MainLayout) só chamam estas funções.
 */
import { describe, expect, it } from 'vitest';

import { filtrarAtalhos, mostrarBotaoAdicionar } from '../botoesCriacaoOS';

/** Os 4 atalhos do menu rápido, na ordem do MainLayout. */
const ATALHOS = [
  { id: 'nova-venda', label: 'Criar Venda' },
  { id: 'nova-os', label: 'Criar OS' },
  { id: 'novo-produto', label: 'Criar Produto' },
  { id: 'novo-servico', label: 'Criar Serviço' },
];

describe('botão do topo da tela de OS', () => {
  it('09 — marcenaria, aba Ordens: sem "Nova OS"', () => {
    expect(mostrarBotaoAdicionar('ordens', false)).toBe(false);
  });

  it('10 — marcenaria, aba Serviços: "Novo Serviço" continua', () => {
    expect(mostrarBotaoAdicionar('servicos', false)).toBe(true);
  });

  it('11 — serigrafia (e informática, oficina), aba Ordens: "Nova OS" como sempre', () => {
    expect(mostrarBotaoAdicionar('ordens', true)).toBe(true);
  });

  it('aba Revisões nunca teve botão', () => {
    expect(mostrarBotaoAdicionar('revisoes', true)).toBe(false);
  });
});

describe('atalhos do menu rápido', () => {
  it('12 — marcenaria: sem "Criar OS"; os outros 3 na mesma ordem', () => {
    expect(filtrarAtalhos(ATALHOS, false).map((a) => a.id)).toEqual(['nova-venda', 'novo-produto', 'novo-servico']);
  });

  it('13 — informática: os 4 atalhos de hoje, na mesma ordem', () => {
    expect(filtrarAtalhos(ATALHOS, true)).toEqual(ATALHOS);
  });
});
