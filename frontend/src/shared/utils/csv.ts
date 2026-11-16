import { salvarArquivo } from './arquivo';

/** Monta o conteúdo CSV (separador ";" + BOM UTF-8 — combo que o Excel PT-BR abre certo). */
function montarCsv(headers: string[], rows: (string | number)[][]): string {
  const esc = (v: string | number): string => {
    const s = String(v ?? '');
    return /[";\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const sep = ';';
  const linhas = [headers, ...rows].map((r) => r.map(esc).join(sep));
  return '﻿' + linhas.join('\r\n'); // BOM UTF-8
}

/**
 * Gera um CSV e o entrega ao usuário pelo "Salvar como" do Windows (no
 * navegador, download comum). Devolve o caminho salvo, ou null se o usuário
 * cancelou ou se está no navegador. Lança `ErroAoSalvar` se não gravar.
 */
export async function saveCsv(
  filename: string,
  headers: string[],
  rows: (string | number)[][],
): Promise<string | null> {
  const blob = new Blob([montarCsv(headers, rows)], { type: 'text/csv;charset=utf-8;' });
  const r = await salvarArquivo(filename, blob);
  return r.cancelado ? null : r.caminho;
}
