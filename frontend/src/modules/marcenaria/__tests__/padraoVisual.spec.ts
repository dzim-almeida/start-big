/**
 * Padrão visual da Marcenaria (redesign 10/2026).
 *
 * O módulo saiu do padrão do sistema porque cada tela montou o próprio
 * <select>, <textarea> e afins. Campo de formulário é componente base
 * (BaseSelect, BaseTextarea…). Onde o nativo é necessário, a exceção fica
 * escrita na linha de cima, com o motivo:
 *
 *   <!-- eslint-disable-next-line vue/no-restricted-html-elements -- nativo: <motivo> -->
 *
 * A mesma regra está no .eslintrc.cjs; este teste existe porque o lint do
 * projeto não roda hoje (ESLint 9 sem eslint.config.js). Impressões (*Print*)
 * ficam de fora: são HTML para papel, não tela.
 */
import { describe, expect, it } from 'vitest';

const fontes = import.meta.glob<string>('../**/*.vue', { query: '?raw', import: 'default', eager: true });

const MARCA_EXCECAO = /eslint-disable-next-line vue\/no-restricted-html-elements -- nativo: \S/;

/** As tags nativas proibidas sem a exceção escrita na linha anterior. */
function semExcecao(fonte: string): string[] {
  const linhas = fonte.split(/\r?\n/);
  const achados: string[] = [];
  linhas.forEach((linha, i) => {
    const tag = linha.match(/<(select|textarea)(\s|>|$)/)?.[1];
    if (!tag || linha.trim().startsWith('/') || linha.trim().startsWith('*')) return;   // comentário de script
    if (!MARCA_EXCECAO.test(linhas[i - 1] ?? '')) achados.push(`linha ${i + 1}: <${tag}>`);
  });
  return achados;
}

describe('padrão visual da Marcenaria', () => {
  const arquivos = Object.entries(fontes).filter(([caminho]) => !caminho.includes('__tests__') && !/Print\.vue$/.test(caminho));

  it('acha os componentes do módulo (o glob não pode vir vazio)', () => {
    expect(arquivos.length).toBeGreaterThan(30);
  });

  it('a trava pega o nativo sem motivo e aceita o com motivo', () => {
    expect(semExcecao('<div>\n  <select v-model="x">')).toEqual(['linha 2: <select>']);
    expect(semExcecao('<!-- eslint-disable-next-line vue/no-restricted-html-elements -- nativo: leitor -->\n<textarea />')).toEqual([]);
    expect(semExcecao('<!-- eslint-disable-next-line vue/no-restricted-html-elements -->\n<textarea />')).toHaveLength(1);   // sem motivo
  });

  it.each(arquivos.map(([caminho, fonte]) => [caminho, fonte] as const))(
    '%s: sem <select>/<textarea> nativo sem motivo escrito',
    (_caminho, fonte) => {
      expect(semExcecao(fonte)).toEqual([]);
    },
  );
});
