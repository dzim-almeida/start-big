import { describe, expect, it } from 'vitest';

import { janelaDePaginas } from '../janelaDePaginas';

describe('janelaDePaginas', () => {
  it('mostra o anterior, o atual e o próximo', () => {
    expect(janelaDePaginas(5, 10)).toEqual([4, 5, 6]);
  });

  it('encosta nas pontas mantendo 3 números', () => {
    expect(janelaDePaginas(1, 10)).toEqual([1, 2, 3]);
    expect(janelaDePaginas(10, 10)).toEqual([8, 9, 10]);
  });

  it('com menos de 3 páginas, mostra as que existem', () => {
    expect(janelaDePaginas(1, 2)).toEqual([1, 2]);
    expect(janelaDePaginas(1, 1)).toEqual([1]);
    expect(janelaDePaginas(1, 0)).toEqual([]);
  });

  it('página fora do intervalo não quebra a janela', () => {
    expect(janelaDePaginas(15, 10)).toEqual([8, 9, 10]);
  });
});
