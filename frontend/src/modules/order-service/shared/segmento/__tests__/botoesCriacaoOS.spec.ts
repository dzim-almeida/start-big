/**
 * Spec 03B (marcenaria, D3/D5) — onde aparecem os botões de criar OS.
 * As telas (OrdemServicoView e MainLayout) só chamam estas funções.
 */
import { describe, expect, it } from 'vitest';

import {
  atalhosComOrcamento,
  filtrarAtalhos,
  mostrarBotaoAdicionar,
  mostrarBotaoNovoOrcamento,
} from '../botoesCriacaoOS';

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

  it('abas Terceirizados e Produção (marcenaria, Specs 11B D13 e 12B): sem botão, só leem', () => {
    expect(mostrarBotaoAdicionar('terceirizados', false)).toBe(false);
    expect(mostrarBotaoAdicionar('producao', false)).toBe(false);
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

/**
 * Spec 06B (marcenaria, D4; casos 17 e 18) — "Criar OS" vira "Novo orçamento"
 * onde a OS não é criada à mão. O MainLayout e a OrdemServicoView só chamam
 * estas funções.
 */
describe('"Novo orçamento" no lugar de "Criar OS"', () => {
  const NOVO_ORCAMENTO = { id: 'novo-orcamento', label: 'Novo orçamento' };

  it('17 — informática: os 4 atalhos de hoje, mesmo com a alternativa disponível', () => {
    expect(atalhosComOrcamento(ATALHOS, true, NOVO_ORCAMENTO)).toEqual(ATALHOS);
    expect(atalhosComOrcamento(ATALHOS, true, null)).toEqual(ATALHOS);
  });

  it('18 — marcenaria, pode gerir: "Novo orçamento" no lugar de "Criar OS"', () => {
    expect(atalhosComOrcamento(ATALHOS, false, NOVO_ORCAMENTO).map((a) => a.label)).toEqual([
      'Criar Venda', 'Novo orçamento', 'Criar Produto', 'Criar Serviço',
    ]);
  });

  it('marcenaria sem permissão de orçamento: o atalho só some (como na 03B)', () => {
    expect(atalhosComOrcamento(ATALHOS, false, null)).toEqual(filtrarAtalhos(ATALHOS, false));
  });

  it('tela de OS: "Novo orçamento" só na aba Ordens da marcenaria, para quem pode gerir', () => {
    expect(mostrarBotaoNovoOrcamento('ordens', false, true)).toBe(true);
    expect(mostrarBotaoNovoOrcamento('ordens', true, true)).toBe(false);     // informática: "Nova OS"
    expect(mostrarBotaoNovoOrcamento('ordens', false, false)).toBe(false);   // sem permissão
    expect(mostrarBotaoNovoOrcamento('servicos', false, true)).toBe(false);  // aba Serviços: "Novo Serviço"
  });
});
