/**
 * Regra do "Salvar como": no app, todo arquivo que o usuário salva (DANFE,
 * XML, ZIP do contador, CSV dos relatórios) passa pela janela do Windows.
 *
 * 1. Grava exatamente onde o usuário escolheu, sugerindo a pasta Downloads.
 * 2. Cancelar não grava nada.
 * 3. Se a janela não abrir, é erro — nunca grava escondido no AppData (o
 *    comportamento antigo: o arquivo ia para onde o usuário não achava).
 * 4. Arquivo aberto em outro programa vira erro de GRAVAR, com mensagem própria.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const save = vi.fn();
const writeFile = vi.fn();
const writeTextFile = vi.fn();
const openPath = vi.fn();

vi.mock('@tauri-apps/api/core', () => ({ isTauri: () => true }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ save }));
vi.mock('@tauri-apps/api/path', () => ({
  downloadDir: async () => 'C:\\Users\\Loja\\Downloads',
  join: async (...partes: string[]) => partes.join('\\'),
}));
vi.mock('@tauri-apps/plugin-fs', () => ({ writeFile, writeTextFile }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath }));

import { ErroAoSalvar, salvarArquivo } from '../arquivo';
import { saveCsv } from '../csv';

const pdf = () => new Blob(['%PDF-1.4'], { type: 'application/pdf' });

describe('salvarArquivo no app', () => {
  beforeEach(() => {
    save.mockReset();
    writeFile.mockReset();
    writeTextFile.mockReset();
    openPath.mockReset();
  });

  it('abre o "Salvar como" sugerindo Downloads e grava onde o usuário escolheu', async () => {
    save.mockResolvedValue('D:\\Notas\\nota.pdf');

    const r = await salvarArquivo('nota.pdf', pdf());

    expect(save).toHaveBeenCalledWith({
      defaultPath: 'C:\\Users\\Loja\\Downloads\\nota.pdf',
      filters: [{ name: 'PDF', extensions: ['pdf'] }],
    });
    expect(writeFile).toHaveBeenCalledTimes(1);
    expect(writeFile.mock.calls[0][0]).toBe('D:\\Notas\\nota.pdf');
    expect(writeFile.mock.calls[0][2]).toBeUndefined(); // nada de baseDir
    expect(openPath).toHaveBeenCalledWith('D:\\Notas\\nota.pdf');
    expect(r).toEqual({ cancelado: false, caminho: 'D:\\Notas\\nota.pdf' });
  });

  it('cancelar a janela não grava nada', async () => {
    save.mockResolvedValue(null);

    const r = await salvarArquivo('nota.pdf', pdf());

    expect(r).toEqual({ cancelado: true });
    expect(writeFile).not.toHaveBeenCalled();
  });

  it('janela que não abre é erro, e não gravação escondida no AppData', async () => {
    save.mockRejectedValue(new Error('dialog.save not allowed'));

    await expect(salvarArquivo('nota.pdf', pdf())).rejects.toBeInstanceOf(ErroAoSalvar);
    expect(writeFile).not.toHaveBeenCalled();
  });

  it('arquivo aberto em outro programa vira ErroAoSalvar com mensagem para o usuário', async () => {
    save.mockResolvedValue('C:\\Users\\Loja\\Desktop\\nota.pdf');
    writeFile.mockRejectedValue(new Error('os error 32'));

    const erro = await salvarArquivo('nota.pdf', pdf()).catch((e) => e);

    expect(erro).toBeInstanceOf(ErroAoSalvar);
    expect(erro.message).toMatch(/aberto em outro programa/);
  });

  it('CSV dos relatórios também passa pelo "Salvar como"', async () => {
    save.mockResolvedValue('D:\\Relatorios\\comissao.csv');

    const caminho = await saveCsv('comissao.csv', ['Nome'], [['Ana']]);

    expect(save.mock.calls[0][0].filters).toEqual([{ name: 'Planilha CSV', extensions: ['csv'] }]);
    expect(writeFile.mock.calls[0][0]).toBe('D:\\Relatorios\\comissao.csv');
    expect(writeTextFile).not.toHaveBeenCalled();
    expect(caminho).toBe('D:\\Relatorios\\comissao.csv');
  });

  it('CSV cancelado devolve null (o relatório não mostra "salvo em")', async () => {
    save.mockResolvedValue(null);

    expect(await saveCsv('comissao.csv', ['Nome'], [['Ana']])).toBeNull();
    expect(writeFile).not.toHaveBeenCalled();
  });
});
