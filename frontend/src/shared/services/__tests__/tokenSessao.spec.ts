/**
 * Testes do dono único do token do login (LIC-04 §6.2, ADR-003, D-27).
 *
 * O jsdom (o "navegador de mentira" dos testes) tem sessionStorage e
 * localStorage de verdade. "Fechar a janela" é simulado limpando o
 * sessionStorage, que é exatamente o que o navegador faz ao fechar.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { apagarToken, guardarToken, lerToken, limparTokenAntigo } from '../tokenSessao.service';

afterEach(() => {
  // Cada teste começa sem nada guardado
  sessionStorage.clear();
  localStorage.clear();
});

describe('tokenSessao.service', () => {
  it('CT-05: guarda e lê o mesmo token, na sessionStorage e não no localStorage', () => {
    guardarToken('abc.def.ghi');
    expect(lerToken()).toBe('abc.def.ghi');
    expect(sessionStorage.getItem('access_token')).toBe('abc.def.ghi');
    expect(localStorage.getItem('access_token')).toBeNull(); // nada em disco
  });

  it('CT-06: recarregar a página (mesma sessão) mantém o token', async () => {
    guardarToken('token-1');
    // Recarregar = o módulo é carregado de novo, mas a sessionStorage continua
    vi.resetModules();
    const recarregado = await import('../tokenSessao.service');
    expect(recarregado.lerToken()).toBe('token-1');
  });

  it('CT-07: janela fechada (sessão nova) não tem token', () => {
    guardarToken('token-1');
    sessionStorage.clear(); // o navegador limpa a sessionStorage ao fechar a janela
    expect(lerToken()).toBeNull();
  });

  it('CT-08: limparTokenAntigo apaga o token que versões antigas gravaram no disco', () => {
    localStorage.setItem('access_token', 'token-de-versao-antiga');
    limparTokenAntigo();
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('apagarToken encerra a sessão (logout)', () => {
    guardarToken('token-1');
    apagarToken();
    expect(lerToken()).toBeNull();
  });
});
